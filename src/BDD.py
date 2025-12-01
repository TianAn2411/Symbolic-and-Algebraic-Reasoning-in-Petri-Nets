import collections
from typing import Tuple, List, Optional, Dict, Any
from pyeda.inter import *
from .PetriNet import PetriNet
import sys
import numpy as np

# Tăng giới hạn đệ quy
sys.setrecursionlimit(50000)

def get_topology_sorted_order(pn: PetriNet) -> List[str]:
    """
    Sắp xếp thứ tự Place dựa trên cấu trúc kết nối (Topology) bằng thuật toán BFS.
    """
    num_places = len(pn.place_ids)
    num_trans = pn.I.shape[0] 
    
    # 1. Xây dựng danh sách kề (Adjacency List)
    adj = collections.defaultdict(set)
    
    for t in range(num_trans):
        inputs = np.where(pn.I[t] > 0)[0]
        outputs = np.where(pn.O[t] > 0)[0]
        
        # Gom nhóm các place liên quan
        for p_in in inputs:
            for p_out in outputs:
                if p_in != p_out:
                    adj[p_in].add(p_out)
                    adj[p_out].add(p_in)
                    
        if len(inputs) > 1:
            base = inputs[0]
            for other in inputs[1:]:
                adj[base].add(other)
                adj[other].add(base)

    # 2. BFS Reordering
    visited = [False] * num_places
    new_order_indices = []
    
    for start in range(num_places):
        if not visited[start]:
            queue = [start]
            visited[start] = True
            
            while queue:
                u = queue.pop(0)
                new_order_indices.append(u)
                for v in adj[u]:
                    if not visited[v]:
                        visited[v] = True
                        queue.append(v)
    
    return [pn.place_ids[i] for i in new_order_indices]


def fast_smoothing(bdd_func, vars_set):
    """
    Công thức: exists v. f = (f|v=0) OR (f|v=1)
    """
    res = bdd_func
    for v in vars_set:
        # Nếu hàm BDD không phụ thuộc vào v, bỏ qua để tiết kiệm
        # (Optional optimization)
        if v not in res.support:
            continue
        
        # Cofactors trả về (f_low, f_high) tương ứng v=0 và v=1
        try:
            # Dùng cofactors nhanh hơn restrict 2 lần
            co_0, co_1 = res.cofactors(v)
            res = co_0 | co_1
        except:
            # Fallback nếu api khác biệt
            res = res.restrict({v: 0}) | res.restrict({v: 1})
            
    return res


def build_BDD(pn: PetriNet) -> tuple:
    bdd_place_ids = get_topology_sorted_order(pn)
    id_to_old_idx = {pid: i for i, pid in enumerate(pn.place_ids)}

    X = {}
    Xp = {}
    for p_id in bdd_place_ids:
        X[p_id] = exprvar(p_id)
        Xp[p_id] = exprvar(p_id + "_p")

    transition_bdd_list = []
    num_trans = pn.I.shape[0]
    all_places_set = set(bdd_place_ids)

    for t_idx in range(num_trans):
        input_indices = np.where(pn.I[t_idx] > 0)[0]
        output_indices = np.where(pn.O[t_idx] > 0)[0]
        
        if len(input_indices) == 0 and len(output_indices) == 0:
            continue

        input_ids = [pn.place_ids[i] for i in input_indices]
        output_ids = [pn.place_ids[i] for i in output_indices]
        
        # Enable: Pre -> 1, Post -> 0 (1-safe)
        enable_exprs = [X[pid] for pid in input_ids]
        input_set = set(input_ids)
        for pid in output_ids:
            if pid not in input_set:
                enable_exprs.append(~X[pid])
        
        enable_term = And(*enable_exprs) if enable_exprs else expr(True)

        # Update
        change_exprs = []
        output_set = set(output_ids)
        for pid in input_ids:
            if pid not in output_set:
                change_exprs.append(~Xp[pid])  # Consumed
            else:
                change_exprs.append(Xp[pid])   # Read/Loop
                
        for pid in output_ids:
            if pid not in input_set:
                change_exprs.append(Xp[pid])   # Produced
        
        change_term = And(*change_exprs)

        # Frame Condition
        affected_set = input_set | output_set
        unaffected_set = all_places_set - affected_set
        
        same_exprs = [Xnor(Xp[pid], X[pid]) for pid in unaffected_set]
        same_term = And(*same_exprs) if same_exprs else expr(True)

        full_trans_expr = And(enable_term, change_term, same_term)
        transition_bdd_list.append(expr2bdd(full_trans_expr))

    # Initial Marking
    init_list = []
    for p_id in bdd_place_ids:
        old_idx = id_to_old_idx[p_id]
        if pn.M0[old_idx] >= 1:
            init_list.append(X[p_id])
        else:
            init_list.append(~X[p_id])

    init_expr = And(*init_list)
    init_bdd = expr2bdd(init_expr)

    return transition_bdd_list, init_bdd, X, Xp, bdd_place_ids


def compute_BDD_reachability(
    initial_bdd: BinaryDecisionDiagram,
    transition_bdd_list: List[BinaryDecisionDiagram],
    place_ids: List[str]
) -> Tuple[BinaryDecisionDiagram, int]:
    
    R = initial_bdd
    frontier = initial_bdd 
    
    # Biến cần khử (X)
    X_vars_list = [bddvar(p) for p in place_ids] 
    var_map_bdd = {bddvar(p + "_p"): bddvar(p) for p in place_ids}
    
    while True:
        accumulated_new_states = None 
        
        for t_bdd in transition_bdd_list:
            rel = frontier & t_bdd
            
            if not rel.is_zero(): 
                # Chỉ khử các biến X xuất hiện trong rel để giảm chi phí
                support_vars = [v for v in X_vars_list if v in rel.support]
                post = fast_smoothing(rel, support_vars)
                post_renamed = post.compose(var_map_bdd)
                
                if accumulated_new_states is None:
                    accumulated_new_states = post_renamed
                else:
                    accumulated_new_states = accumulated_new_states | post_renamed
        
        if accumulated_new_states is None:
            break
            
        new_states = accumulated_new_states & ~R
        
        if new_states.is_zero():
            break
        
        R = R | new_states
        frontier = new_states

    try:
        num_states = int(R.satisfy_count())
    except:
        num_states = -1 

    return R, num_states


def bdd_reachable(pn: PetriNet) -> Tuple[BinaryDecisionDiagram, int]:
    transition_bdd_list, initial_bdd, _, _, sorted_ids = build_BDD(pn)
    
    reachable_bdd, num_states = compute_BDD_reachability(
        initial_bdd,
        transition_bdd_list,
        sorted_ids 
    )
    
    return reachable_bdd, num_states
