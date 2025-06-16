import os
import threading
import time
import random
import logging
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
        self.sense_act_thread = threading.Thread(target=self.sense_act, daemon=True)
        self.housekeeping_thread = threading.Thread(target=self.housekeeping, daemon=True)

    def start(self):
        """Inicia as threads do robô."""
        with self.locks['grid_mutex']:
            self.pos = self.grid.place_robot(self.id)
        if self.pos is None:
            self.logger.error(f"Não foi possível posicionar o robô {self.id}. Encerrando.")
            self.running.clear()
            return

        with self.locks['robots_mutex']: # Garante que a info do robô seja inicializada atomicamente
            self.robots_info[self.id] = {'F': self.F, 'E': self.E, 'V': self.V, 'pos': self.pos, 'status': self.status}
        self.logger.info(f"Robo {self.id} posicionado em {self.pos}")

        try:
            self.sense_act_thread.start()
        except RuntimeError:
            pass
        try:
            self.housekeeping_thread.start()
        except RuntimeError:
            pass

    def stop(self):
        """Para as threads do robô."""
        self.running.clear()
        if self.sense_act_thread.is_alive():
            self.sense_act_thread.join()
        if self.housekeeping_thread.is_alive():
            self.housekeeping_thread.join()

    def _get_possible_moves(self, current_pos, grid_snapshot):
        """Retorna uma lista de movimentos válidos (adjacentes e não bloqueados)."""
        x, y = current_pos
        possible_moves = []
        directions = [(0, -1), (0, 1), (-1, 0), (1, 0)] # N, S, O, L
        
        for dx, dy in directions:
            new_x, new_y = x + dx, y + dy
            if 0 <= new_x < self.grid.width and 0 <= new_y < self.grid.height:
                cell_content = grid_snapshot[new_y][new_x]
                # Um robô pode se mover para uma célula vazia ou para uma bateria.
                # Ele não pode se mover para uma barreira ('#') ou para outra célula com robô (duelos são adjacentes).
                if cell_content == ' ' or cell_content == '⚡':
                    possible_moves.append((new_x, new_y))
        return possible_moves

    def sense_act(self):
        """
        Thread principal do robô: sensoria e decide a próxima ação.
        Prioriza: Bateria > Inimigo > Exploração (via BFS).
        """
        while self.running.is_set() and self.status == 'vivo':
            time.sleep(self.V * 0.2) # Atraso baseado na velocidade

            # 1. Tirar snapshot local do grid (sem lock, conforme especificado para sense_act)
            snapshot = self.grid.get_snapshot()

            target_pos = None
            
            # Prioridade 1: Procurar bateria
            baterias_disponiveis = []
            for y in range(self.grid.height):
                for x in range(self.grid.width):
                    if snapshot[y][x] == '⚡':
                        baterias_disponiveis.append((x, y))
            
            # Se houver baterias, tentar encontrar o caminho para a mais próxima
            if baterias_disponiveis:
                # Ordena as baterias pela distância Manhattan (aproximação rápida)
                baterias_disponiveis.sort(key=lambda p: abs(self.pos[0] - p[0]) + abs(self.pos[1] - p[1]))
                
                for bat_pos in baterias_disponiveis:
                    path = find_path(snapshot, self.pos, bat_pos, ['#']) # Ignora robôs como obstáculos para encontrar caminho para bateria
                    if path:
                        target_pos = path[0] # Pega o primeiro passo do caminho
                        self.logger.info(f"Robo {self.id} encontrou caminho para bateria em {bat_pos}, próximo passo: {target_pos}")
                        break # Encontrou um caminho para uma bateria, segue para lá

            # Prioridade 2: Mover-se aleatoriamente se não houver bateria ou caminho
            if target_pos is None:
                possible_moves = self._get_possible_moves(self.pos, snapshot)
                if possible_moves:
                    target_pos = random.choice(possible_moves)
                    self.logger.info(f"Robo {self.id} movendo-se aleatoriamente para {target_pos}")
                else:
                    self.logger.warning(f"Robo {self.id} sem movimentos possíveis. Aguardando...")
                    time.sleep(0.5)
                    continue

            # 2. Adquirir locks necessários na ordem documentada: grid_mutex > robots_mutex > battery_mutex_k
            # Assumimos que o lock da bateria é adquirido APENAS no momento da coleta.
            
            # Verificação prévia da célula alvo SEM lock, para decidir qual lock adquirir
            cell_content = snapshot[target_pos[1]][target_pos[0]]
            
            # Executar ação: Mover ou Coletar bateria
            try:
                # Ordem de locks: grid_mutex sempre primeiro para movimentação/interação com células
                with self.locks['grid_mutex']:
                    if cell_content == ' ': # Célula vazia, apenas move
                        old_pos = self.pos
                        self.grid.clear_cell(old_pos)
                        self.grid.set_cell(target_pos, self.id)
                        
                        with self.locks['robots_mutex']: # Protege atualização de dados do robô
                            self.pos = target_pos
                            self.robots_info[self.id]['pos'] = self.pos
                            self.E -= 1 # Consome energia ao mover
                            self.robots_info[self.id]['E'] = self.E
                        self.logger.info(f"Robo {self.id} moveu de {old_pos} para {self.pos}. Energia: {self.E}")
                        
                    elif cell_content == '⚡': # Célula com bateria, coleta
                        battery_lock = self.locks['battery_mutexes'].get(target_pos)
                        if battery_lock:
                            with battery_lock: # Adquire lock da bateria
                                # Re-check da célula após adquirir o lock, para evitar corrida na bateria
                                if self.grid.get_snapshot()[target_pos[1]][target_pos[0]] == '⚡':
                                    self.grid.clear_cell(target_pos) # Remove a bateria do grid
                                    with self.locks['robots_mutex']:
                                        self.E = min(100, self.E + 20) # Coleta bateria +20E (máx 100)
                                        self.robots_info[self.id]['E'] = self.E
                                    self.logger.info(f"Robo {self.id} coletou bateria em {target_pos}. Energia: {self.E}")
                                    # Robô permanece na mesma posição após coletar bateria
                                else:
                                    self.logger.info(f"Bateria em {target_pos} já foi coletada por outro robô.")
                        else:
                            self.logger.warning(f"Lock para bateria em {target_pos} não encontrado.")
                    
                    elif cell_content != ' ' and cell_content != '⚡' and cell_content != '#': # Encontrou outro robô, tenta duelar
                        # Duelos são gerenciados por RoboJogador ou uma lógica mais complexa.
                        # Aqui, o robô 'comum' apenas evitará o robô e tentará outro caminho.
                        # A especificação diz "Quando dois robôs se encontram, eles mesmos resolvem o duelo".
                        # A lógica de duelo atômico será implementada em RoboJogador
                        self.logger.info(f"Robo {self.id} encontrou outro robô ({cell_content}) em {target_pos}. Evitando...")
                        pass # Não faz nada, a próxima iteração encontrará outro caminho ou duelará.
                        
            except Exception as e:
                self.logger.error(f"Erro na ação do robô {self.id}: {e}")

    def housekeeping(self):
        """
        Thread que cuida da energia do robô (diminui por segundo) e verifica se ele morreu.
        Também verifica condição de vitória.
        """
        while self.running.is_set() and self.status == 'vivo':
            time.sleep(1)
            with self.locks['robots_mutex']:
                self.E -= 1
                self.robots_info[self.id].update({'E': self.E})
            self.logger.info(f"Robo {self.id} energia restante: {self.E}")
            if self.E <= 0:
                with self.locks['grid_mutex']:
                    self.grid.clear_cell(self.pos)
                with self.locks['robots_mutex']:
                    self.status = 'morto'
                    self.robots_info[self.id].update({'status': 'morto'})
                self.logger.info(f"Robo {self.id} morreu por falta de energia.")
            
            # Checar condição de vitória (apenas 1 robô vivo)
            with self.locks['robots_mutex']:
                vivos = [r_id for r_id, r_info in self.robots_info.items() if r_info['status'] == 'vivo']
                if len(vivos) == 1 and self.robots_info['P']['status'] == 'morto': # Se sobrar só um e não for o jogador
                    self.locks['game_over'].set()
                    self.locks['winner_id'].value = vivos[0]
                    self.logger.info(f"Jogo encerrado! Vencedor: {vivos[0]}")
                elif len(vivos) == 1 and self.robots_info['P']['status'] == 'vivo': # Se sobrar só o jogador
                    self.locks['game_over'].set()
                    self.locks['winner_id'].value = 'P'
                    self.logger.info(f"Jogo encerrado! Vencedor: P (Você!)")
                elif len(vivos) == 0: # Empate: todos morreram
                    self.locks['game_over'].set()
                    self.locks['winner_id'].value = 'EMPATE'
                    self.logger.info(f"Jogo encerrado! EMPATE, todos os robôs morreram.")