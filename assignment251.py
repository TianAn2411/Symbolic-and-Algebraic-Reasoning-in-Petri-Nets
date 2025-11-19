# ============================================================
#  Skeleton code:
#  Author: AndyTruong(2310190) and GPT
#  Version: 1.0
#  Last update: 17/11/2025
# ============================================================
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Tuple, Set, Optional, Any
import argparse
import xml.etree.ElementTree as ET
from collections import deque

@dataclass
class PetriNet:
    """
    Mô hình 1-safe Petri net nội bộ:
      N = (P, T, F, M0)
    - places      : danh sách id place
    - transitions : danh sách id transition
    - pre[t][p]   : số token cần ở place p để t bắn được
    - post[t][p]  : số token tạo ở place p sau khi t bắn
    - M0[p]       : marking ban đầu (0/1 vì 1-safe)
    """

    places: List[str]
    transitions: List[str]
    pre: List[List[int]]
    post: List[List[int]]
    M0: List[int]

    # map id -> index (code cho gọn)
    place_index: Dict[str, int]
    trans_index: Dict[str, int]

    # tên “đẹp” để in trong report (optional)
    place_name: Dict[str, str]
    trans_name: Dict[str, str]


# ============================================================
#  Task 1 – PNML parsing (5%)
#  “Reading Petri nets from PNML files” :contentReference[oaicite:1]{index=1}
# ============================================================

def parsePNML(path: str) -> PetriNet:
    """
    Đọc file PNML 1-safe Petri net và tạo PetriNet nội bộ.

    YÊU CẦU (theo đề):
    - Đọc được:
        + places, transitions
        + arcs (flow relation)
        + initial marking
    - Kiểm tra consistency:
        + arc có source/target tồn tại
        + (tùy bạn) transition có ít nhất 1 input hoặc output, ...
    """
    tree = ET.parse(path)
    root = tree.getroot()

    # Xử lý Namespace: Lấy cái chuỗi trong ngoặc nhọn 
    ns_url = root.tag.split("}")[0].strip("{") if "}" in root.tag else ""
    ns = {"pnml": ns_url} if ns_url else {}
    
    places: List[str] = []
    transitions: List[str] = []
    place_index: Dict[str, int] = {}
    trans_index: Dict[str, int] = {}
    place_name: Dict[str, str] = {}
    trans_name: Dict[str, str] = {}
    
    # List tạm để lưu token ban đầu (sẽ convert sang M0 sau)
    initial_tokens: Dict[str, int] = {} 

    # Helper function để tìm tag bất chấp namespace
    def find_all_tags(parent, tag_name):
        if ns:
            return parent.findall(f".//pnml:{tag_name}", ns)
        else:
            return parent.findall(f".//{tag_name}")

    # 1. Đọc places
    for p in find_all_tags(root, "place"):
        pid = p.get("id")
        places.append(pid)
        idx = len(places) - 1
        place_index[pid] = idx
        
        # Lấy tên (Name)
        name_tag = p.find("name" if not ns else "pnml:name", ns)
        if name_tag is not None:
            text_tag = name_tag.find("text" if not ns else "pnml:text", ns)
            if text_tag is not None and text_tag.text:
                place_name[pid] = text_tag.text.strip()
        
        # Lấy Initial Marking
        marking = 0
        for tag_candidate in ["initialMarking", "hlinitialMarking"]:
            m_tag = p.find(tag_candidate if not ns else f"pnml:{tag_candidate}", ns)
            if m_tag is not None:
                text_tag = m_tag.find("text" if not ns else "pnml:text", ns)
                if text_tag is not None and text_tag.text:
                    try:
                        marking = int(text_tag.text.strip())
                    except ValueError:
                        marking = 0 # Fallback
        initial_tokens[pid] = marking

    # Xây dựng M0 list đúng thứ tự index
    M0: List[int] = [0] * len(places)
    for pid, tokens in initial_tokens.items():
        idx = place_index[pid]
        M0[idx] = 1 if tokens > 0 else 0

    # 2. Đọc transitions
    for t in find_all_tags(root, "transition"):
        tid = t.get("id")
        transitions.append(tid)
        idx = len(transitions) - 1
        trans_index[tid] = idx
        
        # Lấy tên
        name_tag = t.find("name" if not ns else "pnml:name", ns)
        if name_tag is not None:
            text_tag = name_tag.find("text" if not ns else "pnml:text", ns)
            if text_tag is not None and text_tag.text:
                trans_name[tid] = text_tag.text.strip()

    # Khởi tạo ma trận Pre/Post
    num_places = len(places)
    num_trans = len(transitions)
    pre = [[0 for _ in range(num_places)] for _ in range(num_trans)]
    post = [[0 for _ in range(num_places)] for _ in range(num_trans)]

    # 3. Đọc arcs
    for a in find_all_tags(root, "arc"):
        src = a.get("source")
        tgt = a.get("target")
        
        # Lấy weight 
        weight = 1
        inscription = a.find("inscription" if not ns else "pnml:inscription", ns)
        if inscription is not None:
            text_tag = inscription.find("text" if not ns else "pnml:text", ns)
            if text_tag is not None and text_tag.text:
                 try:
                    weight = int(text_tag.text.strip())
                 except ValueError:
                    weight = 1
        
        # Logic nối dây
        if src in place_index and tgt in trans_index:
            # Place -> Transition (Pre)
            p_idx = place_index[src]
            t_idx = trans_index[tgt]
            pre[t_idx][p_idx] += weight
            
        elif src in trans_index and tgt in place_index:
            # Transition -> Place (Post)
            t_idx = trans_index[src]
            p_idx = place_index[tgt]
            post[t_idx][p_idx] += weight
            
        else:
            pass

    # 4) Verify Consistency
    assert len(M0) == num_places, "M0 length mismatch"
    
    return PetriNet(
        places=places,
        transitions=transitions,
        pre=pre,
        post=post,
        M0=M0,
        place_index=place_index,
        trans_index=trans_index,
        place_name=place_name,
        trans_name=trans_name,
    )


