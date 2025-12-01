import numpy as np
import xml.etree.ElementTree as ET
from typing import List, Optional, Dict


class PetriNet:
    def __init__(
        self,
        place_ids: List[str],
        trans_ids: List[str],
        place_names: List[Optional[str]],
        trans_names: List[Optional[str]],
        I: np.ndarray,   # (num_trans, num_places)
        O: np.ndarray,   # (num_trans, num_places)
        M0: np.ndarray   # (num_places,)
    ):
        self.place_ids = place_ids
        self.trans_ids = trans_ids
        self.place_names = place_names
        self.trans_names = trans_names
        self.I = I
        self.O = O
        self.M0 = M0

    @classmethod
    def from_pnml(cls, filename: str) -> "PetriNet":
        # Đọc file PNML
        tree = ET.parse(filename)
        root = tree.getroot()

        # Namespace (nếu file có dùng)
        ns_url = root.tag.split("}")[0].strip("{") if "}" in root.tag else ""
        ns = {"pnml": ns_url} if ns_url else {}

        def find_all(parent, tag_name: str):
            """Tìm tất cả tag bất chấp namespace."""
            if ns:
                return parent.findall(f".//pnml:{tag_name}", ns)
            else:
                return parent.findall(f".//{tag_name}")

        # ---------- 1. Đọc places ----------
        place_ids: List[str] = []
        place_names: List[Optional[str]] = []
        initial_tokens: Dict[str, int] = {}

        for p in find_all(root, "place"):
            pid = p.get("id")
            if pid is None:
                continue

            place_ids.append(pid)

            # Tên place (nếu có)
            name_text: Optional[str] = None
            name_tag = p.find("pnml:name" if ns else "name", ns)
            if name_tag is not None:
                text_tag = name_tag.find("pnml:text" if ns else "text", ns)
                if text_tag is not None and text_tag.text:
                    name_text = text_tag.text.strip()
            place_names.append(name_text)

            # Initial marking (initialMarking hoặc hlinitialMarking)
            marking_val = 0
            for tag_candidate in ("initialMarking", "hlinitialMarking"):
                m_tag = p.find(f"pnml:{tag_candidate}" if ns else tag_candidate, ns)
                if m_tag is not None:
                    text_tag = m_tag.find("pnml:text" if ns else "text", ns)
                    if text_tag is not None and text_tag.text:
                        try:
                            marking_val = int(text_tag.text.strip())
                        except ValueError:
                            marking_val = 0
                    break
            # 1-safe → >0 token coi như 1
            initial_tokens[pid] = 1 if marking_val > 0 else 0

        place_index = {pid: i for i, pid in enumerate(place_ids)}

        # Vector M0 theo thứ tự place_ids
        M0_list = [0] * len(place_ids)
        for pid, tok in initial_tokens.items():
            idx = place_index[pid]
            M0_list[idx] = tok
        M0 = np.array(M0_list, dtype=int)

        # ---------- 2. Đọc transitions ----------
        trans_ids: List[str] = []
        trans_names: List[Optional[str]] = []

        for t in find_all(root, "transition"):
            tid = t.get("id")
            if tid is None:
                continue

            trans_ids.append(tid)

            # Tên transition (nếu có)
            name_text: Optional[str] = None
            name_tag = t.find("pnml:name" if ns else "name", ns)
            if name_tag is not None:
                text_tag = name_tag.find("pnml:text" if ns else "text", ns)
                if text_tag is not None and text_tag.text:
                    name_text = text_tag.text.strip()
            trans_names.append(name_text)

        trans_index = {tid: i for i, tid in enumerate(trans_ids)}

        num_places = len(place_ids)
        num_trans = len(trans_ids)

        # ---------- 3. Ma trận I, O ----------
        # CHÚ Ý: dạng (num_trans, num_places) để phù hợp test:
        #   I[t, p] = số token cần ở place p để t bắn
        #   O[t, p] = số token sinh ra ở place p khi t bắn
        I = np.zeros((num_trans, num_places), dtype=int)
        O = np.zeros((num_trans, num_places), dtype=int)

        for a in find_all(root, "arc"):
            src = a.get("source")
            tgt = a.get("target")
            if src is None or tgt is None:
                continue

            # Đọc weight (inscription/text), mặc định = 1
            weight = 1
            inscription = a.find("pnml:inscription" if ns else "inscription", ns)
            if inscription is not None:
                text_tag = inscription.find("pnml:text" if ns else "text", ns)
                if text_tag is not None and text_tag.text:
                    try:
                        weight = int(text_tag.text.strip())
                    except ValueError:
                        weight = 1

            # Place -> Transition: cập nhật I[t, p]
            if src in place_index and tgt in trans_index:
                p_idx = place_index[src]
                t_idx = trans_index[tgt]
                I[t_idx, p_idx] += weight

            # Transition -> Place: cập nhật O[t, p]
            elif src in trans_index and tgt in place_index:
                t_idx = trans_index[src]
                p_idx = place_index[tgt]
                O[t_idx, p_idx] += weight

            else:
                # Arc trỏ tới id không tồn tại – bỏ qua (hoặc log cảnh báo)
                continue

        # ---------- 4. Kiểm tra đơn giản ----------
        assert M0.shape[0] == num_places, "Kích thước M0 không khớp số place"

        return cls(
            place_ids=place_ids,
            trans_ids=trans_ids,
            place_names=place_names,
            trans_names=trans_names,
            I=I,
            O=O,
            M0=M0,
        )

    def __str__(self) -> str:
        s = []
        s.append("Places: " + str(self.place_ids))
        s.append("Place names: " + str(self.place_names))
        s.append("\nTransitions: " + str(self.trans_ids))
        s.append("Transition names: " + str(self.trans_names))
        s.append("\nI (input) matrix:")
        s.append(str(self.I))
        s.append("\nO (output) matrix:")
        s.append(str(self.O))
        s.append("\nInitial marking M0:")
        s.append(str(self.M0))
        return "\n".join(s)
