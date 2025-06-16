from multiprocessing import Process, Barrier
from memoria_compartilhada import MemoriaCompartilhada
from grid import Grid
from sincronizacao import inicializar_locks
from viewer_process import render_grid
import time
import logging

def deadlock_robo(id_robo, grid_instance, memoria_instance, barrier, ordem):
    logger = logging.getLogger(f"robo_deadlock_{id_robo}")
    logger.setLevel(logging.INFO)
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
            with memoria_instance.battery_mutexes[battery_pos]:
                logger.info(f"{id_robo} obteve battery_mutex {battery_pos}")
                time.sleep(1)
                logger.info(f"{id_robo} tentando grid_mutex")
                with memoria_instance.grid_mutex:
                    logger.info(f"{id_robo} obteve grid_mutex")
        else:
            logger.info(f"{id_robo} tentando grid_mutex")
            with memoria_instance.grid_mutex:
                logger.info(f"{id_robo} obteve grid_mutex")
                time.sleep(1)
                battery_pos = (3, 3)
                logger.info(f"{id_robo} tentando battery_mutex {battery_pos}")
                with memoria_instance.battery_mutexes[battery_pos]:
                    logger.info(f"{id_robo} obteve battery_mutex {battery_pos}")
    except Exception as e:
        logger.error(f"{id_robo} erro: {e}")

def provocar_deadlock():
    memoria = MemoriaCompartilhada()
    grid = Grid(memoria)
    locks = inicializar_locks(memoria)
    
    bateria_pos_deadlock = [(3, 3)]
    with memoria.grid_mutex:
        grid.place_baterias(bateria_pos_deadlock)
    memoria.inicializar_baterias(bateria_pos_deadlock)

    barrier = Barrier(2) # Barreira para sincronizar os dois robôs do deadlock

    p_viewer = Process(target=render_grid, args=(grid, memoria))
    p_viewer.start()

    p1 = Process(target=deadlock_robo, args=('X', grid, memoria, locks, barrier, 'battery-first'))
    p2 = Process(target=deadlock_robo, args=('Y', grid, memoria, locks, barrier, 'grid-first'))

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