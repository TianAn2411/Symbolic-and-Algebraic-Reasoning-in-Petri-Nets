# MATHEMATICAL MODELING – CO2011

## Symbolic and Algebraic Reasoning in Petri Nets  
*Version 0.0.2*

**Giảng viên ra đề / hướng dẫn:** Dr. Van-Giang Trinh  
**Khoa:** Faculty of Computer Science and Engineering – HCMUT

---

## Thành viên

| Họ tên                    | MSSV    | Lớp | Email                               | Ghi chú  |
|--------------------------|---------|-----|-------------------------------------|---------|
| Nguyễn Tô Quốc Việt      | 2313898 |     | viet.nguyenluminous@hcmut.edu.vn    |         |
| **Trương Thiên Ân**          | **2310190** |  **TN02**   | **an.truong241105@hcmut.edu.vn**        | **Leader**  |
| Nguyễn Hồ Nguyên Khôi    | 2420020 |     | khoi.nguyen2420020@hcmut.edu.vn     |         |
| Nguyễn Hoàng Nam         | 2412177 | L04 | nam.nguyen270905@hcmut.edu.vn       |         |
| Nguyễn Thế Nhật Minh     | 2412102 |     | minh.nguyenthenhat@hcmut.edu.vn     |         |

---

## Giới thiệu chung

Bài tập lớn hiện thực và phân tích **1-safe Petri net** cho môn *MATHEMATICAL MODELING – CO2011*, theo chủ đề:

> **Symbolic and Algebraic Reasoning in Petri Nets**

Nhóm triển khai một pipeline đầy đủ:

1. Đọc mô hình Petri net từ file chuẩn **PNML**.
2. Tính toán **reachable markings** bằng phương pháp **explicit (BFS/DFS)**.
3. Biểu diễn Petri net và reachable set theo hướng **symbolic (BDD)**.
4. Mô hình hóa một số bài toán đánh giá / kiểm chứng bằng **ILP**.
5. Thực nghiệm, so sánh, và rút ra nhận xét giữa các phương pháp.

---

## Giới thiệu ngắn các Task

- **Task 1 – PNML Parser & PetriNet model**  
  - Đọc file `.pnml` theo chuẩn 1-safe PNML của đề bài.  
  - Trích xuất:
    - danh sách places, transitions, arcs,
    - ma trận `pre`, `post`,
    - marking ban đầu `M0`.  
  - Xây dựng cấu trúc `PetriNet` dùng chung cho các task sau.

- **Task 2 – Explicit Reachability (BFS/DFS)**  
  - Dùng BFS/DFS duyệt state space bắt đầu từ `M0`.  
  - Marking biểu diễn dưới dạng vector 0/1 (1-safe).  
  - Hiện thực:
    - `is_enabled(pn, t, M)` – kiểm tra transition enabled,  
    - `fire(pn, t, M)` – bắn transition,  
    - `explicitReachability(pn)` – trả về tập reachable markings.

- **Task 3.1 – BDD Encoding**  
  - Encode marking Petri net thành các biến Boolean cho BDD.  
  - Encode quan hệ chuyển tiếp (transition relation) trên BDD.  
  - Chuẩn bị cho bước symbolic reachability.

- **Task 3.2 – Symbolic Reachability with BDD**  
  - Sử dụng BDD để tính reachable markings một cách symbolic.  
  - So sánh:
    - số lượng trạng thái,
    - thời gian chạy,
    - dung lượng bộ nhớ  
    với kết quả từ Task 2 trên các mô hình PNML nhỏ/ trung bình.

- **Task 4 – ILP-based Analysis**  
  - Mô hình hóa một số thuộc tính / bài toán trên Petri net dưới dạng **Integer Linear Programming (ILP)** (theo yêu cầu cụ thể trong assignment).  
  - Xây dựng biến, ràng buộc, và (nếu có) hàm mục tiêu.  
  - Giải bằng solver phù hợp.

- **Task 5 – Evaluation & Comparison**  
  - Chạy nhiều mô hình `.pnml` khác nhau.  
  - Thu thập số liệu:
    - số reachable markings,
    - thời gian / bộ nhớ cho explicit (Task 2), symbolic BDD (Task 3.x), và ILP (Task 4 nếu áp dụng).  
  - Tổng hợp bảng kết quả, vẽ biểu đồ (nếu cần) và đưa ra nhận xét.  
  - **Task 5 được phối hợp bởi các thành viên làm Task 1 và Task 2.**

---

## Cấu trúc thư mục (dự kiến)


```text
.
├── README.md
├── mm-251-assignment.pdf      # Đề bài, file PDF, tài liệu môn học
├── pnml_file/                    # Các file .pnml dùng để test
├── src/               # Hàm hỗ trợ (đọc config, in kết quả, v.v.)
├── run.py             # Hàm test tất cả các test dựa vào input từ pnml_file/
└── requirements.txt           # (Nếu dùng thư viện ngoài / venv)
```
---
## Bảng phân việc

| Task | Người phụ trách | MSSV | Tiến độ | Note                                      |
|:----:|------------------|:----:|:-------:|-------------------------------------------|
| 1    | Quốc Việt          | 2313898| 100% |                                          |
| 2    | Thiên Ân           | 2310190| 100% |                                          |
| 3.1  | Nguyên Khôi        | 2420020| 100% |                                          |
| 3.2  |Hoàng Nam           | 2412177| 100% |                                          |
| 4    |Nhật Minh           | 2412102| 100% |                                          |
| 5    |Thiên Ân & Quốc Việt|        | 100% |                                          |

