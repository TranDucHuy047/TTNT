# src/fitness.py

from typing import Dict, Tuple

DEFAULT_WEIGHTS = {
    "HARD": 1000,     # phạt ràng buộc cứng
    "OVERFLOW": 10.0, # phạt vượt sức chứa
    "SOFT_LATE": 1.0  # phạt ca muộn
}

def _slot_id_of(row: Dict) -> str:
    # hỗ trợ cả 'slot_id' và 'timeslot_id'
    return row.get("slot_id") or row.get("timeslot_id")

def compute_fitness(individual: Dict[str, Tuple[str, str]], dataset: Dict, *args, **kwargs):
    """
    individual: { class_id: (slot_id, room_id), ... }
    dataset: {
      'classes': [{class_id, teacher_id, size, room_type?/room_type_required?}, ...],
      'rooms':   [{room_id, capacity, room_type}, ...],
      'timeslots': [{slot_id/timeslot_id, start}, ...]
    }
    return: (score_to_maximize, meta_dict)
    """

    classes   = dataset["classes"]
    rooms     = dataset["rooms"]
    timeslots = dataset["timeslots"]

    # ===== build lookup maps =====
    room_cap   = {r["room_id"]: int(r["capacity"]) for r in rooms}
    room_rtype = {r["room_id"]: r["room_type"]     for r in rooms}
    class_info = {
        c["class_id"]: {
            "teacher": c.get("teacher_id"),
            "size":    int(c.get("size", 0)),
            "rtype":   (c.get("room_type") or c.get("room_type_required"))
        }
        for c in classes
    }
    slot_start = {_slot_id_of(t): t.get("start") for t in timeslots}

    # ===== scoring =====
    hard_conflicts = 0
    overflow = 0.0
    soft_late = 0

    used_room_ts = set()     # (slot, room)
    used_teacher_ts = set()  # (teacher, slot)

    for cid, (ts, rid) in individual.items():
        info    = class_info[cid]
        teacher = info["teacher"]
        size    = info["size"]
        req     = info["rtype"]

        # trùng phòng-ca
        if (ts, rid) in used_room_ts:
            hard_conflicts += 1
        else:
            used_room_ts.add((ts, rid))

        # gv trùng ca
        if (teacher, ts) in used_teacher_ts:
            hard_conflicts += 1
        else:
            used_teacher_ts.add((teacher, ts))

        # sai loại phòng
        if room_rtype.get(rid) != req:
            hard_conflicts += 1

        # vượt sức chứa
        if size > room_cap.get(rid, 0):
            overflow += (size - room_cap.get(rid, 0))

        # soft: ca muộn
        if slot_start.get(ts) in ("13:00", "15:00"):
            soft_late += 1

    penalty = (
        DEFAULT_WEIGHTS["HARD"]     * hard_conflicts +
        DEFAULT_WEIGHTS["OVERFLOW"] * overflow +
        DEFAULT_WEIGHTS["SOFT_LATE"]* soft_late
    )

    # GA đang maximize => score = -penalty
    score = -penalty

    meta = {
        "hard_conflicts": hard_conflicts,
        "overflow": overflow,
        "soft_late": soft_late,
        "penalty": penalty
    }
    return score, meta
