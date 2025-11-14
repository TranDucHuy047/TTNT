import random
from .fitness import compute_fitness as fitness
from .heuristic import heuristic_seed


# ----------------- helpers -----------------

def _slot_id_of(row):
    # chấp nhận cả 'slot_id' và 'timeslot_id'
    return row.get('slot_id') or row.get('timeslot_id')

def _all_slot_ids(dataset):
    return [_slot_id_of(t) for t in dataset['timeslots']]

def _room_info_maps(dataset):
    cap = {r['room_id']: int(r['capacity']) for r in dataset['rooms']}
    rtype = {r['room_id']: r['room_type'] for r in dataset['rooms']}
    return cap, rtype

def _pick_room_for(class_row, dataset):
    room_cap, room_type = _room_info_maps(dataset)
    req  = class_row.get('room_type') or class_row.get('room_type_required')
    size = int(class_row.get('size', 0))
    # 1) đúng loại + đủ chỗ
    cands = [rid for rid in room_cap if room_type[rid] == req and room_cap[rid] >= size]
    if not cands:
        # 2) đúng loại
        cands = [rid for rid in room_cap if room_type[rid] == req]
    if not cands:
        # 3) fallback: mọi phòng
        cands = list(room_cap.keys())
    return random.choice(cands)

def _prefer_early_slot(slot_ids, dataset):
    # Ưu tiên 07:00, 09:00, 11:00
    start = { _slot_id_of(t): t.get('start') for t in dataset['timeslots'] }
    early = [s for s in slot_ids if start.get(s) in ('07:00','09:00','11:00')]
    return random.choice(early if early else slot_ids)

def _parse_feasible_times(c):
    """
    Trả về danh sách timeslot khả dụng cho lớp c nếu có cột
    (feasible_timeslots hoặc possible_times), ngược lại None.
    """
    s = c.get('feasible_timeslots') or c.get('possible_times')
    if not s:
        return None
    text = str(s).strip()
    if not text:
        return None
    parts = [p.strip() for p in text.replace(';', ',').split(',') if p.strip()]
    return parts or None

# ----------------- GA operators -----------------

def create_individual(dataset, use_heuristic=False):
    if use_heuristic:
        return heuristic_seed(dataset)
    else:
        assign = {}
        classes = dataset['classes']
        rooms = dataset['rooms']
        timeslots = dataset['timeslots']
        room_ids = [r['room_id'] for r in rooms]
        timeslot_ids = [t['slot_id'] for t in timeslots]
        for c in classes:
            # Thêm kiểm tra khóa tồn tại
            if c.get('possible_times'):
                ts = random.choice(c['possible_times'])
            else:
                # Nếu khóa không tồn tại hoặc danh sách rỗng, chọn ngẫu nhiên từ TẤT CẢ timeslot
                ts = random.choice(timeslot_ids)
            r = random.choice(room_ids)
            assign[c['class_id']] = (ts, r)
        return assign


def crossover(p1, p2):
    child = {}
    for key in p1:
        child[key] = p1[key] if random.random() < 0.5 else p2[key]
    return child

def mutate(individual, dataset, mutation_rate=0.05):
    # Đột biến chỉ xảy ra với xác suất nhỏ
    if random.random() < mutation_rate:
        classes = list(individual.keys())
        
        # 1. Chọn ngẫu nhiên một lớp (c) để đột biến
        class_to_mutate = random.choice(classes)
        
        # 2. Lấy danh sách timeslot và room (Đã sửa lỗi timeslot_id -> slot_id)
        timeslots = dataset['timeslots']
        rooms = dataset['rooms']
        timeslot_ids = [t['slot_id'] for t in timeslots] 
        room_ids = [r['room_id'] for r in rooms]

        # 3. Gán ngẫu nhiên lại timeslot và room
        new_ts = random.choice(timeslot_ids)
        new_r = random.choice(room_ids)
        
        individual[class_to_mutate] = (new_ts, new_r)
        
    return individual

