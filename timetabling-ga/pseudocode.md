
---

## 9️⃣ Parameter Notes

| Parameter | Ý nghĩa | Giá trị khuyến nghị |
|------------|----------|----------------------|
| `pop_size` | Kích thước quần thể | 40–80 |
| `generations` | Số thế hệ tối đa | 50–120 |
| `mutation_rate` | Xác suất đột biến | 0.1–0.2 |
| `HARD_WEIGHT` | Trọng số phạt vi phạm cứng | 1000 |
| `OVERFLOW_WEIGHT` | Phạt vượt sức chứa | 10–20 |
| `SOFT_WEIGHT` | Phạt ràng buộc mềm | 1–3 |

---

## 10️⃣ Output

- `solution.csv` — lịch tối ưu: (class_id, slot, room)
- `summary.json` — fitness & thống kê vi phạm
- `ga_log.csv` — tiến hóa qua từng thế hệ

---

### ✅ Tổng kết
Thuật toán GA được dùng để tìm lịch học tối ưu bằng cách:
1. Biểu diễn lịch học dưới dạng ánh xạ lớp → (ca, phòng).  
2. Đánh giá bằng hàm fitness dựa trên mức độ vi phạm ràng buộc.  
3. Lặp lại qua nhiều thế hệ với lai ghép, đột biến và sửa lỗi heuristic.  
4. Dừng khi không còn vi phạm hoặc đạt số thế hệ tối đa.

---
