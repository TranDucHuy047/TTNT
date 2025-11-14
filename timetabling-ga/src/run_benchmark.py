from .data_loader import load_dataset
from .genetic_utils import run_ga
from .export_excel import export_schedule
from .plot_results import plot_fitness

GENERATIONS = 50 
POP_SIZE = 50   

if __name__ == "__main__":
    dataset = load_dataset("data/base")

    history_ga = []
    history_heuristic = []

    print("=== GA thuần ===")
    result1 = run_ga(dataset, 
                     pop_size=POP_SIZE, 
                     generations=GENERATIONS, 
                     use_heuristic=False, 
                     history_list=history_ga) 
    
    export_schedule(result1['best_individual'], path="output/schedule_ga_thuan.xlsx") 

    print("\n=== GA + Heuristic (MRV+Degree) ===")
    result2 = run_ga(dataset, 
                     pop_size=POP_SIZE, 
                     generations=GENERATIONS, 
                     use_heuristic=True, 
                     history_list=history_heuristic)
    
    export_schedule(result2['best_individual'], path="output/schedule_ga_heuristic.xlsx") 

    plot_fitness(history_ga, history_heuristic)

    print("\nKết quả so sánh:")
    print("GA thuần:", result1['best_fitness'])
    print("GA+Heuristic:", result2['best_fitness'])