import time
import random
import threading
from grid import Grid
from robos import Robo
from collections import defaultdict

# Mock para a futura memória compartilhada
class MemoriaMock:
    def __init__(self):
        self.grid = [[' ' for _ in range(40)] for _ in range(20)]

# Função que imprime o grid
def render_grid(grid: Grid):
    clear_screen = "\033c"
    border = "+" + "-" * grid.width + "+"

    while True:
        snapshot = grid.get_snapshot()

        print(clear_screen, end="")
        print(border)
        for row in snapshot:
            print("|" + "".join(row) + "|")
        print(border)
        
        time.sleep(0.3)

def main():
    memoria = MemoriaMock()
    grid = Grid(memoria)

    locks = {
        'grid_mutex': threading.Lock(),
        'robots_mutex': threading.Lock()
    }
    
    robots_info = defaultdict(dict)

    barreiras = [(x, 10) for x in range(10, 30)] + \
                [(5, y) for y in range(5, 15)] + \
                [(34, y) for y in range(5, 15)]
    
    grid.place_barreiras(barreiras)

    baterias = []
    while len(baterias) < 10:
        x, y = random.randint(0, grid.width - 1), random.randint(0, grid.height - 1)
        if memoria.grid[y][x] == ' ':
            baterias.append((x, y))
    grid.place_baterias(baterias)

    robos = [Robo(id, grid, robots_info, locks) for id in ['A', 'B', 'C', 'D']]

    for robo in robos:
        robo.start()

    viewer_thread = threading.Thread(target=render_grid, args=(grid,))
    viewer_thread.daemon = True
    viewer_thread.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nEncerrando robôs...")
        for robo in robos:
            robo.stop()

if __name__ == "__main__":
    main()
