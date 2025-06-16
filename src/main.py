from multiprocessing import Process
from memoria_compartilhada import MemoriaCompartilhada
from grid import Grid
from sincronizacao import inicializar_locks
from viewer_process import renderiza_grid
from robo_jogador import RoboJogador
from robos import Robo
import time
import random
from main_deadlock import main_deadlock

def main():
    # Inicializa a memória compartilhada e o grid
    memoria = MemoriaCompartilhada()
    grid = Grid(memoria)
    locks = inicializar_locks(memoria)

    # Inicializa grid
    barreiras = [(x, 10) for x in range(10, 30)] + \
                [(5, y) for y in range(5, 15)] + \
                [(34, y) for y in range(5, 15)]

    baterias = []
    while len(baterias) < 10:
        x, y = random.randint(0, grid.width - 1), random.randint(0, grid.height - 1)
        if memoria.grid[y][x] == ' ':
            baterias.append((x, y))
    grid.place_barreiras(barreiras)
    grid.place_baterias(baterias)
    memoria.inicializar_baterias(baterias)

    # Processos
    processos = []

    # Inicia o processo de renderização do grid
    '''
    p_viewer = Process(target=renderiza_grid, args=(memoria,))
    p_viewer.start()
    processos.append(p_viewer)'''
    # Removido para evitar conflito visual com curses (modo normal)


    # Cria o RoboJogador e inicia a thread sense_act
    jogador = RoboJogador('P', grid, memoria.robots_info, locks)
    p_jogador = Process(target=jogador.start)  # Usa o método start() para começar o controle do robô
    p_jogador.start()
    processos.append(p_jogador)

    # Robôs automáticos (exemplo)
    for rid in ['A', 'B', 'C']:
        robo = Robo(rid, grid, memoria.robots_info, locks)
        p = Process(target=robo.start)
        p.start()
        processos.append(p)

    try:
        while p_jogador.is_alive():
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        for p in processos:
            p.terminate()
        print("Jogo encerrado.")


if __name__ == "__main__":
    modo = int(input("1 - Modo normal | 2 - Modo deadlock: "))
    if modo == 1:
        main()
    elif modo == 2:
        main_deadlock()
    else:
        print("Opção inválida.")
