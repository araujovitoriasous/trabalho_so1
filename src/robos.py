import os
import threading
import time
import random
import logging
#teste permissions
class Robo:
    def __init__(self, id_robo, grid, robots_info, locks):
        self.id = id_robo
        self.grid = grid
        self.robots_info = robots_info
        self.locks = locks

        self.F = random.randint(1, 10)  # Força do robô
        self.E = random.randint(10, 100)  # Energia do robô
        self.V = random.randint(1, 5)  # Velocidade do robô
        self.status = 'vivo'  # Status do robô
        self.pos = None  # Posição inicial do robô

        # 🧱 Garante que o diretório de logs exista
        os.makedirs("logs", exist_ok=True)

        # Configuração de logs
        logging.basicConfig(
            filename=f'logs/robo_{self.id}.log',
            level=logging.INFO,
            format='%(asctime)s - %(message)s'
        )
        logging.info(f'Robo {self.id} criado com F={self.F}, E={self.E}, V={self.V}')

        # Evento para controle da execução das threads
        self.running = threading.Event()
        self.running.set()

        # Threads do robô
        self.sense_act_thread = threading.Thread(target=self.sense_act, name=f"sense_act_{self.id}")
        self.housekeeping_thread = threading.Thread(target=self.housekeeping, name=f"housekeeping_{self.id}")

        # Configuração de logs
        logging.basicConfig(filename=f'logs/robo_{self.id}.log', level=logging.INFO,
                            format='%(asctime)s - %(message)s')
        logging.info(f'Robo {self.id} criado com F={self.F}, E={self.E}, V={self.V}')

    def start(self):
        # Coloca o robô no grid
        with self.locks['grid_mutex']:
            self.pos = self.grid.place_robot(self.id)

        # Registra o robô no dicionário de robôs
        with self.locks['robots_mutex']:
            self.robots_info[self.id] = {'F': self.F, 'E': self.E, 'V': self.V, 'pos': self.pos, 'status': self.status}

        # Inicia as threads do robô
        self.sense_act_thread.start()
        self.housekeeping_thread.start()

    def stop(self):
        # Encerra as threads do robô
        self.running.clear()
        self.sense_act_thread.join()
        self.housekeeping_thread.join()

    def calculate_new_pos(self, direction, steps):
        """
        Calcula a nova posição a partir da direção e o número de passos.
        """
        x, y = self.pos
        if direction == 'N':  # Norte
            y = max(y - steps, 0)
        elif direction == 'S':  # Sul
            y = min(y + steps, self.grid.height - 1)
        elif direction == 'E':  # Leste
            x = min(x + steps, self.grid.width - 1)
        elif direction == 'W':  # Oeste
            x = max(x - steps, 0)
        return (x, y)

    def sense_act(self):
        """
        Lógica de ação do robô (mover, coletar bateria, duelando, etc).
        """
        while self.running.is_set() and self.status == 'vivo':
            snapshot = self.grid.get_snapshot()
            direction = random.choice(['N', 'S', 'E', 'W'])  # Movimenta aleatoriamente
            steps = random.randint(1, self.V)  # Número de passos
            target = self.calculate_new_pos(direction, steps)  # Calcula nova posição

            # Verifica se a célula está livre, se for, move o robô
            if snapshot[target[1]][target[0]] == ' ':
                with self.locks['grid_mutex']:
                    self.grid.clear_cell(self.pos)
                    self.grid.set_cell(target, self.id)
                    old = self.pos
                    self.pos = target

                with self.locks['robots_mutex']:
                    self.robots_info[self.id]['pos'] = self.pos

                logging.info(f'Robo {self.id} moveu de {old} para {self.pos}')

            time.sleep(0.5)  # Intervalo entre as ações

    def housekeeping(self):
        """
        Thread que cuida da energia do robô (diminui por segundo) e verifica se ele morreu.
        """
        while self.running.is_set() and self.status == 'vivo':
            time.sleep(1)
            with self.locks['robots_mutex']:
                self.E -= 1
                self.robots_info[self.id]['E'] = self.E
                logging.info(f'Robo {self.id} energia restante: {self.E}')
                if self.E <= 0:
                    self.status = 'morto'
                    self.robots_info[self.id]['status'] = 'morto'
                    with self.locks['grid_mutex']:
                        self.grid.clear_cell(self.pos)
                    logging.info(f'Robo {self.id} morreu por falta de energia')
                    self.running.clear()