def _repair(ind, dataset, max_iters=200):
    """
    Greedy repair: nếu trùng GV/phòng-ca, dời lớp sang slot/room hợp lệ gần nhất,
    ưu tiên slot sớm.
    """
    classes = { c['class_id']: c for c in dataset['classes'] }
    slot_ids = _all_slot_ids(dataset)
    teacher_of = { cid: classes[cid]['teacher_id'] for cid in classes }

    # map start time để ưu tiên
    start_map = {}
    for t in dataset['timeslots']:
        sid = _slot_id_of(t)
        start_map[sid] = t.get('start')

    for _ in range(max_iters):
        changed = False
        used_room_ts = {}
        used_teacher_ts = {}
        conflicts = []

        # detect conflicts
        for cid, (ts, rid) in ind.items():
            used_room_ts.setdefault((ts, rid), []).append(cid)
            used_teacher_ts.setdefault((teacher_of[cid], ts), []).append(cid)

        for (ts, rid), lst in used_room_ts.items():
            if len(lst) > 1:
                conflicts.append(('room', ts, rid, lst))
        for (tch, ts), lst in used_teacher_ts.items():
            if len(lst) > 1:
                conflicts.append(('teacher', ts, None, lst))

        if not conflicts:
            break

        # resolve one conflict at a time
        kind, ts, rid, lst = conflicts[0]
        # giữ 1 lớp, dời các lớp còn lại
        for cid in lst[1:]:
            trial_slots = slot_ids[:]
            # ưu tiên slot sớm
            trial_slots.sort(key=lambda s: {'07:00':0,'09:00':1,'11:00':2}.get(start_map.get(s,''), 9))
            moved = False
            for new_ts in trial_slots:
                new_r = _pick_room_for(classes[cid], dataset)
                # room-ca phải trống
                if any( (new_ts==ind[oc][0] and new_r==ind[oc][1]) for oc in ind if oc!=cid ):
                    continue
                # giáo viên không trùng ca
                if any( (teacher_of[oc]==teacher_of[cid] and ind[oc][0]==new_ts) for oc in ind if oc!=cid ):
                    continue
                ind[cid] = (new_ts, new_r)
                changed = True
                moved = True
                break
            if not moved:
                # nếu không dời được slot, thử đổi room trước
                new_r = _pick_room_for(classes[cid], dataset)
                ind[cid] = (ts, new_r)
                changed = True

        if not changed:
            break

    return ind

# ----------------- GA main loop -----------------

import random # Đảm bảo random được import
# Giả định các hàm fitness, create_individual, _repair, crossover, mutate đã được định nghĩa ở nơi khác

def run_ga(dataset, pop_size=20, generations=50, use_heuristic=False, history_list=None):
    
    population = [create_individual(dataset, use_heuristic) for _ in range(pop_size)]
    population = [_repair(ind, dataset) for ind in population]

    best_ind, best_fit, best_meta = None, float('-inf'), None
    log = []

    for gen in range(generations):
        scored = []
        for ind in population:
            # Giả định các hàm fitness được định nghĩa
            f, meta = fitness(ind, dataset) 
            scored.append((f, ind, meta))
        scored.sort(key=lambda x: x[0], reverse=True)

        current_best_fit = scored[0][0] 

        if current_best_fit > best_fit:
            best_fit, best_ind, best_meta = scored[0]

        # GHI LỊCH SỬ FITNESS
        if history_list is not None:
            history_list.append(current_best_fit) 
            
        log.append({"generation": gen, "best_fitness": current_best_fit}) 
        print(f"Gen {gen+1}: Best fitness = {current_best_fit:.2f}")

        if current_best_fit == 0:
            break 
        
        # CHỌN BỐ MẸ VÀ KHỞI TẠO THẾ HỆ MỚI
        parents = [ind for _, ind, _ in scored[:max(2, pop_size//2)]]
        next_gen = parents[:]

        # LẶP LẠI (CHỈ MỘT LẦN) CHO ĐẾN KHI next_gen ĐỦ KÍCH THƯỚC
        while len(next_gen) < pop_size:
            p1, p2 = random.sample(parents, 2)
            child = crossover(p1, p2)
            
            # Đột biến và Repair cơ bản
            child = mutate(child, dataset)
            child = _repair(child, dataset)
            next_gen.append(child)
            
            # ĐỘT BIẾN TĂNG CƯỜNG (20% xác suất)
            # Áp dụng thêm đột biến và repair cho 20% cá thể mới
            if random.random() < 0.2:
                next_gen[-1] = mutate(next_gen[-1], dataset) 
                next_gen[-1] = _repair(next_gen[-1], dataset)

        population = next_gen
        
    return {
        "best_individual": best_ind,
        "best_fitness": best_fit,
        "best_meta": best_meta,
        "log": log,
    }