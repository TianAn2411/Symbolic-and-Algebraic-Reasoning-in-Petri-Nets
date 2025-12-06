# MATHEMATICAL MODELING – CO2011

## Symbolic and Algebraic Reasoning in Petri Nets  

**Giảng viên ra đề / hướng dẫn:** Dr. Van-Giang Trinh  
**Khoa:** Faculty of Computer Science and Engineering – HCMUT

---

## Thành viên

| Họ tên                    | MSSV    | Lớp | Email                               | Ghi chú  |
|--------------------------|---------|-----|-------------------------------------|---------|
| Nguyễn Tô Quốc Việt      | 2313898 |     | viet.nguyenluminous@hcmut.edu.vn    |         |
| **Trương Thiên Ân** | **2310190** | **TN02** | **an.truong241105@hcmut.edu.vn** | **Leader** |
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
4. Kiểm chứng tính chất **Deadlock** bằng phương pháp kết hợp BDD và ILP.
5. Giải quyết bài toán **Tối ưu hóa (Optimization)** và đánh giá hiệu năng tổng thể.

---

## Chi tiết các Task và Hàm hiện thực

### **Task 1 – PNML Parser & PetriNet Model**
- Đọc file `.pnml` theo chuẩn 1-safe PNML.
- Xây dựng cấu trúc dữ liệu cơ sở.

### **Task 2 – Explicit Reachability (BFS/DFS)**
- Duyệt không gian trạng thái bằng thuật toán tìm kiếm BFS/DFS.
  
### **Task 3 – Symbolic Reachability with BDD**
- Mã hóa Petri net và tính toán tập reachable markings sử dụng Binary Decision Diagrams (BDD) để xử lý bùng nổ trạng thái.

### **Task 4 – Deadlock Detection (ILP-based Analysis)**
- Phân tích tính chất hệ thống, cụ thể là tìm kiếm trạng thái Deadlock (nơi hệ thống dừng hoạt động).
- Sử dụng Integer Linear Programming (ILP) để lọc kết quả từ BDD.

### **Task 5 – Optimization & Evaluation**
- **Optimization:** Tìm marking đạt được (`reachable marking`) sao cho hàm mục tiêu $c \cdot M$ là lớn nhất.
  - Sử dụng thuật toán **Branch & Cut** kết hợp BDD và LP Relaxation.
---

## Cấu trúc thư mục

```text
.
├── README.md                  # Thông tin dự án và hướng dẫn
├── mm-251-assignment.pdf      # Đề bài
├── pnml_file/                 # Thư mục chứa các file .pnml test case
│   ├── fsm.pnml           # Hệ thống sản xuất
│   ├── hospital.pnml      # Quy trình bệnh viện
│   ├── hotel.pnml         # Hệ thống khách sạn
│   ├── philo6.pnml        # Bài toán các triết gia (6 places)
│   ├── philo12.pnml       # Bài toán các triết gia (12 places)
│   ├── complex.pnml       # Một mạng phức tạp với 20 places để test hiệu năng
├── src/                       # Source code chính
│   ├── PetriNet.py            # Model & Parser
│   ├── BFS.py                 # Explicit BFS
│   ├── DFS.py                 # Explicit DFS
│   ├── BDD.py                 # Symbolic Reachability
│   ├── Deadlock.py            # Deadlock Detection (Task 4)
│   └── Optimization.py        # Optimization (Task 5)
├── run.py                     # Script chính để chạy demo tổng hợp
├── result.txt                 # Kết quả chạy run.py
└── requirements.txt           # Danh sách thư viện cần thiết
```
---
## Bảng phân việc

| Task | Người phụ trách | MSSV | Tiến độ | Note                                       |
|:----:|------------------|:----:|:-------:|-------------------------------------------|
| 1    | Quốc Việt          | 2313898| 100% |                                          |
| 2    | Thiên Ân           | 2310190| 100% |                                          |
| 3.1  | Nguyên Khôi        | 2420020| 100% |                                          |
| 3.2  |Hoàng Nam           | 2412177| 100% |                                          |
| 4    |Nhật Minh           | 2412102| 100% |                                          |
| 5    |Thiên Ân & Quốc Việt|        | 100% |                                          |

---
## Hướng dẫn Cài đặt và Chạy chương trình

### Clone repository

```bash
git clone git@github.com:TianAn2411/Symbolic-and-Algebraic-Reasoning-in-Petri-Nets.git
cd Symbolic-and-Algebraic-Reasoning-in-Petri-Nets
```

### Ubuntu/Linux
#### Chuẩn bị môi trường
```bash
# 1. Cài đặt pip và venv nếu chưa có
sudo apt update
sudo apt install python3-pip python3-venv

# 2. Tạo môi trường ảo
python3 -m venv venv

# 3. Kích hoạt môi trường ảo
source venv/bin/activate

# 4. Tải các thư viện cần thiết
pip install -r requirements.txt
```

#### Chạy test
```bash
# 1. Chạy test mặc định của chương trình
python3 run.py

# 2. Chạy test tự chọn
python3 run.py <đường dẫn tới file pnml> (các file có sẵn trong pnml_file)

Caution: Nếu các bạn có file pnml riêng thì nên cấu hình thêm vecto C để chạy task 5 vì trong run.py là đã cấu hình sẵn vector C để phục vụ chạy test

# 3. Chạy tất cả các test
python3 run.py --all
```
Kết quả chạy sẽ được lưu vào `result.txt`

### Window
#### Chuẩn bị môi trường
```bash
# 1. Tải các thư viện cần thiết
pip install -r requirements.txt
```

#### Chạy test
```bash
# 1. Chạy test mặc định của chương trình
python run.py

# 2. Chạy test tự chọn
python run.py <đường dẫn tới file pnml> (các file có sẵn trong pnml_file)

Caution: Nếu các bạn có file pnml riêng thì nên cấu hình thêm vecto C để chạy task 5 vì trong run.py là đã cấu hình sẵn vector C để phục vụ chạy test

# 3. Chạy tất cả các test
python run.py --all
```
Kết quả chạy sẽ được lưu vào `result.txt`
