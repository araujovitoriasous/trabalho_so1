from multiprocessing import Manager, Lock, Barrier

class MemoriaCompartilhada:
    def __init__(self,qtd_robos=4):
        self.manager = Manager()
        # Cria a matriz 40x20 compartilhada
        self.grid = self.manager.list([self.manager.list([' '] * 40) for _ in range(20)])
        
        # Dicionário de robôs, compartilhado entre os processos
        self.robots_info = self.manager.dict()
        
        # Flags de controle do jogo (inicializado e vencedor)
        self.flags = self.manager.dict({'init_done': False, 'vencedor': None})
        
        # Mutexes para sincronização
        self.grid_mutex = Lock()   # Protege a manipulação do grid
        self.robots_mutex = Lock() # Protege a manipulação dos robôs no dicionário
        
        # Dicionário para baterias, cada posição de bateria tem um lock
        self.battery_mutexes = {}

        # Barrier para sincronizar os robôs antes de cada ação
        self.barrier = Barrier(qtd_robos)  # temos {qtd_robos} robôs
        
        self.locks = {
            'grid_mutex': self.grid_mutex,
            'robots_mutex': self.robots_mutex,
            'barrier': self.barrier
            **self.battery_mutexes
        }

    def inicializar_baterias(self, posicoes_baterias):
        """
        Para cada posição de bateria fornecida, cria um lock específico em `battery_mutexes`.
        Isso impede que dois robôs tentem pegar a mesma bateria ao mesmo tempo.
        """
        self.battery_mutexes = self.manager.dict()
        for pos in posicoes_baterias:
            self.battery_mutexes[pos] = Lock()
        self.locks.update(self.battery_mutexes)
