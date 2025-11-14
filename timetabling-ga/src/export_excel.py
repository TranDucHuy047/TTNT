import pandas as pd
import os # Cần import os để tạo thư mục nếu chưa tồn tại

def export_schedule(schedule, path="output/schedule.xlsx"):
    # Đảm bảo thư mục output tồn tại
    output_dir = os.path.dirname(path)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    rows = []
    for class_id, (timeslot, room) in schedule.items():
        rows.append({"class_id": class_id, "timeslot": timeslot, "room": room})
    df = pd.DataFrame(rows)
    df.to_excel(path, index=False)
    print(f"✅ Exported schedule to {path}")