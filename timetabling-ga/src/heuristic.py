import random

# MRV (Minimum Remaining Values): chọn lớp có ít timeslot khả thi nhất
def heuristic_mrv(dataset):
    # Dùng c.get('possible_times') để trả về None nếu khóa không tồn tại.
# Sau đó kiểm tra xem giá trị trả về có giá trị (True) hay không.
    classes = sorted(dataset['classes'], 
                 key=lambda c: len(c['possible_times']) if c.get('possible_times') else 999)    
    return classes

# LCV (Least Constraining Value): chọn ca học ít gây xung đột nhất cho các lớp khác
def heuristic_lcv(class_data, timeslots, assigned):
    # Đếm số lần 1 timeslot đã được dùng -> càng ít dùng càng tốt
    usage = {ts['timeslot_id']: 0 for ts in timeslots}
    for (_, (ts, _)) in assigned.items():
        usage[ts] = usage.get(ts, 0) + 1
    # Ưu tiên timeslot ít dùng nhất
    sorted_ts = sorted(usage.keys(), key=lambda t: usage[t])
    return sorted_ts

# Degree heuristic: ưu tiên lớp có nhiều xung đột tiềm năng nhất (chung giảng viên, cùng loại phòng)
def heuristic_degree(dataset):
    conflict_count = {}
    for c1 in dataset['classes']:
        count = 0
        for c2 in dataset['classes']:
            if c1 == c2:
                continue
            if c1['teacher_id'] == c2['teacher_id'] or c1['room_type'] == c2['room_type']:
                count += 1
        conflict_count[c1['class_id']] = count
    classes_sorted = sorted(dataset['classes'], key=lambda c: conflict_count[c['class_id']], reverse=True)
    return classes_sorted

# Kết hợp MRV + Degree khi khởi tạo
import random # Đảm bảo import thư viện này nếu chưa có

def heuristic_seed(dataset):
    classes = heuristic_mrv(dataset)
    degree_sorted = heuristic_degree(dataset)
    
    # Sắp xếp theo thứ tự MRV, sau đó là Degree (nếu có)
    classes = sorted(classes, key=lambda c: degree_sorted.index(c) if c in degree_sorted else 0)
    
    assignment = {}
    rooms = dataset['rooms']
    timeslots = dataset['timeslots']
    room_ids = [r['room_id'] for r in rooms]
    
    # KHAI BÁO 1: Đưa việc tính timeslot_ids lên trên cùng (Đã sửa lỗi timeslot_id -> slot_id)
    timeslot_ids = [t['slot_id'] for t in timeslots] 
    
    for c in classes:
        # KHAI BÁO 2: Logic gán ts an toàn (Được đặt bên trong vòng lặp)
        
        # SỬA LỖI KEYERROR: 'possible_times'
        if c.get('possible_times'):
            ts = random.choice(c['possible_times'])
        else:
            # Nếu khóa không tồn tại hoặc danh sách rỗng, chọn ngẫu nhiên từ TẤT CẢ timeslot
            ts = random.choice(timeslot_ids) 
            
        r = random.choice(room_ids)
        assignment[c['class_id']] = (ts, r)
        
    return assignment
    classes = heuristic_mrv(dataset)
    degree_sorted = heuristic_degree(dataset)
    
    # Sắp xếp theo thứ tự MRV, sau đó là Degree (nếu có)
    classes = sorted(classes, key=lambda c: degree_sorted.index(c) if c in degree_sorted else 0)
    
    assignment = {}
    rooms = dataset['rooms']
    timeslots = dataset['timeslots']
    room_ids = [r['room_id'] for r in rooms]
    ts = random.choice(c.get('possible_times')) if c.get('possible_times') else random.choice([t['slot_id'] for t in timeslots])
    # Khai báo timeslot_ids để tránh lặp lại logic
    timeslot_ids = [t['slot_id'] for t in timeslots] # SỬA LỖI TIMESLOT_ID THÀNH SLOT_ID
    
    for c in classes:
        # SỬA LỖI KEYERROR: 'possible_times'
        # Dùng c.get() để kiểm tra sự tồn tại của khóa một cách an toàn
        if c.get('possible_times'):
            ts = random.choice(c['possible_times'])
        else:
            # Nếu không có ràng buộc khả thi, chọn ngẫu nhiên từ TẤT CẢ timeslot
            ts = random.choice(timeslot_ids) 
            
        r = random.choice(room_ids)
        assignment[c['class_id']] = (ts, r)
        
    return assignment

