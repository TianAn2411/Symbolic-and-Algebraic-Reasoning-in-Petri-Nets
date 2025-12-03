from typing import Set, Tuple
import numpy as np
from .PetriNet import PetriNet

def dfs_reachable(pn: PetriNet) -> Set[Tuple[int, ...]]:
    """
    DFS tối ưu hóa bằng Bitmasking cho mạng 1-Safe.
    """
    num_places = len(pn.place_ids)
    num_trans = len(pn.trans_ids)

    # --- 1. PRE-PROCESSING ---
    input_masks = [0] * num_trans
    output_masks = [0] * num_trans
    
    for t in range(num_trans):
        in_m = 0
        out_m = 0
        for p in range(num_places):
            if pn.I[t, p] > 0: in_m |= (1 << p)
            if pn.O[t, p] > 0: out_m |= (1 << p)
        input_masks[t] = in_m
        output_masks[t] = out_m

    # --- 2. INITIAL STATE ---
    start_state_int = 0
    for i, val in enumerate(pn.M0):
        if val > 0: start_state_int |= (1 << i)

    # --- 3. DFS LOOP ---
    visited_ints = {start_state_int}
    stack = [start_state_int]
    
    while stack:
        curr = stack.pop()
        
        for t in range(num_trans):
            in_mask = input_masks[t]
            
            # Check Enabled
            if (curr & in_mask) == in_mask:
                # Fire
                next_state = (curr ^ in_mask) | output_masks[t]
                
                if next_state not in visited_ints:
                    visited_ints.add(next_state)
                    stack.append(next_state)

    # --- 4. CONVERT BACK ---
    result_set = set()
    for state_int in visited_ints:
        marking = tuple(1 if (state_int & (1 << i)) else 0 for i in range(num_places))
        result_set.add(marking)
        
    return result_set