# ============================================================
#  Task 2 – Explicit reachability (5%)
#  “Explicit computation of reachable markings” :contentReference[oaicite:2]{index=2}
# ============================================================

Marking = Tuple[int, ...]


def isEnabled(pn: PetriNet, t_idx: int, M: Marking) -> bool:
    """
    Kiểm tra transition t_idx có enabled tại marking M hay không.

    Điều kiện:  với mọi place p:
        M[p] >= pre[t][p]
    (Trong 1-safe net thì pre[t][p] ∈ {0,1}, M[p] ∈ {0,1}.)
    """
    # TODO: hiện thực đúng điều kiện enabled.
    for p_index in range(len(pn.places)):
        if M[p_index] < pn.pre[t_idx][p_index]:
            return False
        
    return True

def fire(pn: PetriNet, t_idx: int, M: Marking) -> Marking:
    """
    Bắn transition t_idx từ marking M, trả về marking M'.

    Công thức:
        M'(p) = M(p) - pre[t][p] + post[t][p]
    """
    # TODO: tạo list mới, áp dụng công thức trên tất cả p.
    M_new = list(M)
    for p_index in range(len(pn.places)):
        M_new[p_index] = M[p_index] - pn.pre[t_idx][p_index] + pn.post[t_idx][p_index]

    return tuple(M_new)


def explicitReachability(pn: PetriNet) -> Set[Marking]:
    """
    Dùng BFS để duyệt toàn bộ state space reachable.

    - Input:
        pn      : PetriNet
    - Output:
        tập tất cả marking reachable từ M0
    """
    start: Marking = tuple(pn.M0)
    visited: Set[Marking] = set()
    visited.add(start)

    container = deque([start])
    pop = container.popleft
    push = container.append
    # TODO:
    #  while container không rỗng:
    #      lấy 1 marking M
    #      duyệt qua mọi transition t
    #          nếu is_enabled(t, M):
    #              M_new = fire(t, M)
    #              nếu M_new chưa thuộc visited:
    #                  thêm vào visited và container
    #
    #  Cuối cùng trả visited.
    while container:
        M = pop()
        for t_index in range(len(pn.transitions)):
            if isEnabled(pn, t_index, M):
                M_new = fire(pn, t_index, M)
                if (M_new not in visited):
                    visited.add(M_new)
                    push(M_new)
    
    return visited


