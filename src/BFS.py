from collections import deque
from typing import Set, Tuple
import numpy as np
from .PetriNet import PetriNet

Marking = Tuple[int, ...]


def is_enabled(pn: PetriNet, t_idx: int, M: Marking) -> bool:
    """
    Transition t_idx enabled tại marking M nếu:
      - M[p] >= I[t][p] với mọi place p (đủ token để bắn)
      - và marking mới M'(p) = M(p) - I[t][p] + O[t][p] không vượt quá 1 (1-safe)
    """
    num_trans, num_places = pn.I.shape

    for p in range(num_places):
        required = int(pn.I[t_idx][p])
        if M[p] < required:
            return False

        produced = int(pn.O[t_idx][p])
        new_tokens = M[p] - required + produced
        if new_tokens > 1:
            # 1-safe: không cho phép có hơn 1 token trên một place
            return False

    return True


def fire(pn: PetriNet, t_idx: int, M: Marking) -> Marking:
    """
    Bắn transition t_idx từ marking M:
        M'(p) = M(p) - I[t][p] + O[t][p]
    (Giả sử đã is_enableded nên không sinh ra marking > 1.)
    """
    num_trans, num_places = pn.I.shape
    M_new = [0] * num_places

    for p in range(num_places):
        required = int(pn.I[t_idx][p])
        produced = int(pn.O[t_idx][p])
        M_new[p] = M[p] - required + produced

    return tuple(M_new)


def bfs_reachable(pn: PetriNet) -> Set[Marking]:
    """
    BFS toàn bộ state space reachable từ M0.
    """
    # M0 là np.array → chuyển sang tuple để bỏ vào set
    start: Marking = tuple(int(x) for x in pn.M0.tolist())
    visited: Set[Marking] = {start}

    queue = deque([start])
    num_trans, num_places = pn.I.shape

    while queue:
        M = queue.popleft()

        for t_idx in range(num_trans):
            if is_enabled(pn, t_idx, M):
                M_new = fire(pn, t_idx, M)
                if M_new not in visited:
                    visited.add(M_new)
                    queue.append(M_new)

    return visited
