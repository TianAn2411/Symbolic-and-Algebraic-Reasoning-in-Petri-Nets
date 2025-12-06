import sys
import os
import argparse
import numpy as np
from src.PetriNet import PetriNet
from src.BDD import bdd_reachable
from src.Optimization import max_reachable_marking
from src.BFS import bfs_reachable
from src.DFS import dfs_reachable
from src.Deadlock import deadlock_reachable_marking

def get_weight_vector(pn, filename):
    """
    Hàm hỗ trợ xác định vector trọng số c dựa trên tên file
    """
    num_places = len(pn.place_names)
    weight_map = {}
    
    # Chuẩn hóa tên file để so sánh (bỏ đường dẫn thư mục nếu cần)
    base_name = os.path.basename(filename)

    if "fsm.pnml" in base_name:
        weight_map = {
            "Done_A1": 10, "Done_A2": 10, "Done_B1": 10, "Done_B2": 10,
            "Start_A1": -1, "Start_A2": -1, "Start_B1": -1, "Start_B2": -1,
            "A1_In_M1": 1, "A1_In_M2": 1, "A2_In_M1": 1, "A2_In_M2": 1,
            "B1_In_M2": 1, "B1_In_M1": 1, "B2_In_M2": 1, "B2_In_M1": 1,
            "Res_Machine_1": 0, "Res_Machine_2": 0, "Res_Robot": 0
        }
    elif "hospital.pnml" in base_name:
        weight_map = {
            "Done_A1": 20, "Done_A2": 20, "Done_B1": 10,
            "Start_A1": -2, "Start_A2": -2, "Start_B1": -1,
            "A1_With_Nurse": 2, "A1_With_Doctor": 3, "A1_In_Surgery": 5,
            "A2_With_Nurse": 2, "A2_With_Doctor": 3, "A2_In_Surgery": 5,
            "B1_With_Nurse": 1, "B1_With_Doctor": 2,
            "Res_Nurse_1": 0, "Res_Nurse_2": 0, "Res_Doctor": 0, "Res_SurgeryRoom": 0
        }
    elif "philo6.pnml" in base_name:
        weight_map = {
            "EAT_1": 10, "EAT_2": 10, "EAT_3": 10, 
            "EAT_4": 10, "EAT_5": 10, "EAT_6": 10,
            "WAIT_LEFT_FORK_1": -1, "WAIT_RIGHT_FORK_1": -1,
            "WAIT_LEFT_FORK_2": -1, "WAIT_RIGHT_FORK_2": -1,
            "WAIT_LEFT_FORK_3": -1, "WAIT_RIGHT_FORK_3": -1,
            "WAIT_LEFT_FORK_4": -1, "WAIT_RIGHT_FORK_4": -1,
            "WAIT_LEFT_FORK_5": -1, "WAIT_RIGHT_FORK_5": -1,
            "WAIT_LEFT_FORK_6": -1, "WAIT_RIGHT_FORK_6": -1,
            "FORK_1": 0, "FORK_2": 0, "FORK_3": 0,
            "FORK_4": 0, "FORK_5": 0, "FORK_6": 0
        }
    elif "philo12.pnml" in base_name:
        weight_map = {}
        for i in range(12):
            weight_map[f"Eat_{i}"] = 10
            weight_map[f"Wait_{i}"] = -1
            weight_map[f"Think_{i}"] = 0
            weight_map[f"Fork_{i}"] = 0
    elif "hotel.pnml" in base_name:
        weight_map = {
            "A1_In_Room_Done": 10, "A2_In_Room_Done": 10,
            "B1_Checked_Out": 10, "B2_Checked_Out": 10,
            "A1_Arrive_Lobby": -1, "A2_Arrive_Lobby": -1,
            "B1_Leave_Room": -1, "B2_Leave_Room": -1,
            "A1_At_Reception": 2, "A1_Has_Key": 3,
            "A2_At_Reception": 2, "A2_Has_Key": 3,
            "B1_In_Elevator": 3, "B1_Paying": 2,
            "B2_In_Elevator": 3, "B2_Paying": 2,
            "Res_Receptionist": 0, "Res_Elevator": 0,
            "Res_RoomKey_101": 0, "Res_RoomKey_102": 0
        }
    
    # Tạo vector c 
    c = np.zeros(num_places, dtype=int)
    for i, name in enumerate(pn.place_names):
        c[i] = weight_map.get(name, 0)

    # Xử lý override đặc biệt cho complex.pnml
    if "complex.pnml" in base_name:
        c_hardcoded = [-3, 1, 4, -1, 1, 0, 3, -5, 5, -4, -2, 2, 5, 4, 5, -1, 2, 0, 1, 0]
        if len(c_hardcoded) == num_places:
            c = np.array(c_hardcoded)
        else:
            # Nếu số lượng place không khớp, trả về warning trong log
            pass 

    return c