# ============================================================
#  Task 3 – BDD-based reachability (40%)
#  “Symbolic computation of reachable markings by using BDD” :contentReference[oaicite:3]{index=3}
# ============================================================

# Gợi ý: bạn có thể dùng PyEDA, dd, CUDD (Python binding), ...
# Ở đây mình chỉ đưa interface, còn implementation để nhóm bạn tự thiết kế
# cho phù hợp với thư viện chọn.

class BDDReachabilityResult:
    """
    Gói kết quả Task 3:
    - manager     : object của thư viện BDD (vd: BDD manager)
    - reachable   : BDD biểu diễn tập Reach(M0)
    - var_map     : map từ place index -> biến BDD
    - num_states  : số lượng marking reachable (đếm từ BDD)
    """

    def __init__(self,
                 manager: Any,
                 reachable: Any,
                 var_map: Dict[int, Any],
                 num_states: int):
        self.manager = manager
        self.reachable = reachable
        self.var_map = var_map
        self.num_states = num_states


def bddReachability(pn: PetriNet) -> BDDReachabilityResult:
    """
    TASK 3:
    - Mã hoá mỗi place p thành một biến Boolean x_p
    - Mã hoá marking M thành valuation của các biến (x_p = 1 iff M(p) = 1)
    - Dùng symbolic image computation:
        R0 = {M0}
        Ri+1 = Ri ∪ Post(Ri)
      cho đến khi cố định (fixpoint):
        R_{i+1} == R_i
    - Trả về BDD biểu diễn Reach(M0), và số state reachable.

    TODO: nhóm chọn thư viện BDD và hiện thực chi tiết.
    """
    # TODO:
    # 1) Khởi tạo BDD manager & biến cho mỗi place
    # 2) Xây BDD cho initial state M0
    # 3) Xây BDD cho quan hệ chuyển tiếp (transition relation)
    # 4) Lặp fixpoint: R_{i+1} = R_i ∪ Post(R_i) cho đến hội tụ
    # 5) Đếm số state trong BDD (nếu thư viện hỗ trợ)
    raise NotImplementedError


# ============================================================
#  Task 4 – ILP + BDD deadlock detection (20%)
#  “Deadlock detection by using ILP and BDD” :contentReference[oaicite:4]{index=4}
# ============================================================

def findDeadlockILP(pn: PetriNet,
                      reach_res: BDDReachabilityResult) -> Optional[Marking]:
    """
    TASK 4:
    - Kết hợp ILP formulation + BDD Reach(M0) để tìm deadlock.
    - Dead marking = marking không enable bất kỳ transition nào.
    - Deadlock = dead marking nằm trong Reach(M0).

    Hướng chung:
    - Dùng biến ILP cho marking M (0/1 cho mỗi place, vì 1-safe).
    - Thêm ràng buộc:
        + M thuộc Reach(M0): mã hoá bằng BDD (vd chuyển BDD → ràng buộc tuyến tính,
          hoặc enum một phần các marking từ BDD, tuỳ chiến lược).
        + Dead marking: với mọi t, không thỏa điều kiện enabled.
    - Giải ILP:
        + Nếu feasible → trích marking M (trả về tuple).
        + Nếu infeasible → None (không có deadlock).
    """
    # TODO:
    # 1) Chọn thư viện ILP (PuLP, Gurobi, OR-Tools, ...)
    # 2) Tạo model, biến M_p ∈ {0,1}
    # 3) Ràng buộc M thuộc Reach(M0) (dựa trên BDD từ reach_res)
    # 4) Ràng buộc dead marking (không transition nào enabled)
    # 5) Gọi solver, đọc kết quả.
    raise NotImplementedError


# ============================================================
#  Task 5 – Optimization over reachable markings (20%)
#  “maximize c^T M,  M ∈ Reach(M0)” :contentReference[oaicite:5]{index=5}
# ============================================================

