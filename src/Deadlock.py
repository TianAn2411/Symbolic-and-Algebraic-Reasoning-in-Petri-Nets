import collections
from typing import Tuple, List, Optional
from pyeda.inter import *
from collections import deque
from .PetriNet import PetriNet
import numpy as np
import itertools
from pulp import LpProblem, LpVariable, LpBinary, LpMinimize, lpSum, PULP_CBC_CMD

def deadlock_reachable_marking(
    pn: PetriNet, 
    bdd: BinaryDecisionDiagram, 
) -> Optional[List[int]]:
    """
    Tìm một trạng thái deadlock trong tập reachable markings được biểu diễn bởi BDD.
    Sử dụng kết hợp giải mã BDD và ILP để chọn deadlock.
    """
    MAX_MARKINGS = 10000
    
    # --- 0. TÁI TẠO MAP VAR (Vì hàm này chỉ nhận BDD raw) ---
    # Cập nhật: pn.place_ids thay vì pn.places
    X_bdd = {p: bddvar(p) for p in pn.place_ids}
    idx_to_var = {i: X_bdd[pn.place_ids[i]] for i in range(len(pn.place_ids))}

    # --- 1. TRÍCH XUẤT MARKING TỪ BDD ---
    cacmarkingdatduoc = []
    somarkingdaxuly = 0
    
    try:
        # satisfy_all trả về các "cube" (gán giá trị từng phần)
        for ketqua in bdd.satisfy_all():
            if somarkingdaxuly >= MAX_MARKINGS: break
            
            # Phân loại: Biến nào đã biết (Fixed), biến nào thiếu (Missing/Don't Care)
            fixed_vals = {}
            missing_indices = []
            
            for pidx in range(len(pn.place_ids)):
                bdd_v = idx_to_var[pidx]
                val = ketqua.get(bdd_v) # Trả về 0, 1 hoặc None
                
                if val is not None:
                    fixed_vals[pidx] = val
                else:
                    # Biến không có trong BDD -> Don't Care -> Phải vét cạn
                    missing_indices.append(pidx)
            
            # Sinh ra tất cả các marking có thể từ các biến thiếu (0 và 1)
            for combo in itertools.product([0, 1], repeat=len(missing_indices)):
                if somarkingdaxuly >= MAX_MARKINGS: break
                
                current_m = [0] * len(pn.place_ids)
                
                # Điền giá trị cố định
                for idx, v in fixed_vals.items():
                    current_m[idx] = v
                
                # Điền giá trị hoán vị (cho biến missing)
                for i, val in enumerate(combo):
                    idx = missing_indices[i]
                    current_m[idx] = val
                
                cacmarkingdatduoc.append(tuple(current_m))
                somarkingdaxuly += 1
                
    except Exception as e:
        print(f"Error extracting BDD: {e}")
        return None
    
    if not cacmarkingdatduoc:
        return None

    # --- 2. LỌC DEADLOCK BẰNG PYTHON (CHUẨN 1-SAFE) ---
    deadlock_indices = []
    
    for i, m in enumerate(cacmarkingdatduoc):
        is_dead = True
        # Cập nhật: pn.trans_ids
        for tidx in range(len(pn.trans_ids)):
            # a. Check Input (Có đủ token để bắn không?)
            enough_input = True
            for p in range(len(pn.place_ids)):
                # Cập nhật: dùng ma trận I
                if m[p] < pn.I[tidx, p]:
                    enough_input = False
                    break
            if not enough_input: continue 
                
            # b. Check Output (1-Safe Rule: Bắn xong có bị tràn không?)
            safe_fire = True
            for p in range(len(pn.place_ids)):
                # Công thức: M' = M - I + O
                # Cập nhật: dùng ma trận I và O
                new_val = m[p] - pn.I[tidx, p] + pn.O[tidx, p]
                if new_val > 1:
                    safe_fire = False # Bắn xong tràn token -> Cấm bắn
                    break
            
            if safe_fire:
                is_dead = False # Tìm được 1 cái bắn ngon -> Không phải Deadlock
                break
        
        if is_dead:
            deadlock_indices.append(i)

    if not deadlock_indices:
        return None

    # --- 3. DÙNG ILP ĐỂ CHỌN KẾT QUẢ ---
    mohinh = LpProblem("Select_Deadlock", LpMinimize)
    bienchon = {}
    
    # Chỉ tạo biến cho các index deadlock để tiết kiệm bộ nhớ
    for i in deadlock_indices:
        bienchon[i] = LpVariable(f"choose_{i}", cat=LpBinary)
    
    # Ràng buộc: Chọn đúng 1 cái nằm trong danh sách Deadlock
    mohinh += lpSum(bienchon[i] for i in deadlock_indices) == 1
    
    status = mohinh.solve(PULP_CBC_CMD(msg=0))
    
    if status != 1: return None
        
    for i in deadlock_indices:
        if bienchon[i].varValue is not None and bienchon[i].varValue > 0.5:
            return list(cacmarkingdatduoc[i])

    return None