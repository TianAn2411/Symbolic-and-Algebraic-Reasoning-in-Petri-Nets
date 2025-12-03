from src.PetriNet import PetriNet
from src.BDD import bdd_reachable
from src.Optimization import max_reachable_marking
from src.BFS import bfs_reachable
from src.DFS import dfs_reachable
from src.Deadlock import deadlock_reachable_marking
from pyeda.inter import * 
import numpy as np

def main():
    # ------------------------------------------------------
    # 1. Load Petri Net từ file PNML
    # ------------------------------------------------------
    filename = "pnml_file/example.pnml" # đổi file tại đây
    print("Loading PNML:", filename)

    pn = PetriNet.from_pnml(filename)
    print("\n--- Petri Net Loaded ---")
    print(pn)

    # ------------------------------------------------------
    # 2. BFS reachable
    # ------------------------------------------------------
    print("\n--- BFS Reachable Markings ---")
    bfs_set = bfs_reachable(pn)
    # for m in bfs_set:
    #     print(np.array(m))  //nếu mạng quá lớn thì comment lại
    print("Total BFS reachable =", len(bfs_set))

    # ------------------------------------------------------
    # 3. DFS reachable
    # ------------------------------------------------------
    print("\n--- DFS Reachable Markings ---")
    dfs_set = dfs_reachable(pn)
    # for m in dfs_set:
    #     print(np.array(m))
    print("Total DFS reachable =", len(dfs_set))

    # ------------------------------------------------------
    # 4. BDD reachable
    # ------------------------------------------------------
    print("\n--- BDD Reachable ---")
    bdd, count = bdd_reachable(pn)
    # print("Satisfying all:", list(bdd.satisfy_all())) # Tắt dòng này nếu mạng quá lớn
    # print("Minimized =", espresso_exprs(bdd2expr(bdd))) # Tắt dòng này nếu biểu thức quá dài
    print("BDD reachable markings =", count)

    # ------------------------------------------------------
    # 5. Deadlock detection
    # ------------------------------------------------------
    print("\n--- Deadlock reachable marking ---")
    dead = deadlock_reachable_marking(pn, bdd)
    if dead is not None:
        print("Deadlock marking found:", dead)
    else:
        print("No deadlock reachable.")

    # ------------------------------------------------------
    # 6. Optimization: maximize c·M
    # ------------------------------------------------------
    print("\n--- Optimize c·M ---")
    
    num_places = len(pn.place_names)

    if filename == "pnml_file/fsm.pnml":
        weight_map = {
        # Mục tiêu: +10 cho tất cả sản phẩm hoàn thành
        "Done_A1": 10, "Done_A2": 10,
        "Done_B1": 10, "Done_B2": 10,
        
        # Nguyên liệu: -1 cho tất cả đầu vào
        "Start_A1": -1, "Start_A2": -1,
        "Start_B1": -1, "Start_B2": -1,
        
        # Trung gian: +1 để khuyến khích tiến độ
        "A1_In_M1": 1, "A1_In_M2": 1,
        "A2_In_M1": 1, "A2_In_M2": 1,
        "B1_In_M2": 1, "B1_In_M1": 1,
        "B2_In_M2": 1, "B2_In_M1": 1,
        
        # Tài nguyên: 0
        "Res_Machine_1": 0, "Res_Machine_2": 0, "Res_Robot": 0
        }
    elif filename == "pnml_file/hospital.pnml":
        weight_map = {
        "Done_A1": 20, "Done_A2": 20,
        "Done_B1": 10,
        "Start_A1": -2, "Start_A2": -2,
        "Start_B1": -1,
        "A1_With_Nurse": 2, "A1_With_Doctor": 3, "A1_In_Surgery": 5,
        "A2_With_Nurse": 2, "A2_With_Doctor": 3, "A2_In_Surgery": 5,
        "B1_With_Nurse": 1, "B1_With_Doctor": 2,
        "Res_Nurse_1": 0, "Res_Nurse_2": 0, "Res_Doctor": 0, "Res_SurgeryRoom": 0
        }
    elif filename == "pnml_file/example.pnml":  
        weight_map = {
            # Mục tiêu: Càng nhiều người ĂN càng tốt
            "EAT_1": 10, "EAT_2": 10, "EAT_3": 10, 
            "EAT_4": 10, "EAT_5": 10, "EAT_6": 10,
            
            # Phạt trạng thái chờ (để tránh Deadlock)
            "WAIT_LEFT_FORK_1": -1, "WAIT_RIGHT_FORK_1": -1,
            "WAIT_LEFT_FORK_2": -1, "WAIT_RIGHT_FORK_2": -1,
            "WAIT_LEFT_FORK_3": -1, "WAIT_RIGHT_FORK_3": -1,
            "WAIT_LEFT_FORK_4": -1, "WAIT_RIGHT_FORK_4": -1,
            "WAIT_LEFT_FORK_5": -1, "WAIT_RIGHT_FORK_5": -1,
            "WAIT_LEFT_FORK_6": -1, "WAIT_RIGHT_FORK_6": -1,
            
            # Tài nguyên: 0
            "FORK_1": 0, "FORK_2": 0, "FORK_3": 0,
            "FORK_4": 0, "FORK_5": 0, "FORK_6": 0
        }
    elif filename == "pnml_file/philo12.pnml":
        weight_map = {}
        for i in range(12):
            weight_map[f"Eat_{i}"] = 10
            weight_map[f"Wait_{i}"] = -1
            weight_map[f"Think_{i}"] = 0
            weight_map[f"Fork_{i}"] = 0
    else:
        weight_map = {
        # Mục tiêu: Khách A lên phòng, Khách B rời đi (+10)
        "A1_In_Room_Done": 10, "A2_In_Room_Done": 10,
        "B1_Checked_Out": 10, "B2_Checked_Out": 10,
        
        # Khách chờ: Điểm phạt để ép hệ thống xử lý nhanh (-1)
        "A1_Arrive_Lobby": -1, "A2_Arrive_Lobby": -1,
        "B1_Leave_Room": -1, "B2_Leave_Room": -1,
        
        # Đang làm thủ tục: Khuyến khích (+2)
        "A1_At_Reception": 2, "A1_Has_Key": 3,
        "A2_At_Reception": 2, "A2_Has_Key": 3,
        "B1_In_Elevator": 3, "B1_Paying": 2,
        "B2_In_Elevator": 3, "B2_Paying": 2,
        
        # Tài nguyên: 0
        "Res_Receptionist": 0, "Res_Elevator": 0,
        "Res_RoomKey_101": 0, "Res_RoomKey_102": 0
        }
    
    c = np.zeros(num_places, dtype=int)
    
    # Duyệt qua danh sách Place đã sắp xếp của mạng để gán trọng số đúng vị trí
    for i, name in enumerate(pn.place_names):
        c[i] = weight_map.get(name, 0) # Nếu không có tên trong map thì mặc định là 0
        
    print(f"Generated Smart Weight Vector c:\n{c}") 
    max_mark, max_val = max_reachable_marking(
        pn.place_ids, bdd, c
    )
    
    print("Max marking found:", max_mark)
    print("Max value (c·M):", max_val)


if __name__ == "__main__":
    main()