# main.py (MODIFICADO)
from multiprocessing import Process
from memoria_compartilhada import MemoriaCompartilhada
from grid import Grid
from sincronizacao import inicializar_locks
from viewer_process import render_grid 
from robo_jogador import RoboJogador
from robos import Robo
import time
from main_deadlock import main_deadlock # Mantém a importação para a demonstração separada

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
    memoria.flags['init_done'] = True # Sinaliza que o grid e baterias foram inicializados

    # Processos
    processos = []

    # Inicia o processo de renderização do grid
    # Passa a instância de Grid e a instância de MemoriaCompartilhada
    p_viewer = Process(target=render_grid, args=(grid, memoria)) 
    p_viewer.start()
    processos.append(p_viewer)

    # Cria o RoboJogador e inicia a thread sense_act
    jogador = RoboJogador('P', grid, memoria.robots_info, locks)
    p_jogador = Process(target=jogador.start)
    p_jogador.start()
    processos.append(p_jogador)

    # Robôs automáticos (exemplo)
    # Garante que sempre haverá 3 robôs "normais" + 1 jogador
    for i in range(1, 4): # IDs 'R1', 'R2', 'R3'
        rid = f'R{i}'
        robo = Robo(rid, grid, memoria.robots_info, locks)
        p = Process(target=robo.start)
        p.start()
        processos.append(p)

    try:
        # Loop principal para manter o main process ativo, ou pode usar join em todos os processos
        while not memoria.game_over_event.is_set():
            time.sleep(0.5)
            # Pode adicionar aqui uma lógica para encerrar se todos os robôs morrerem
            # ou se uma condição de vitória for atingida

        # Se o game_over_event for setado, encerra todos os processos
        print("\\n[INFO] Jogo encerrado. Aguardando processos terminarem...")
        for p in processos:
            if p.is_alive():
                p.terminate() # Termina processos que ainda estão rodando
                p.join() # Espera eles terminarem
        print("[INFO] Todos os processos do jogo encerrados.")

    except KeyboardInterrupt:
        print("\\n[INFO] Jogo encerrado pelo usuário. Finalizando processos...")
    finally:
        for p in processos:
            if p.is_alive():
                p.terminate()
                p.join()
        print("[INFO] Todos os processos encerrados.")

if __name__ == "__main__":
    # Para rodar a simulação normal
    main()
    
    # Para rodar a simulação de deadlock
    # main_deadlock()