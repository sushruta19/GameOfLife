"""
graph.py (p2life variant)
Handles the live population vs generation graph for two players in a separate process.
"""

import multiprocessing as mp
import queue
import matplotlib.pyplot as plt
import matplotlib.animation as animation

def run_graph(q: mp.Queue) -> None:
    fig, ax = plt.subplots()
    fig.canvas.manager.set_window_title("P2Life Toroidal - Live Graph")
    ax.set_title("Population vs Generation")
    ax.set_xlabel("Generation")
    ax.set_ylabel("Population")
    
    line_p1, = ax.plot([], [], lw=2, color='green', label='Green (P1)', alpha=0.6)
    line_p2, = ax.plot([], [], lw=2, color='red', label='Red (P2)', alpha=0.6)
    ax.legend()
    
    gens = []
    pops_p1 = []
    pops_p2 = []
    
    def update(frame):
        updated = False
        # Drain the queue to get the latest data
        while True:
            try:
                gen, p1_pop, p2_pop = q.get_nowait()
                if not gens or gens[-1] != gen:
                    gens.append(gen)
                    pops_p1.append(p1_pop)
                    pops_p2.append(p2_pop)
                    updated = True
            except queue.Empty:
                break
        
        if updated and gens:
            line_p1.set_data(gens, pops_p1)
            line_p2.set_data(gens, pops_p2)
            # Dynamically auto-scale the axes
            max_pop = max(max(pops_p1), max(pops_p2))
            ax.set_xlim(max(0, min(gens)), max(gens) + max(10, int(len(gens)*0.1)))
            ax.set_ylim(0, max_pop + max(10, int(max_pop*0.1)))
            
        return line_p1, line_p2

    ani = animation.FuncAnimation(fig, update, interval=100, cache_frame_data=False)
    plt.show()