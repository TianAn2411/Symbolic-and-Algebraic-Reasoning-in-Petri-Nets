import numpy as np
from pyeda.inter import *
import heapq
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Set, Dict
import pulp

@dataclass(order=True)
class Node:
    ub: float
    I0: Set[str] = field(compare=False) # Tập biến bị ép = 0
    I1: Set[str] = field(compare=False) # Tập biến bị ép = 1
    
    def __post_init__(self):
        # Priority Queue là Min-Heap, ta muốn lấy UB lớn nhất -> lưu âm
        self.sort_index = -self.ub

def check_bdd_satisfy(bdd, env: Dict[str, int]) -> bool:
    """
    Hàm thay thế cho evaluate().
    Sử dụng restrict để kiểm tra tính thỏa mãn của BDD với môi trường env.
    """
    if bdd.is_one(): return True
    if bdd.is_zero(): return False

    support_vars = list(bdd.support)
    name_to_var = {str(v): v for v in support_vars}
    
    restrict_map = {}
    for name, val in env.items():
        if name in name_to_var:
            restrict_map[name_to_var[name]] = val
            
    res = bdd.restrict(restrict_map)
    return res.is_one()

def solve_lp_relaxation(P: List[str], c: np.ndarray, I0: Set[str], I1: Set[str], cuts: List[tuple]) -> Tuple[float, Dict[str, float]]:
    """Giải bài toán LP Relaxation"""

    prob = pulp.LpProblem("Relaxation", pulp.LpMaximize)
    
    # [FIX] Tạo biến LP an toàn
    x_vars = {}
    for p in P:
        x_vars[p] = pulp.LpVariable(f"x_{p}", 0, 1)

    # Hàm mục tiêu
    prob += pulp.lpSum([c[i] * x_vars[p] for i, p in enumerate(P)])

    # Ràng buộc cố định
    for p in I0: prob += x_vars[p] == 0
    for p in I1: prob += x_vars[p] == 1

    # Thêm Cuts
    for coeffs, rhs in cuts:
        prob += pulp.lpSum([coeffs.get(p, 0) * x_vars[p] for p in P]) <= rhs

    # [FIX] Tắt log solver để output gọn gàng
    prob.solve(pulp.PULP_CBC_CMD(msg=False))

    
    if pulp.LpStatus[prob.status] != 'Optimal':
        # Trả về dict rỗng nếu không optimal
        return float('-inf'), {}
    
    obj_val = pulp.value(prob.objective)
    
    #Nếu solver trả về None cho objective, coi như thất bại
    if obj_val is None:
        return float('-inf'), {}
    # Lấy giá trị an toàn, ép kiểu float
    sol = {}
    for p in P:
        val = pulp.value(x_vars[p])
        sol[p] = float(obj_val) if val is not None else 0.0

    return pulp.value(prob.objective), sol

def get_bdd_inferences(bdd_node, P: List[str], current_vars: Set[str]) -> Tuple[List[tuple], Set[str], Set[str]]:
    """Separation: Sinh Cuts từ BDD"""
    mutex_cuts = []
    forced_0 = set()
    forced_1 = set()
    
    if bdd_node.is_zero():
        return [], set(), set()

    support_vars = list(bdd_node.support)
    name_to_var = {str(v): v for v in support_vars}

    def safe_restrict(node, mapping):
        valid_map = {name_to_var[k]: v for k, v in mapping.items() if k in name_to_var}
        if not valid_map: return node
        return node.restrict(valid_map)

    for p in current_vars:
        # Check p=1
        r1 = safe_restrict(bdd_node, {p: 1})
        if r1.is_zero(): forced_0.add(p)
            
        # Check p=0
        r0 = safe_restrict(bdd_node, {p: 0})
        if r0.is_zero(): forced_1.add(p)

    candidates = list(current_vars - forced_0 - forced_1)
    limit_checks = 0
    for i in range(len(candidates)):
        for j in range(i + 1, len(candidates)):
            if limit_checks > 50: break # Giảm limit xuống 50 cho nhanh
            u, v = candidates[i], candidates[j]
            
            r_uv = safe_restrict(bdd_node, {u: 1, v: 1})
            if r_uv.is_zero():
                mutex_cuts.append(({u: 1, v: 1}, 1))
            limit_checks += 1

    return mutex_cuts, forced_0, forced_1