def run_analysis(filename):
    """
    Chạy phân tích cho 1 file và trả về chuỗi kết quả
    """
    result_log = []
    
    def log(message):
        print(message)
        result_log.append(str(message))

    log("="*60)
    log(f"PROCESSING FILE: {filename}")
    log("="*60)

    try:
        # 1. Load Petri Net
        if not os.path.exists(filename):
            log(f"Error: File {filename} not found.")
            return "\n".join(result_log)

        pn = PetriNet.from_pnml(filename)
        log("--- Petri Net Loaded ---")
        log(f"Places: {len(pn.place_names)}")
        log(f"Transitions: {len(pn.trans_ids)}")
        log(pn)

        # 2. BFS
        log("\n--- BFS Reachable Markings ---")
        bfs_set = bfs_reachable(pn)
        log(f"Total BFS reachable = {len(bfs_set)}")

        # 3. DFS
        log("\n--- DFS Reachable Markings ---")
        dfs_set = dfs_reachable(pn)
        log(f"Total DFS reachable = {len(dfs_set)}")

        # 4. BDD
        log("\n--- BDD Reachable ---")
        bdd, count = bdd_reachable(pn)
        log(f"BDD reachable markings = {count}")

        # 5. Deadlock
        log("\n--- Deadlock reachable marking ---")
        dead = deadlock_reachable_marking(pn, bdd)
        if dead is not None:
            log(f"Deadlock marking found: {dead}")
        else:
            log("No deadlock reachable.")

        # 6. Optimization
        log("\n--- Optimize c·M ---")
        c = get_weight_vector(pn, filename)
        
        # Chỉ hiển thị vector c nếu ngắn, dài quá thì hiển thị tóm tắt
        
        log(f"Weight Vector c:\n{c}")

        max_mark, max_val = max_reachable_marking(pn.place_ids, bdd, c)
        log(f"Max marking found: {max_mark}")
        log(f"Max value (c·M): {max_val}")
        
    except Exception as e:
        log(f"\nCRITICAL ERROR analyzing {filename}: {e}")
        import traceback
        log(traceback.format_exc())

    log("\n")
    return "\n".join(result_log)

def main():
    parser = argparse.ArgumentParser(description="Run Petri Net Analysis")
    
    # Thêm argument --file
    parser.add_argument("filename", nargs="?", help="Path to the .pnml file to analyze")
    
    # Thêm argument --all
    parser.add_argument("--all", action="store_true", help="Run all predefined test files and save to result.txt")
    
    args = parser.parse_args()

    # Danh sách các file test mặc định
    test_files = [
        "pnml_file/fsm.pnml",
        "pnml_file/hospital.pnml",
        "pnml_file/hotel.pnml",
        "pnml_file/philo6.pnml",
        "pnml_file/complex.pnml",
        "pnml_file/philo12.pnml"
    ]

    if args.all:
        print("Running ALL tests. Output will be saved to result.txt...")
        full_report = ""
        
        # Đảm bảo thư mục tồn tại
        if not os.path.exists("pnml_file"):
            print("Warning: Directory 'pnml_file' not found. Please check paths.")

        for f in test_files:
            report = run_analysis(f)
            full_report += report + "\n"
        
        # Ghi ra file
        with open("result.txt", "w", encoding="utf-8") as file:
            file.write(full_report)
            
        print("\nAll tests finished. Check 'result.txt' for details.")
        
    elif args.filename:
        full_report = ""
        # Chạy 1 file cụ thể 
        report = run_analysis(args.filename)
        full_report += report + "\n"
        with open("result.txt", "w", encoding="utf-8") as file:
            file.write(full_report)
        
        result = "\n test " + args.filename + " finished. Check 'result.txt' for details."
        print(result)
        
    else:

        print("Usage:")
        print("  Run specific file: python run.py pnml_file/fsm.pnml")
        print("  Run all tests:     python run.py --all")
        print("  Run default:       python run.py pnml_file/fsm.pnml")
        
 
        print("\nRunning default (fsm.pnml)...")
        run_analysis("pnml_file/fsm.pnml")

if __name__ == "__main__":
    main()