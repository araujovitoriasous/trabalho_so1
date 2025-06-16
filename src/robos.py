import threading
import time
import random
import logging
import os
from pathfinding import find_path

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
        
        # Setup do logger
        self.logger = logging.getLogger(f"robo_{self.id}")
        self.logger.setLevel(logging.INFO)
        os.makedirs("logs", exist_ok=True)
        fh = logging.FileHandler(f"logs/robo_{self.id}.log")
        fh.setFormatter(logging.Formatter("%(asctime)s - %(message)s"))
        self.logger.addHandler(fh)

        self.logger.info(f"Robo {self.id} criado com F={self.F}, E={self.E}, V={self.V}")

        # Evento para controle de execução das threads
        self.running = threading.Event()
        self.running.set()

        # Criação das threads
        self.sense_act_thread = threading.Thread(target=self.sense_act, name=f"sense_act_{self.id}")
        self.housekeeping_thread = threading.Thread(target=self.housekeeping, name=f"housekeeping_{self.id}")
    def calculate_new_pos(self, direction, steps):
        """Calcula a nova posição a partir da direção e o número de passos."""
        x, y = self.pos
        directions = {
            'N': lambda pos, steps: (pos[0], max(pos[1] - steps, 0)),
            'S': lambda pos, steps: (pos[0], min(pos[1] + steps, self.grid.height - 1)),
            'E': lambda pos, steps: (min(pos[0] + steps, self.grid.width - 1), pos[1]),
            'W': lambda pos, steps: (max(pos[0] - steps, 0), pos[1]),
        }
        return directions[direction]((x, y), steps)
    def start(self):
        """Inicia o robô, posicionando-o na grade e iniciando as threads de ação e manutenção."""
        self.pos = self.grid.place_robot(self.id)
        if self.pos is None:
            raise RuntimeError(f"Failed to place robot with id {self.id} on grid")
    
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
        except RuntimeError as e:
            self.logger.error(f"Failed to start sense_act_thread for Robo {self.id}: {e}")
        try:
            self.housekeeping_thread.start()
        except RuntimeError as e:
            self.logger.error(f"Failed to start housekeeping_thread for Robo {self.id}: {e}")

    def stop(self):
        """Encerra as threads do robô."""
        self.running.clear()

        if self.sense_act_thread.is_alive():
            self.sense_act_thread.join()
        if self.housekeeping_thread.is_alive():
            self.housekeeping_thread.join()

    def try_acquire_lock(self, lock_name):
        """Tenta adquirir um lock e registra a dependência"""
        if lock_name == "grid":
            with self.locks['grid_mutex']:
                pass  # Simplesmente adquire o lock
        elif lock_name == "battery":
            battery_lock = self.locks['battery_mutexes'].get(self.pos)
            if battery_lock:
                with battery_lock:
                    pass  # Simplesmente adquire o lock da bateria

    def sense_act(self):
        """Simulação de ações do robô"""
        while self.running.is_set() and self.status == 'vivo':
            time.sleep(self.V * 0.2)  # Atraso baseado na velocidade

            # 1. Tirar snapshot local do grid
            snapshot = self.grid.get_snapshot()

            target_pos = None
            baterias_disponiveis = []

            # Procurar bateria
            for y in range(self.grid.height):
                for x in range(self.grid.width):
                    if snapshot[y][x] == '⚡':  # Verifica se há uma bateria na célula
                        baterias_disponiveis.append((x, y))
            
            if baterias_disponiveis:
                baterias_disponiveis.sort(key=lambda p: abs(self.pos[0] - p[0]) + abs(self.pos[1] - p[1]))
                
                # Escolher a bateria mais próxima
                for bat_pos in baterias_disponiveis:
                    # Encontrar o caminho para a bateria
                    path = find_path(snapshot, self.pos, bat_pos, ['#'])
                    if path:
                        target_pos = path[0]
                        self.logger.info(f"Robo {self.id} encontrou caminho para bateria em {bat_pos}, próximo passo: {target_pos}")
                        break

            if target_pos is None:
                # Caso não tenha bateria disponível, move aleatoriamente
                possible_moves = self._get_possible_moves(self.pos, snapshot)
                if possible_moves:
                    target_pos = random.choice(possible_moves)
                    self.logger.info(f"Robo {self.id} movendo-se aleatoriamente para {target_pos}")
                else:
                    self.logger.warning(f"Robo {self.id} sem movimentos possíveis. Aguardando...")
                    time.sleep(0.5)
                    continue

            # Verificação prévia da célula alvo
            cell_content = snapshot[target_pos[1]][target_pos[0]]
            
            try:
                self.try_acquire_lock("grid")

                if cell_content == ' ':
                    # Movendo-se para uma célula vazia
                    old_pos = self.pos
                    self.grid.clear_cell(old_pos)
                    self.grid.set_cell(target_pos, self.id)

                    with self.locks['robots_mutex']:
                        self.pos = target_pos
                        self.robots_info[self.id]['pos'] = self.pos
                        self.E -= 1  # Energia diminui ao mover
                        self.robots_info[self.id]['E'] = self.E
                    self.logger.info(f"Robo {self.id} moveu de {old_pos} para {self.pos}. Energia: {self.E}")
                
                elif cell_content == '⚡':  # Verificando se a célula contém uma bateria
                    # Tentando adquirir o lock da bateria para evitar que outros robôs a peguem ao mesmo tempo
                    battery_lock = self.locks['battery_mutexes'].get(target_pos)
                    if battery_lock:
                        with battery_lock:  # Garantindo exclusividade na coleta da bateria
                            if self.grid.get_snapshot()[target_pos[1]][target_pos[0]] == '⚡':  # Verifica novamente a bateria
                                self.grid.clear_cell(target_pos)  # Remove a bateria do grid
                                with self.locks['robots_mutex']:
                                    # Atualiza a energia, limitada a 100
                                    self.E = min(100, self.E + 20)
                                    self.robots_info[self.id]['E'] = self.E
                                self.logger.info(f"Robo {self.id} coletou bateria em {target_pos}. Energia: {self.E}")
                            else:
                                self.logger.info(f"Bateria em {target_pos} já foi coletada por outro robô.")
                
                elif cell_content != ' ' and cell_content != '⚡' and cell_content != '#':
                    # Se houver outro robô em uma célula adjacente, inicia o duelo
                    self.logger.info(f"Robo {self.id} encontrou outro robô ({cell_content}) em {target_pos}. Iniciando duelo...")
                    self.duelo(cell_content, target_pos)
            except Exception as e:
                self.logger.error(f"Erro na ação do robô {self.id}: {e}")

    def duelo(self, inimigo_id, target_pos):
        """
        Lógica de duelo entre dois robôs.
        O robô com maior força (F) vence o duelo.
        """
        inimigo = self.robots_info.get(inimigo_id)
        if inimigo:
            self.logger.info(f"Duelo iniciado entre {self.id} e {inimigo_id}!")
            if self.F > inimigo['F']:
                self.robots_info[self.id]['E'] += 10  # Vencedor ganha energia
                self.grid.clear_cell(target_pos)  # Limpa a célula do adversário
                self.logger.info(f"{self.id} venceu o duelo contra {inimigo_id}!")
            elif self.F < inimigo['F']:
                self.robots_info[self.id]['E'] -= 10  # Perdedor perde energia
                self.logger.info(f"{inimigo_id} venceu o duelo contra {self.id}!")
            else:
                self.logger.info(f"O duelo entre {self.id} e {inimigo_id} terminou em empate!")
        else:
            self.logger.warning(f"Inimigo {inimigo_id} não encontrado!")

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