def optimizeMarkingILP(pn: PetriNet,
                         reach_res: BDDReachabilityResult,
                         c: List[int]) -> Optional[Tuple[Marking, int]]:
    """
    TASK 5:
    - Cho vector trọng số c (mỗi place một hệ số nguyên),
      tìm marking M ∈ Reach(M0) tối đa hóa c^T M.
    - Nếu không tồn tại tranh nghiệm (infeasible) → trả về None.

    Hướng chung:
    - Cấu trúc ILP tương tự Task 4:
        + Biến M_p ∈ {0,1}
        + Ràng buộc M ∈ Reach(M0) (dùng BDD).
        + Hàm mục tiêu: maximize sum_p c[p] * M_p.
    - Giải ILP, đọc marking tối ưu + giá trị mục tiêu.
    """
    # TODO:
    # 1) Tạo model ILP mới hoặc tái dùng từ Task 4 (nếu bạn thiết kế khéo).
    # 2) Ràng buộc M ∈ Reach(M0) như Task 4.
    # 3) Đặt objective maximize sum c[p] * M_p.
    # 4) Giải và trả kết quả.
    raise NotImplementedError


# ============================================================
#  Hàm tiện ích & main() để test
# ============================================================

def summarizePetriNet(pn: PetriNet) -> None:
    """
    In vài thông tin tóm tắt để debug.
    """
    print("=== Petri Net Summary ===")
    print(f"|P| = {len(pn.places)} places")
    print(f"|T| = {len(pn.transitions)} transitions")
    print(f"M0  = {pn.M0}")
    print("Places:")
    for i, pid in enumerate(pn.places):
        name = pn.place_name.get(pid, pid)
        print(f"  p{i}: id={pid}, name={name}")
    print("Transitions:")
    for j, tid in enumerate(pn.transitions):
        name = pn.trans_name.get(tid, tid)
        print(f"  t{j}: id={tid}, name={name}")


def main():
    parser = argparse.ArgumentParser(
        description="MM-251 Assignment Skeleton: Petri net + BDD + ILP"
    )
    parser.add_argument("pnml_file", help="Đường dẫn tới file PNML đầu vào")
    parser.add_argument(
        "--task",
        choices=["1", "2", "3", "4", "5", "all"],
        default="all",
        help="Task nào muốn chạy (mặc định: all)",
    )
    parser.add_argument(
        "--bfs",
        action="store_true",
        help="Dùng BFS cho Task 2 (mặc định DFS nếu không bật cờ này)",
    )

    args = parser.parse_args()

    # Task 1: đọc PNML
    print("\n[Task 1] Parsing PNML...")
    pn = parsePNML(args.pnml_file)
    summarizePetriNet(pn)

    reachable_markings: Optional[Set[Marking]] = None
    bdd_res: Optional[BDDReachabilityResult] = None

    # Task 2: explicit reachability
    if args.task in ("2", "all"):
        print("\n[Task 2] Explicit reachability (BFS = {})".format(args.bfs))
        reachable_markings = explicitReachability(pn, use_bfs=args.bfs)
        # TODO: in thêm thống kê: số state, ví dụ một vài marking, ...

    # Task 3: BDD-based reachability
    if args.task in ("3", "4", "5", "all"):
        print("\n[Task 3] BDD-based reachability")
        bdd_res = bddReachability(pn)
        # TODO: in số marking reachable từ BDD, so sánh time/memory với Task 2

    # Task 4: Deadlock detection via ILP + BDD
    if args.task in ("4", "all"):
        if bdd_res is None:
            raise RuntimeError("Cần chạy Task 3 trước để có BDD Reach(M0).")
        print("\n[Task 4] ILP + BDD deadlock detection")
        dead = findDeadlockILP(pn, bdd_res)
        if dead is None:
            print("  -> Không tìm thấy deadlock.")
        else:
            print("  -> Deadlock marking:", dead)

    # Task 5: Optimization over reachable markings
    if args.task in ("5", "all"):
        if bdd_res is None:
            raise RuntimeError("Cần chạy Task 3 trước để có BDD Reach(M0).")
        print("\n[Task 5] Optimization over reachable markings")
        # TODO: cho vector c từ file / tham số / hard-code để test
        c = [1] * len(pn.places)  # ví dụ tạm: maximize tổng số token
        opt = optimizeMarkingILP(pn, bdd_res, c)
        if opt is None:
            print("  -> Không tìm được marking tối ưu (problem infeasible).")
        else:
            M_opt, val = opt
            print("  -> Marking tối ưu:", M_opt)
            print("     Giá trị objective:", val)


if __name__ == "__main__":
    main()
