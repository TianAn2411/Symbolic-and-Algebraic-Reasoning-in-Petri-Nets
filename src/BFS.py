from collections import deque
from typing import Set, Tuple
import numpy as np
from .PetriNet import PetriNet

def bfs_reachable(pn: PetriNet) -> Set[Tuple[int, ...]]:
    """
    BFS tối ưu hóa bằng Bitmasking cho mạng 1-Safe.
    Nhanh hơn gấp nhiều lần so với dùng Vector/Tuple.
    """
    num_places = len(pn.place_ids)
    num_trans = len(pn.trans_ids)

    # --- Chuyển Ma trận I/O sang Bitmask ---
    # Input Mask: Bit 1 tại vị trí cần token
    input_masks = [0] * num_trans
    # Output Mask: Bit 1 tại vị trí sinh ra token
    output_masks = [0] * num_trans
    # Clear Mask: Những vị trí bị mất token (dùng để xóa bit cũ)
    # Với 1-safe, ta cần xóa input trước khi thêm output
    
    for t in range(num_trans):
        in_m = 0
        out_m = 0
        for p in range(num_places):
            if pn.I[t, p] > 0:
                in_m |= (1 << p)
            if pn.O[t, p] > 0:
                out_m |= (1 << p)
        input_masks[t] = in_m
        output_masks[t] = out_m

    # --- 2. INITIAL STATE ---
    # Chuyển M0 (vector) sang số nguyên (int)
    start_state_int = 0
    for i, val in enumerate(pn.M0):
        if val > 0:
            start_state_int |= (1 << i)

    # --- 3. BFS LOOP (Bitwise Operations) ---
    visited_ints = {start_state_int}
    queue = deque([start_state_int])
    
    while queue:
        curr = queue.popleft()
        
        for t in range(num_trans):
            in_mask = input_masks[t]
            
            # Kiểm tra Enabled: (Current & Input) == Input
            # Nghĩa là tất cả bit 1 của Input đều có mặt trong Current
            if (curr & in_mask) == in_mask:
                
                # Fire: (Current - Input) + Output
                # 1. Xóa token input: curr ^ in_mask (hoặc curr & ~in_mask)
                # 2. Thêm token output: | out_mask
                next_state = (curr ^ in_mask) | output_masks[t]
                
                # Kiểm tra 1-Safe: Nếu sau khi thêm output mà số token ko khớp logic 
                # (tức là place đó đã có token rồi mà lại thêm nữa -> không phải 1-safe đơn giản)
                # Nhưng với bài toán này ta giả định 1-safe chuẩn -> next_state là hợp lệ.
                
                if next_state not in visited_ints:
                    visited_ints.add(next_state)
                    queue.append(next_state)

    # --- 4. CONVERT BACK TO TUPLES---
    # Nếu chỉ cần đếm số lượng, có thể return len(visited_ints)
    # Nhưng để tương thích các hàm khác, ta convert lại thành tuple
    
    result_set = set()
    for state_int in visited_ints:
        # Giải mã bitmask thành tuple
        marking = tuple(1 if (state_int & (1 << i)) else 0 for i in range(num_places))
        result_set.add(marking)
        
    return result_set