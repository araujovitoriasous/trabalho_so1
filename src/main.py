from multiprocessing import Process
from memoria_compartilhada import MemoriaCompartilhada
from grid import Grid
from sincronizacao import inicializar_locks
from viewer_process import render_grid 
from robo_jogador import RoboJogador
from robos import Robo
import time

def main():
    # Inicializa a memória compartilhada e o grid
    memoria = MemoriaCompartilhada()
    grid = Grid(memoria)
    locks = inicializar_locks(memoria)

    # Inicializa grid
    barreiras = [(5, 5), (10, 10), (15, 15)]
    baterias = [(3, 3), (8, 8), (18, 2)]
    with memoria.grid_mutex:
        grid.place_barreiras(barreiras)
        grid.place_baterias(baterias)
    memoria.inicializar_baterias(baterias)

    # Processos
    processos = []

    # Inicia o processo de renderização do grid
    p_viewer = Process(target=render_grid, args=(memoria,))
    p_viewer.start()
    processos.append(p_viewer)

    # Cria o RoboJogador e inicia a thread sense_act
    jogador = RoboJogador('P', grid, memoria.robots_info, locks)
    p_jogador = Process(target=jogador.start)  # Usa o método start() para começar o controle do robô
    p_jogador.start()
    processos.append(p_jogador)

    # Robôs automáticos (exemplo)
    for rid in ['A', 'B']:
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
    main()
