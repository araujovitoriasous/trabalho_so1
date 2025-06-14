from multiprocessing import Manager, Lock, Barrier

class MemoriaCompartilhada:
    def __init__(self, qtd_robos=4):
        self.manager = Manager()

        # Cria a matriz 40x20 compartilhada
        self.grid = self.manager.list(
            [self.manager.list([' '] * 40) for _ in range(20)]
        )

        # Dicionário de robôs, compartilhado entre os processos
        self.robots_info = self.manager.dict()

        # Flags de controle do jogo (inicializado e vencedor)
        self.flags = self.manager.dict({'init_done': False, 'vencedor': None})

        # Mutexes para sincronização
        self.locks = {
            'grid_mutex': Lock(),  # Protege a manipulação do grid
            'robots_mutex': Lock(),  # Protege a manipulação dos robôs no dicionário
            'barrier': Barrier(qtd_robos),  # temos {qtd_robos} robôs
            **self.manager.dict()  # Dicionário para baterias, cada posição de bateria tem um lock
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
