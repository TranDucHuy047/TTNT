import csv
import pathlib
import os 

def _load_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def load_dataset(folder="data/base"):
    """
    Đọc dataset từ một thư mục (VD: data/base hoặc data/tests/case_small_rooms).
    Bắt buộc có: classes.csv, rooms.csv, teachers.csv, timeslots.csv
    Tùy chọn: feasible.csv (cột: class_id, slot_id)
    """
    
    # 1. Lấy đường dẫn tuyệt đối đến thư mục chứa file data_loader.py (thư mục 'src')
    current_file_path = pathlib.Path(__file__).resolve()
    
    # 2. Đi lên 2 cấp: từ /src -> /timetabling-ga (thư mục code) -> /timetabling-ga (thư mục gốc)
    project_base_dir = current_file_path.parent.parent
    
    # 3. Kết hợp đường dẫn gốc với tham số folder (VD: "data" hoặc "data/tests/...")
    # Thư mục chứa data thực sự là project_root / folder_name
    data_dir = project_base_dir / folder
    
    # --- PHẦN SỬA ĐỔI LỖI ĐƯỜNG DẪN KẾT THÚC ---

    # Sửa folder thành đường dẫn tuyệt đối đã tính toán
    folder = os.fspath(data_dir) 

    classes_path   = os.path.join(folder, "classes.csv")
    rooms_path     = os.path.join(folder, "rooms.csv")
    teachers_path  = os.path.join(folder, "teachers.csv")
    timeslots_path = os.path.join(folder, "timeslots.csv")
    feasible_path  = os.path.join(folder, "feasible.csv")

    classes   = _load_csv(classes_path)
    rooms     = _load_csv(rooms_path)
    # ... (các dòng code còn lại giữ nguyên) ...
    teachers  = _load_csv(teachers_path)
    timeslots = _load_csv(timeslots_path)

    # Chuẩn hóa/ép kiểu nhẹ (an toàn)
    # ... (giữ nguyên) ...

    dataset = {
        "classes": classes,
        "rooms": rooms,
        "teachers": teachers,
        "timeslots": timeslots,
    }

    if os.path.exists(feasible_path):
        dataset["feasible"] = _load_csv(feasible_path)  # cột: class_id, slot_id

    return dataset