import itertools
from typing import List, Optional, Tuple
from .PetriNet import PetriNet
from pulp import LpProblem, LpVariable, LpBinary, LpMinimize, lpSum, PULP_CBC_CMD

def deadlock_reachable_marking(
    pn: PetriNet, 
    bdd_node  # Đây là object BDD node trả về từ bdd_reachable
) -> Optional[List[int]]:
    """
    Tìm một trạng thái deadlock sử dụng thư viện `dd`.
    """
    # Lấy BDD Manager từ node
    bdd = bdd_node.bdd
    
    # Danh sách các biến (để điền giá trị cho biến Don't Care)
    all_vars = pn.place_ids
    
    # 1. Trích xuất Marking từ BDD
    # Chúng ta chỉ lấy tối đa một số lượng mẫu để kiểm tra, tránh duyệt hết nếu quá lớn
    MAX_SAMPLES = 10000 
    candidate_markings = []
    
    count = 0
    # pick_iter trả về generator các partial assignments (cube)
    # care_vars: chỉ quan tâm đến các biến hiện tại (x), không quan tâm biến (x')
    care_vars = set(all_vars)
    
    for assignment in bdd.pick_iter(bdd_node, care_vars=care_vars):
        if count >= MAX_SAMPLES: 
            break
            
        # assignment là dict {var_name: True/False}
        # Cần chuyển về list [0, 1, 0...] theo thứ tự place_ids
        
        # Xác định biến thiếu (Don't care)
        fixed_part = {}
        missing_vars = []
        
        for pid in all_vars:
            if pid in assignment:
                fixed_part[pid] = 1 if assignment[pid] else 0
            else:
                missing_vars.append(pid)
        
        # Sinh tất cả tổ hợp cho biến thiếu
        for combo in itertools.product([0, 1], repeat=len(missing_vars)):
            if count >= MAX_SAMPLES: break
            
            full_marking = [0] * len(all_vars)
            
            # Điền biến cố định
            for pid, val in fixed_part.items():
                idx = pn.place_ids.index(pid) # Có thể tối ưu bằng map, nhưng n nhỏ nên ok
                full_marking[idx] = val
                
            # Điền biến thiếu
            for i, val in enumerate(combo):
                pid = missing_vars[i]
                idx = pn.place_ids.index(pid)
                full_marking[idx] = val
                
            candidate_markings.append(tuple(full_marking))
            count += 1

    if not candidate_markings:
        return None

    # 2. Lọc Deadlock (Logic giống cũ)
    deadlock_indices = []
    num_trans = len(pn.trans_ids)
    num_places = len(pn.place_ids)
    
    for i, m in enumerate(candidate_markings):
        is_dead = True
        
        for t_idx in range(num_trans):
            # Check Input (Enable)
            enabled = True
            for p_idx in range(num_places):
                if m[p_idx] < pn.I[t_idx, p_idx]:
                    enabled = False
                    break
            
            if not enabled: continue
            
            # Check Output (1-Safe check)
            # Nếu bắn transition này mà tạo ra > 1 token ở chỗ nào đó thì không được bắn
            # Deadlock là trạng thái KHÔNG THỂ bắn cái nào hợp lệ
            safe_fire = True
            for p_idx in range(num_places):
                new_val = m[p_idx] - pn.I[t_idx, p_idx] + pn.O[t_idx, p_idx]
                if new_val > 1:
                    safe_fire = False
                    break
            
            if safe_fire:
                # Tìm được ít nhất 1 transition bắn được -> Không chết
                is_dead = False
                break
        
        if is_dead:
            deadlock_indices.append(i)

    if not deadlock_indices:
        return None

    # 3. Chọn 1 Deadlock bằng ILP (để đảm bảo tính ngẫu nhiên/tối ưu nếu cần)
    # Hoặc đơn giản trả về cái đầu tiên: return list(candidate_markings[deadlock_indices[0]])
    
    prob = LpProblem("Select_Deadlock", LpMinimize)
    choices = {i: LpVariable(f"c_{i}", cat=LpBinary) for i in deadlock_indices}
    prob += lpSum(choices.values()) == 1
    prob.solve(PULP_CBC_CMD(msg=False))
    
    for i in deadlock_indices:
        if choices[i].varValue and choices[i].varValue > 0.5:
            return list(candidate_markings[i])

    return list(candidate_markings[deadlock_indices[0]])