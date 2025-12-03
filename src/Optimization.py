import numpy as np
import heapq
from dataclasses import dataclass, field
from typing import List, Optional, Set, Dict
import pulp

@dataclass(order=True)
class Node:
    ub: float
    I0: Set[str] = field(compare=False) # Tập biến ép = 0
    I1: Set[str] = field(compare=False) # Tập biến ép = 1
    
    def __post_init__(self):
        self.sort_index = -self.ub

def solve_lp_relaxation(P: List[str], c: np.ndarray, I0: Set[str], I1: Set[str], cuts: List[tuple]) -> tuple:
    """Giải LP Relaxation bằng PuLP"""
    prob = pulp.LpProblem("Relaxation", pulp.LpMaximize)
    x_vars = {p: pulp.LpVariable(f"x_{p}", 0, 1) for p in P}

    # Objective
    prob += pulp.lpSum([c[i] * x_vars[p] for i, p in enumerate(P)])

    # Constraints
    for p in I0: prob += x_vars[p] == 0
    for p in I1: prob += x_vars[p] == 1

    # Cuts
    for coeffs, rhs in cuts:
        prob += pulp.lpSum([coeffs.get(p, 0) * x_vars[p] for p in P]) <= rhs

    prob.solve(pulp.PULP_CBC_CMD(msg=False))

    if pulp.LpStatus[prob.status] != 'Optimal':
        return float('-inf'), {}

    obj = pulp.value(prob.objective)
    if obj is None: return float('-inf'), {}

    sol = {}
    for p in P:
        val = pulp.value(x_vars[p])
        sol[p] = float(val) if val is not None else 0.0
        
    return float(obj), sol

def max_reachable_marking(
    place_ids: List[str], 
    bdd_node, 
    c: np.ndarray
) -> tuple:
    """
    Branch & Cut Optimization sử dụng thư viện `dd`.
    """
    # Lấy Manager từ node
    bdd = bdd_node.bdd
    
    if bdd_node == bdd.false:
        return None, None

    c_dict = {name: val for name, val in zip(place_ids, c)}
    
    # Hàng đợi ưu tiên
    root = Node(ub=float('inf'), I0=set(), I1=set())
    pq = [root]
    
    best_val = float('-inf')
    best_sol = None
    
    # Map tên biến sang dd var (nếu cần, nhưng dd dùng string id trực tiếp)
    # support của dd trả về set string
    all_vars_support = bdd.support(bdd_node) 

    iter_count = 0
    MAX_ITERS = 1000

    print("[Optimization] Starting Branch & Cut...")

    while pq:
        iter_count += 1
        if iter_count > MAX_ITERS:
            print(f"  > Hit iteration limit ({MAX_ITERS}). Stopping.")
            break
            
        node = heapq.heappop(pq)
        
        # Pruning
        if node.ub <= best_val and best_val != float('-inf'):
            continue

        # 1. Restrict BDD (dùng bdd.let)
        # Tạo dict gán giá trị: {var: True/False}
        assignment = {}
        for p in node.I0: assignment[p] = False
        for p in node.I1: assignment[p] = True
        
        # Lọc bớt assignment chỉ chứa biến có trong support để tránh lỗi (tùy phiên bản dd)
        valid_assignment = {k: v for k, v in assignment.items()} # dd thường chấp nhận tất cả
        
        current_bdd = bdd.let(valid_assignment, bdd_node)

        if current_bdd == bdd.false:
            continue

        # Check nếu tìm được 1 nghiệm duy nhất (Singleton)
        path_count = bdd.count(current_bdd, nvars=len(place_ids))
        if path_count == 1:
            # Lấy nghiệm duy nhất đó
            # pick trả về 1 dict thỏa mãn
            model = bdd.pick(current_bdd, care_vars=set(place_ids))
            
            # Tính giá trị
            current_val = 0
            current_sol = []
            for p in place_ids:
                # Nếu biến trong model là True -> 1, False -> 0
                # Nếu biến không có trong model (Don't care) -> Thường gán 0 cho an toàn hoặc theo I1
                val = 1 if model.get(p, False) else 0
                
                # Override bằng ràng buộc nhánh (cho chắc chắn)
                if p in node.I1: val = 1
                if p in node.I0: val = 0
                
                current_sol.append(val)
                if val == 1: current_val += c_dict[p]
            
            if current_val > best_val:
                best_val = current_val
                best_sol = current_sol
            continue

        # 2. Sinh Cuts từ BDD (Separation)
        # Tìm biến chưa gán
        free_vars = [p for p in place_ids if p not in node.I0 and p not in node.I1]
        
        forced_0 = set()
        forced_1 = set()
        mutex_cuts = [] # list of ({vars: 1}, rhs)
        
        # Inference đơn giản
        for p in free_vars:
            # Check p=1 -> Nếu ra False nghĩa là p phải = 0
            if bdd.let({p: True}, current_bdd) == bdd.false:
                forced_0.add(p)
            # Check p=0 -> Nếu ra False nghĩa là p phải = 1
            elif bdd.let({p: False}, current_bdd) == bdd.false:
                forced_1.add(p)
                
        # Cập nhật ràng buộc mới
        new_I0 = node.I0 | forced_0
        new_I1 = node.I1 | forced_1
        real_free_vars = [p for p in place_ids if p not in new_I0 and p not in new_I1]

        # 3. Solve LP
        ub_lp, sol_lp = solve_lp_relaxation(place_ids, c, new_I0, new_I1, mutex_cuts)
        
        if ub_lp == float('-inf'): continue
        
        current_ub = min(node.ub, ub_lp)
        if current_ub <= best_val: continue

        # 4. Check Integer Solution
        is_integer = True
        temp_I1 = set(new_I1)
        
        for p in real_free_vars:
            val = sol_lp.get(p, 0.0)
            if abs(val - 0) > 1e-5 and abs(val - 1) > 1e-5:
                is_integer = False
                break
            if val > 0.9: temp_I1.add(p)
            
        if is_integer:
            # Kiểm tra lại với BDD xem nghiệm nguyên này có hợp lệ không
            check_env = {p: (True if p in temp_I1 else False) for p in place_ids}
            if bdd.let(check_env, bdd_node) != bdd.false:
                val_int = sum(c_dict[p] for p in temp_I1)
                if val_int > best_val:
                    best_val = val_int
                    best_sol = [1 if p in temp_I1 else 0 for p in place_ids]
                if val_int >= current_ub - 1e-5: continue

        # 5. Branching
        if not real_free_vars: continue
        
        # Chọn biến có giá trị phân số gần 0.5 nhất
        branch_var = max(real_free_vars, key=lambda p: min(abs(sol_lp.get(p, 0) - 0.5), 0.5))
        
        # Nhánh 1
        heapq.heappush(pq, Node(ub=current_ub, I0=new_I0, I1=new_I1 | {branch_var}))
        # Nhánh 0
        heapq.heappush(pq, Node(ub=current_ub, I0=new_I0 | {branch_var}, I1=new_I1))

    final_val = int(best_val) if best_val != float('-inf') else None
    return best_sol, final_val
