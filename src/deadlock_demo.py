# deadlock_demo.py (MODIFICADO)
from multiprocessing import Process, Barrier
from memoria_compartilhada import MemoriaCompartilhada
from grid import Grid
from sincronizacao import inicializar_locks
from viewer_process import render_grid # Importa a função render_grid
import time
import logging

def deadlock_robo(id_robo, grid_instance, memoria_instance, locks, barrier, ordem): # Alterado: recebe grid_instance e memoria_instance
    logger = logging.getLogger(f"robo_deadlock_{id_robo}")
    logger.setLevel(logging.INFO)
    import os
    os.makedirs("logs", exist_ok=True)
    fh = logging.FileHandler(f"logs/robo_deadlock_{id_robo}.log")
    fh.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
    logger.addHandler(fh)
    
    pos = (2, 3) if id_robo == 'X' else (4, 3)
    
    # Adquire o lock do grid para posicionar o robô no grid
    with memoria_instance.grid_mutex: # Usa o mutex da memoria_instance
        grid_instance.set_cell(pos, id_robo) # Usa set_cell do grid_instance

    logger.info(f"{id_robo} posicionado em {pos}")
    logger.info(f"{id_robo} aguardando na barreira...")
    barrier.wait()
    
    try:
        if ordem == 'battery-first':
            battery_pos = (3, 3)
            logger.info(f"{id_robo} tentando battery_mutex {battery_pos}")
            # Adquire o lock da bateria primeiro
            with memoria_instance.battery_mutexes[battery_pos]: # Usa o mutex da memoria_instance
                logger.info(f"{id_robo} obteve battery_mutex {battery_pos}")
                time.sleep(1) # Simula algum trabalho
                logger.info(f"{id_robo} tentando grid_mutex")
                # Tenta adquirir o lock do grid em seguida
                with memoria_instance.grid_mutex: # Usa o mutex da memoria_instance
                    logger.info(f"{id_robo} obteve grid_mutex")
        else: # ordem == 'grid-first'
            logger.info(f"{id_robo} tentando grid_mutex")
            # Adquire o lock do grid primeiro
            with memoria_instance.grid_mutex: # Usa o mutex da memoria_instance
                logger.info(f"{id_robo} obteve grid_mutex")
                time.sleep(1) # Simula algum trabalho
                battery_pos = (3, 3)
                logger.info(f"{id_robo} tentando battery_mutex {battery_pos}")
                # Tenta adquirir o lock da bateria em seguida
                with memoria_instance.battery_mutexes[battery_pos]: # Usa o mutex da memoria_instance
                    logger.info(f"{id_robo} obteve battery_mutex {battery_pos}")
    except Exception as e:
        logger.error(f"{id_robo} erro: {e}")

def provocar_deadlock():
    # Inicializa a memória compartilhada e o grid
    memoria = MemoriaCompartilhada()
    grid = Grid(memoria)
    locks = inicializar_locks(memoria)
    
    # Posiciona uma bateria para o cenário de deadlock
    bateria_pos_deadlock = [(3, 3)]
    with memoria.grid_mutex:
        grid.place_baterias(bateria_pos_deadlock)
    memoria.inicializar_baterias(bateria_pos_deadlock) # Inicializa os locks das baterias

    barrier = Barrier(2) # Barreira para sincronizar os dois robôs do deadlock

    # Inicia o processo de renderização do grid, passando o objeto 'grid' e 'memoria' real
    p_viewer = Process(target=render_grid, args=(grid, memoria)) # Corrigido: Passa grid e memoria
    p_viewer.start()

    # Cria os dois processos de robôs que irão provocar o deadlock
    p1 = Process(target=deadlock_robo, args=('X', grid, memoria, locks, barrier, 'battery-first')) # Passa grid e memoria
    p2 = Process(target=deadlock_robo, args=('Y', grid, memoria, locks, barrier, 'grid-first')) # Passa grid e memoria

    p1.start()
    p2.start()

    try:
        p1.join(10)
        p2.join(10)
        print("[INFO] If the processes are still alive after 10 s, the deadlock was reached.")
    except KeyboardInterrupt:
        print("\\n[INFO] Simulação de deadlock encerrada.")
    finally:
        p_viewer.terminate()
        p_viewer.join()
        print("[INFO] Processos encerrados.")