def max_reachable_marking(P: List[str], bdd, c: np.ndarray) -> Tuple[Optional[List[int]], Optional[float]]:
    """Main Branch & Cut Algorithm"""
    
    if bdd.is_zero():
        return None, None

    root_node = Node(ub=float('inf'), I0=set(), I1=set())
    pq = [root_node]
    
    best_val = float('-inf')
    best_sol = None
    
    # Map tên biến -> hệ số c
    c_dict = {name: val for name, val in zip(P, c)}

    all_vars = list(bdd.support)
    global_name_to_var = {str(v): v for v in all_vars}

    while pq:
        node = heapq.heappop(pq)
        
        # Pruning
        if node.ub <= best_val and best_val != float('-inf'):
            continue

        # 1. Restrict BDD
        current_map = {}
        for p in node.I0:
            if p in global_name_to_var: current_map[global_name_to_var[p]] = 0
        for p in node.I1:
            if p in global_name_to_var: current_map[global_name_to_var[p]] = 1
            
        current_bdd = bdd.restrict(current_map)

        if current_bdd.is_zero():
            continue

        free_vars = [p for p in P if p not in node.I0 and p not in node.I1]

        # 2. Leaf Node Check
        if not free_vars:
            current_val = sum(c_dict[p] for p in node.I1)
            if current_val > best_val:
                best_val = current_val
                best_sol = [1 if p in node.I1 else 0 for p in P]
            continue

        # 3. Separation
        cuts, forced_0, forced_1 = get_bdd_inferences(current_bdd, P, set(free_vars))
        
        new_I0 = node.I0 | forced_0
        new_I1 = node.I1 | forced_1
        free_vars = [p for p in P if p not in new_I0 and p not in new_I1]

        # 4. Solve LP
        ub_lp, sol_lp = solve_lp_relaxation(P, c, new_I0, new_I1, cuts)
        
        # [FIX] Kiểm tra nếu LP thất bại -> cắt nhánh này
        if ub_lp == float('-inf') or not sol_lp:
            continue

        current_ub = min(node.ub, ub_lp)

        if current_ub <= best_val:
            continue

        # Heuristic: Check nghiệm nguyên
        is_integer = True
        temp_I1 = set(new_I1)
        
        for p in free_vars:
            # [FIX] sol_lp.get trả về 0.0 nếu không có key, an toàn.
            val = sol_lp.get(p, 0.0)
            
            # [FIX] Kiểm tra None (phòng hờ)
            if val is None: val = 0.0
            
            if abs(val - 0) > 1e-5 and abs(val - 1) > 1e-5:
                is_integer = False
                break
            if val > 0.9: temp_I1.add(p)
        
        if is_integer:
            check_env = {p: (1 if p in temp_I1 else 0) for p in P}
            if check_bdd_satisfy(bdd, check_env):
                val_int = sum(c_dict[p] for p in temp_I1)
                if val_int > best_val:
                    best_val = val_int
                    best_sol = [check_env[p] for p in P]
                # Nếu tìm thấy nghiệm nguyên tối ưu bằng cận trên, ta có thể dừng nhánh này luôn
                if val_int >= current_ub - 1e-5:
                    continue

        # 5. Branching
        if not free_vars: continue
        
        # Chiến lược chọn biến phân nhánh: Chọn biến có giá trị phân số gần 0.5 nhất (Most fractional)
        # Hoặc chọn biến có hệ số c lớn nhất
        # Ở đây dùng hệ số c lớn nhất cho đơn giản
        branch_var = max(free_vars, key=lambda p: abs(c_dict[p]))
        
        child_1 = Node(ub=current_ub, I0=new_I0, I1=new_I1 | {branch_var})
        heapq.heappush(pq, child_1)
        
        child_0 = Node(ub=current_ub, I0=new_I0 | {branch_var}, I1=new_I1)
        heapq.heappush(pq, child_0)

    final_val = int(best_val) if best_val != float('-inf') and best_val is not None else None
    
    return best_sol, final_val