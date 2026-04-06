"""
graph.py
Handles the live population vs generation graph in a separate process.
"""

import multiprocessing as mp
import queue
import matplotlib.pyplot as plt
import matplotlib.animation as animation

def run_graph(q: mp.Queue) -> None:
    fig, ax = plt.subplots()
    fig.canvas.manager.set_window_title("Conway's Game of Life - Live Graph")
    ax.set_title("Population vs Generation")
    ax.set_xlabel("Generation")
    ax.set_ylabel("Population")
    
    line, = ax.plot([], [], lw=2, color='green')
    
    gens = []
    pops = []
    
    def update(frame):
        updated = False
        # Drain the queue to get the latest data
        while True:
            try:
                gen, pop = q.get_nowait()
                if not gens or gens[-1] != gen:
                    gens.append(gen)
                    pops.append(pop)
                    updated = True
            except queue.Empty:
                break
        
        if updated and gens:
            line.set_data(gens, pops)
            # Dynamically auto-scale the axes
            ax.set_xlim(max(0, min(gens)), max(gens) + max(10, int(len(gens)*0.1)))
            ax.set_ylim(0, max(pops) + max(10, int(max(pops)*0.1)))
            
        return line,

    # Update the graph every 100 milliseconds
    ani = animation.FuncAnimation(fig, update, interval=100, cache_frame_data=False)
    plt.show()