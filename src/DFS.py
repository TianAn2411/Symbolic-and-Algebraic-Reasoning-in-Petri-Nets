from collections import deque
import numpy as np
from .PetriNet import PetriNet
from typing import Set, Tuple
from .BFS import is_enabled, fire
Marking = Tuple[int, ...]

def dfs_reachable(pn: PetriNet) -> Set[Marking]:
    """
    DFS (stack) để duyệt toàn bộ state space reachable từ M0.
    """
    # M0 là np.ndarray → convert sang tuple int
    start: Marking = tuple(int(x) for x in pn.M0.tolist())

    visited: Set[Marking] = {start}
    stack = [start]

    num_trans, num_places = pn.I.shape

    while stack:
        M = stack.pop()

        for t_idx in range(num_trans):
            if is_enabled(pn, t_idx, M):
                M_new = fire(pn, t_idx, M)
                if M_new not in visited:
                    visited.add(M_new)
                    stack.append(M_new)

    return visited