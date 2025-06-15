from multiprocessing import Lock

def inicializar_locks(memoria):
    """
    Inicializa todos os locks necessários para proteger a memória compartilhada.
    Retorna um dicionário com os locks.
    """
    locks = {}

    # Locks para o grid
    locks['grid_mutex'] = Lock()

    # Locks para os robôs
    locks['robots_mutex'] = Lock()

    # Locks para as baterias (um lock por bateria)
    locks['battery_mutexes'] = {}

    # Retorna todos os locks
    return locks
