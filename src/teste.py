from multiprocessing import Manager, Lock
from sincronizacao import inicializar_sincronizacao
from grid import Grid
from robos import Robo
import time

def testar_memoria_e_robo():
    # Inicializando a memória compartilhada e o grid
    posicoes_baterias=[(1, 1), (2, 2)]
    memoria = inicializar_sincronizacao(posicoes_baterias)
    grid = Grid(memoria)

    # Criando o robô
    locks = {
        'grid_mutex': memoria.grid_mutex,
        'robots_mutex': memoria.robots_mutex,
        'battery_mutexes': memoria.battery_mutexes
    }
    robo = Robo('A', grid, memoria.robots_info, locks)

    # Colocando o robô no grid
    with memoria.grid_mutex:
        pos = grid.place_robot(robo.id)

    '''# Colocando as baterias no grid
    with memoria.grid_mutex:
        grid.place_baterias(posicoes_baterias)'''

    # Registrando o robô no dicionário de robôs
    with memoria.robots_mutex:
        memoria.robots_info[robo.id] = {'F': robo.F, 'E': robo.E, 'V': robo.V, 'pos': pos, 'status': 'vivo'}

    # Verificando se o robô foi corretamente posicionado e registrado
    print(f"Posição do robô {robo.id}: {memoria.robots_info[robo.id]['pos']}")
    snapshot = grid.get_snapshot()

    # Mostra a posição do robô no grid
    print("Tabuleiro após o posicionamento do robô:")
    for row in snapshot:
        print(''.join(row))
    
    # Verifica se o robô foi realmente posicionado no grid
    x, y = memoria.robots_info[robo.id]['pos']
    print(f"Verificando posição no grid ({x},{y}): {snapshot[y][x]}")

    # Verifica se o robô foi posicionado corretamente
    if snapshot[y][x] == 'A':
        print("Teste passou: O robô foi posicionado corretamente no grid!")
    else:
        print("Teste falhou: O robô não foi posicionado corretamente no grid.")

if __name__ == "__main__":
    testar_memoria_e_robo()


