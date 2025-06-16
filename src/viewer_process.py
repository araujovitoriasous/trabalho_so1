import time
import random
import multiprocessing
import threading
from grid import Grid
from robos import Robo
from memoria_compartilhada import MemoriaCompartilhada

# Função que imprime o grid
def renderiza_grid(memoria):
    ESC = "\033"
    limpar_tela = f"{ESC}[H{ESC}[J"

    while True:
        border = "+" + "-" * 40 + "+"
        with memoria.grid_mutex:
            snapshot = [list(row) for row in memoria.grid]

        print(limpar_tela, end="")
        print(border)
        for row in snapshot:
            print("|" + "".join(row) + "|")
        print(border)
        
        time.sleep(0.3)

def iniciar_robo(robo_id, memoria):
    grid = Grid(memoria)
    robo = Robo(
        robo_id,
        grid,
        memoria.robots_info,
        {
            'grid_mutex': memoria.grid_mutex,
            'robots_mutex': memoria.robots_mutex,
            'battery_mutexes': memoria.battery_mutexes
        }
    )
    robo.run()

def main_viewer():
    memoria = MemoriaCompartilhada()
    grid = Grid(memoria)

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
    memoria.inicializar_baterias(baterias)

    robo_ids = ['A', 'B', 'C', 'D']
    processos_robos = []

    for robo_id in robo_ids:
        p = multiprocessing.Process(target=iniciar_robo, args=(robo_id, memoria))
        p.start()
        processos_robos.append(p)

    viewer_thread = threading.Thread(target=renderiza_grid, args=(memoria,))
    viewer_thread.daemon = True
    viewer_thread.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nEncerrando robôs...")
        for p in processos_robos:
            p.terminate()
        for p in processos_robos:
            p.join()

if __name__ == "__main__":
    multiprocessing.set_start_method("spawn")
    main_viewer()
