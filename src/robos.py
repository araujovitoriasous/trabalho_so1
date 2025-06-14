import os
import threading
import time
import random
import logging

class Robo:
    def __init__(self, id_robo, grid, robots_info, locks):
        self.id = id_robo
        self.grid = grid
        self.robots_info = robots_info
        self.locks = locks

        # Atributos do robô
        self.F = random.randint(1, 10)  # Força do robô
        self.E = random.randint(10, 100)  # Energia do robô
        self.V = random.randint(1, 5)  # Velocidade do robô
        self.status = 'vivo'  # Status do robô
        self.pos = None  # Posição inicial do robô
        
        #Setup do logger
        os.makedirs("logs", exist_ok=True)
        self.logger = logging.getLogger(f"robo_{self.id}")
        if not self.logger.handlers:
            fh = logging.FileHandler(f"logs/robo_{self.id}.log")
            fh.setFormatter(logging.Formatter("%(asctime)s - %(message)s"))
            self.logger.addHandler(fh)
        self.logger.setLevel(logging.INFO)
        self.logger.info(f"Robo {self.id} criado com F={self.F}, E={self.E}, V={self.V}")

        # Evento para controle de execução das threads
        self.running = threading.Event()
        self.running.set()

        # Criação das threads
        self.sense_act_thread = threading.Thread(target=self.sense_act, name=f"sense_act_{self.id}")
        self.housekeeping_thread = threading.Thread(target=self.housekeeping, name=f"housekeeping_{self.id}")

    def start(self):
        """
        Inicia o robô, posicionando-o na grade e iniciando as threads de ação e manutenção.
        """
        # Posiciona o robô na grade
        self.pos = self.grid.place_robot(self.id)
        if self.pos is None:
            raise RuntimeError(f"Failed to place robot with id {self.id} on grid")
    
        # Armazena as informações do robô
        robot_data = {
            'F': self.F,
            'E': self.E,
            'V': self.V,
            'pos': self.pos,
            'status': self.status
        }
        
        with self.locks['robots_mutex']:
            self.robots_info[self.id] = robot_data
    
        # Inicia as threads do robô
        try:
            self.sense_act_thread.start()
        except RuntimeError:
            pass
        try:
            self.housekeeping_thread.start()
        except RuntimeError:
            pass

    def stop(self):
        # Encerra as threads do robô
        self.running.clear()

        # Aguarda o término das threads
        if self.sense_act_thread.is_alive():
            self.sense_act_thread.join()
        if self.housekeeping_thread.is_alive():
            self.housekeeping_thread.join()

    def calculate_new_pos(self, direction, steps):
        """
        Calcula a nova posição a partir da direção e o número de passos.
        """
        x, y = self.pos
        directions = {
            'N': lambda pos, steps: (pos[0], max(pos[1] - steps, 0)),
            'S': lambda pos, steps: (pos[0], min(pos[1] + steps, self.grid.height - 1)),
            'E': lambda pos, steps: (min(pos[0] + steps, self.grid.width - 1), pos[1]),
            'W': lambda pos, steps: (max(pos[0] - steps, 0), pos[1]),
        }
        return directions[direction]((x, y), steps)

    def sense_act(self):
        """
        Thread principal de ação do robô: movimenta-se aleatoriamente enquanto estiver vivo.
        Lógica de ação do robô (mover, coletar bateria, duelando, etc).
        """
        while self.running.is_set() and self.status == 'vivo':
            direction = random.choice(['N', 'S', 'E', 'W'])  # Movimenta aleatoriamente
            steps = random.randint(1, self.V)  # Número de passos
            target = self.calculate_new_pos(direction, steps)  # Calcula nova posição
            with self.locks['grid_mutex']:
                snapshot = self.grid.get_snapshot()
                free = snapshot[target[1]][target[0]] == ' '
            if free:
                old = self.pos
                with self.locks['robots_mutex']:
                    with self.locks['grid_mutex']:
                        self.grid.clear_cell(old)
                        self.grid.set_cell(target, self.id)
                    self.pos = target
                    self.robots_info[self.id]['pos'] = self.pos
                self.logger.info(f'Robo {self.id} moveu de {old} para {self.pos}')
            time.sleep(0.5)  # Intervalo entre as ações

    def housekeeping(self):
        """
        Thread que cuida da energia do robô (diminui por segundo) e verifica se ele morreu.
        """
        while self.running.is_set() and self.status == 'vivo':
            time.sleep(1)
            with self.locks['robots_mutex']:
                self.E -= 1
                self.robots_info[self.id].update({'E': self.E})
            self.logger.info(f'Robo {self.id} energia restante: {self.E}')
            if self.E <= 0:
                with self.locks['grid_mutex']:
                    self.grid.clear_cell(self.pos)
                with self.locks['robots_mutex']:
                    self.status = 'morto'
                    self.robots_info[self.id].update({'status': 'morto'})
                self.logger.info(f'Robo {self.id} morreu por falta de energia')
                self.running.clear()

