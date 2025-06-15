from multiprocessing import Process, Barrier
from memoria_compartilhada import MemoriaCompartilhada
from grid import Grid
from sincronizacao import inicializar_locks
from viewer_process import render_grid
import time
import logging

def deadlock_robo(id_robo, grid, memoria, locks, barrier, ordem):
    logger = logging.getLogger(f"robo_deadlock_{id_robo}")
    logger.setLevel(logging.INFO)
    fh = logging.FileHandler(f"logs/robo_deadlock_{id_robo}.log")
    fh.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
    logger.addHandler(fh)
    
    pos = (2, 3) if id_robo == 'X' else (4, 3)
    grid.set_cell(pos, id_robo)

    logger.info(f"{id_robo} posicionado em {pos}")
    logger.info(f"{id_robo} aguardando na barreira...")
    barrier.wait()
    
    try:
        if ordem == 'battery-first':
            battery_pos = (3, 3)
            logger.info(f"{id_robo} tentando battery_mutex {battery_pos}")
            with memoria.battery_mutexes[battery_pos]:
                logger.info(f"{id_robo} obteve battery_mutex {battery_pos}")
                time.sleep(1)
                logger.info(f"{id_robo} tentando grid_mutex")
                with memoria.grid_mutex:
                    logger.info(f"{id_robo} obteve grid_mutex")
        else:
            logger.info(f"{id_robo} tentando grid_mutex")
            with memoria.grid_mutex:
                logger.info(f"{id_robo} obteve grid_mutex")
                time.sleep(1)
                battery_pos = (3, 3)
                logger.info(f"{id_robo} tentando battery_mutex {battery_pos}")
                with memoria.battery_mutexes[battery_pos]:
                    logger.info(f"{id_robo} obteve battery_mutex {battery_pos}")
    except Exception as e:
        logger.error(f"{id_robo} erro: {e}")

def provocar_deadlock():
    memoria = MemoriaCompartilhada()
    grid = Grid(memoria)
    locks = inicializar_locks(memoria)
    
    bateria = [(3, 3)]
    with memoria.grid_mutex:
        grid.place_baterias(bateria)
    memoria.inicializar_baterias(bateria)
    
    barrier = Barrier(2)

    # Adapta o Grid para o formato esperado por render_grid, simulando memoria.grid.width
    class MemoriaFake:
        def __init__(self, grid):
            self.grid = grid

    p_viewer = Process(target=render_grid, args=(MemoriaFake(grid),))


    #p_viewer = Process(target=render_grid, args=(grid,))
    p_viewer.start()

    p1 = Process(target=deadlock_robo, args=('X', grid, memoria, locks, barrier, 'battery-first'))
    p2 = Process(target=deadlock_robo, args=('Y', grid, memoria, locks, barrier, 'grid-first'))

    p1.start()
    p2.start()

    p1.join()
    p2.join()
    p_viewer.terminate()
