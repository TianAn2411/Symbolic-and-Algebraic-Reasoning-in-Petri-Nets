from dd import autoref as _bdd
from .PetriNet import PetriNet
from typing import Tuple, List, Dict
import time
import sys

# Tăng giới hạn đệ quy để an toàn
sys.setrecursionlimit(50000)

def build_BDD_dd(pn: PetriNet, bdd_manager) -> tuple:
    """
    Xây dựng BDD sử dụng thư viện `dd`.
    """
    
    # 1. Khai báo biến
    place_ids = pn.place_ids
    
    # Khai báo biến hiện tại (x) và biến kế tiếp (x')
    vars_x = place_ids
    vars_xp = [p + "_p" for p in place_ids]
    
    # Đăng ký biến với BDD Manager
    # Interleaved ordering: x1, x1', x2, x2'... để tối ưu
    ordered_vars = []
    for p in place_ids:
        ordered_vars.append(p)
        ordered_vars.append(p + "_p")
    
    bdd_manager.declare(*ordered_vars)
    
    # 2. Xây dựng Transition Relations
    
    trans_rels = []
    
    # Cache các biến BDD để dùng lại
    x_nodes = {p: bdd_manager.var(p) for p in place_ids}
    xp_nodes = {p: bdd_manager.var(p + "_p") for p in place_ids}
    
    num_trans = pn.I.shape[0]
    all_places_set = set(place_ids)

    for t_idx in range(num_trans):
        # Lấy input/output places
        input_indices = [i for i, val in enumerate(pn.I[t_idx]) if val > 0]
        output_indices = [i for i, val in enumerate(pn.O[t_idx]) if val > 0]
        
        if not input_indices and not output_indices:
            continue
            
        input_ids = [pn.place_ids[i] for i in input_indices]
        output_ids = [pn.place_ids[i] for i in output_indices]
        
        # --- Logic Enabling ---
        # Pre-conditions: Place input phải = 1
        enable_cond = bdd_manager.true
        for pid in input_ids:
            enable_cond &= x_nodes[pid]
            
        # 1-Safe check: Place output (nếu ko phải input) phải = 0
        input_set = set(input_ids)
        for pid in output_ids:
            if pid not in input_set:
                enable_cond &= ~x_nodes[pid]
        
        # --- Logic Update (Next State) ---
        change_cond = bdd_manager.true
        output_set = set(output_ids)
        
        # Input mất token -> Next = 0
        for pid in input_ids:
            if pid not in output_set:
                change_cond &= ~xp_nodes[pid]
            else:
                change_cond &= xp_nodes[pid] # Self-loop
        
        # Output thêm token -> Next = 1
        for pid in output_ids:
            if pid not in input_set:
                change_cond &= xp_nodes[pid]
                
        # --- Frame Condition (Unchanged Places) ---
        # Những chỗ không liên quan: x' == x
        affected = input_set | output_set
        unaffected = all_places_set - affected
        
        frame_cond = bdd_manager.true
        for pid in unaffected:
            # x' == x  <=>  (x & x') | (!x & !x')
            u = x_nodes[pid]
            v = xp_nodes[pid]
            frame_cond &= (u & v) | (~u & ~v)
            
        # Tổng hợp transition
        full_trans = enable_cond & change_cond & frame_cond
        trans_rels.append(full_trans)

    # 3. Initial Marking
    init_expr = bdd_manager.true
    for i, pid in enumerate(place_ids):
        if pn.M0[i] > 0:
            init_expr &= x_nodes[pid]
        else:
            init_expr &= ~x_nodes[pid]
            
    return trans_rels, init_expr, x_nodes, xp_nodes

def bdd_reachable(pn: PetriNet) -> Tuple[object, int]:
    """
    Hàm chính tính toán Reachability bằng thư viện dd.
    [FIXED] Sử dụng bdd.quantify thay vì relational_product.
    """
    # Khởi tạo BDD Manager
    bdd = _bdd.BDD()
    
    # Xây dựng quan hệ
    trans_rels, R, x_nodes, xp_nodes = build_BDD_dd(pn, bdd)
    
    frontier = R
    
    # Map đổi tên: x' -> x
    rename_map = {p + "_p": p for p in pn.place_ids}
    
    # Tập biến cần khử: Biến hiện tại x
    q_vars = set(pn.place_ids)
    
    step = 0
    start_time = time.time()
    
    while True:
        step += 1
        
        # In log định kỳ
        if step % 1 == 0:
            print(f"    -> Step {step}...", end="\r")

        accumulated_next = bdd.false
        
        # Partitioned Transition Relation
        for rel in trans_rels:
            
            # 1. Conjunction (Giao): Trạng thái biên & Quan hệ chuyển đổi
            conjunction = frontier & rel
            
            if conjunction == bdd.false:
                continue
                
            # 2. Quantify (Tồn tại): Khử biến hiện tại x, chỉ giữ lại x'
            # forall=False nghĩa là Existential Quantification
            img = bdd.quantify(conjunction, q_vars, forall=False)
            
            # 3. Rename: x' -> x (Để chuẩn bị cho vòng lặp sau)
            img_renamed = bdd.let(rename_map, img)
            
            accumulated_next |= img_renamed
            
        if accumulated_next == bdd.false:
            break
            
        # Chỉ giữ lại trạng thái mới: New = Next & ~Reached
        new_states = accumulated_next & ~R
        
        if new_states == bdd.false:
            break
            
        R |= new_states
        frontier = new_states

    end_time = time.time()
    
    # Đếm số trạng thái
    # nvars là số lượng biến trong tập kết quả (chỉ tính biến x, không tính x')
    count = int(bdd.count(R, nvars=len(pn.place_ids)))
    
    print(f" Finished in {end_time - start_time:.4f}")
    
    return R, count