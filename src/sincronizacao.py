from multiprocessing import Lock, Event

def inicializar_locks(memoria):
    """
    Inicializa todos os locks e eventos necessários para proteger e sinalizar a memória compartilhada.
    Retorna um dicionário com os locks/eventos.
    """
    locks = {}

    # Locks para o grid
    locks['grid_mutex'] = memoria.grid_mutex # Usa o lock da instância de memoria
    
    # Locks para os robôs
    locks['robots_mutex'] = memoria.robots_mutex # Usa o lock da instância de memoria

    # Locks para as baterias (um lock por bateria)
    locks['battery_mutexes'] = memoria.battery_mutexes # Usa os locks da instância de memoria

    # Evento de game over (referência ao objeto do Manager)
    locks['game_over'] = memoria.game_over_event # Referencia o Event do Manager
    locks['winner_id'] = memoria.flags # Referencia o dicionário de flags do Manager

    return locks