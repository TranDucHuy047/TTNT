import matplotlib.pyplot as plt
import os # Cần import os để tạo thư mục nếu chưa tồn tại

def plot_fitness(history_ga, history_heuristic):
    # Đảm bảo thư mục output tồn tại
    output_dir = "output"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    plt.figure()
    plt.plot(history_ga, label="GA thuần")
    plt.plot(history_heuristic, label="GA + heuristic", linestyle="--")
    plt.xlabel("Thế hệ (generation)")
    plt.ylabel("Fitness")
    plt.title("So sánh tiến hóa GA vs GA+Heuristic")
    plt.legend()
    plt.savefig(os.path.join(output_dir, "chart_comparison.png"))
    print("✅ Saved chart_comparison.png")