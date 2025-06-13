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
    while True:
        snapshot = grid.get_snapshot()
        print("\033c", end="")  # Limpa a tela (emulando clear no terminal)
        print("+" + "-" * grid.width + "+")
        for row in snapshot:
            print("|" + "".join(row) + "|")
        print("+" + "-" * grid.width + "+")
        time.sleep(0.3)

def main():
    # Inicializa memória local e grid
    memoria = MemoriaMock()
    grid = Grid(memoria)

    # Inicializa estruturas de controle
    locks = {
        'grid_mutex': threading.Lock(),
        'robots_mutex': threading.Lock()
    }
    robots_info = defaultdict(dict)

    # === Adiciona barreiras fixas no grid ===
    barreiras = []
    # horizontal no meio
    for x in range(10, 30):
        barreiras.append((x, 10))
    # vertical esquerda
    for y in range(5, 15):
        barreiras.append((5, y))
    # vertical direita
    for y in range(5, 15):
        barreiras.append((34, y))
    grid.place_barreiras(barreiras)

    # === Adiciona baterias aleatórias ===
    baterias = []
    while len(baterias) < 10:  # 10 baterias
        x = random.randint(0, grid.width - 1)
        y = random.randint(0, grid.height - 1)
        if memoria.grid[y][x] == ' ':  # Evita sobreposição com barreiras
            baterias.append((x, y))
    grid.place_baterias(baterias)

    # === Criação dos robôs ===
    robos = [
        Robo('A', grid, robots_info, locks),
        Robo('B', grid, robots_info, locks),
        Robo('C', grid, robots_info, locks),
        Robo('D', grid, robots_info, locks)
    ]

    # Inicia os robôs
    for robo in robos:
        robo.start()

    # Inicia o renderizador em uma thread separada
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
