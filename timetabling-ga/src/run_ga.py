import os
import json
import csv
from pathlib import Path
import pandas as pd

from src.data_loader import load_dataset
from src.genetic_utils import run_ga  # dùng GA hiện có (trả dict)

# ---------- helpers xuất báo cáo ----------

def _export_solution(individual, out_csv: Path):
    """
    individual có thể là:
      - dict[class_id] -> (timeslot_id/slot_id, room_id), hoặc
      - list Gene(class_id, slot_id, room_id)
    """
    rows = []
    if isinstance(individual, dict):
        for cid, val in individual.items():
            ts, rid = val[0], val[1]
            rows.append({"class_id": cid, "slot_id": ts, "room_id": rid})
    else:
        # fallback: list Gene-like objects
        for g in individual or []:
            rows.append({
                "class_id": getattr(g, "class_id"),
                "slot_id": getattr(g, "slot_id"),
                "room_id": getattr(g, "room_id"),
            })
    if rows:
        pd.DataFrame(rows).to_csv(out_csv, index=False)

def _export_log(log_list, out_csv: Path):
    """log_list: list[{generation, best_fitness, ...}]"""
    if not log_list:
        return
    pd.DataFrame(log_list).to_csv(out_csv, index=False)

def _analyze_placeholder(best_individual, dataset):
    """
    Nếu bạn có analyzer thật, thay thế chỗ gọi hàm này.
    Tạm thời trả 0 cho các loại vi phạm chi tiết.
    """
    hard = {"feasible": 0, "room_type": 0, "capacity": 0, "teacher_overlap": 0, "room_overlap": 0}
    soft = {"late_slot": 0}
    return hard, soft

# ---------- chạy 1 case ----------

def run_one_case(case_folder: Path, out_folder: Path, pop_size=40, generations=50):
    out_folder.mkdir(parents=True, exist_ok=True)

    # nạp dataset từ folder case/base
    dataset = load_dataset(str(case_folder))

    # chạy GA
    result = run_ga(dataset, pop_size=pop_size, generations=generations)

    best = result.get("best_individual")
    best_fitness = float(result.get("best_fitness", 0.0))
    best_meta = result.get("best_meta") or {}
    log = result.get("log", [])

    # in màn hình cho tiện theo dõi
    print("✅ Best fitness:", best_fitness)
    if best_meta:
        print("ℹ️  Details:", best_meta)

    # xuất file
    _export_solution(best, out_folder / "solution.csv")
    _export_log(log, out_folder / "ga_log.csv")

    # số generation thực sự chạy
    gens = generations
    if log:
        try:
            gens = max(int(x.get("generation", 0)) for x in log) + 1
        except Exception:
            pass

    # Nếu chưa có analyzer chi tiết, map nhanh từ best_meta cho khớp Details
    hard_v, soft_v = _analyze_placeholder(best, dataset)
    # gắn những gì GA đã đếm được
    hard_v["teacher_overlap"] = int(best_meta.get("hard_conflicts", 0))
    soft_v["late_slot"] = int(best_meta.get("soft_late", 0))
    overflow_val = float(best_meta.get("overflow", 0.0))

    summary = {
        "suite": case_folder.name,
        "best_fitness": best_fitness,
        "hard_violations": hard_v,
        "soft_violations": soft_v,
        "overflow": overflow_val,
        "generations": gens,
    }

    (out_folder / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return summary

# ---------- tiện ích quét case ----------

def _collect_cases(root: Path):
    """
    Nếu root có classes.csv -> 1 case
    Ngược lại: lấy tất cả subfolders có classes.csv
    """
    if (root / "classes.csv").exists():
        return [root]
    return [p for p in root.iterdir() if p.is_dir() and (p / "classes.csv").exists()]

# ---------- entry point ----------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--suite", default=str(Path("data/base")),
                        help="Folder dataset (1 case) hoặc thư mục chứa nhiều case")
    parser.add_argument("--out",   default=str(Path("output/runs")),
                        help="Thư mục output gốc")
    parser.add_argument("--pop",   type=int, default=40)
    parser.add_argument("--gen",   type=int, default=50)
    args = parser.parse_args()

    # Đảm bảo dùng đường dẫn tuyệt đối
    BASE = Path(__file__).resolve().parents[1]
    SUITE = (BASE / args.suite).resolve()
    OUT   = (BASE / args.out).resolve()
    OUT.mkdir(parents=True, exist_ok=True)

    cases = _collect_cases(SUITE)
    summaries = []

    for c in cases:
        case_out = OUT / c.name
        s = run_one_case(c, case_out, pop_size=args.pop, generations=args.gen)
        print(json.dumps(s, ensure_ascii=False, indent=2))
        summaries.append(s)

    # Nếu chạy nhiều case: tổng hợp summary_all.csv
    if len(summaries) > 1:
        sum_csv = OUT / "summary_all.csv"
        fields = [
            "suite","best_fitness","generations",
            "feasible","room_type","capacity","teacher_overlap","room_overlap",
            "late_slot","overflow"
        ]
        with open(sum_csv, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            for s in summaries:
                h = s.get("hard_violations", {})
                soft = s.get("soft_violations", {})
                w.writerow({
                    "suite": s.get("suite"),
                    "best_fitness": s.get("best_fitness"),
                    "generations": s.get("generations"),
                    "feasible": h.get("feasible", 0),
                    "room_type": h.get("room_type", 0),
                    "capacity": h.get("capacity", 0),
                    "teacher_overlap": h.get("teacher_overlap", 0),
                    "room_overlap": h.get("room_overlap", 0),
                    "late_slot": soft.get("late_slot", 0),
                    "overflow": s.get("overflow", 0.0),
                })
        print(f"✅ Summary saved: {sum_csv}")
