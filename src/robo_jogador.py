import curses
from robos import Robo
import time
import logging

class RoboJogador(Robo):
    def __init__(self, id_robo, grid, robots_info, locks):
        super().__init__(id_robo, grid, robots_info, locks)
        self.logger = logging.getLogger(f"robo_{self.id}") # Reusa o logger do Robo
        if not self.logger.handlers: # Garante que o handler seja adicionado apenas uma vez
            fh = logging.FileHandler(f"logs/robo_{self.id}.log")
            fh.setFormatter(logging.Formatter("%(asctime)s - %(message)s"))
            self.logger.addHandler(fh)
        self.logger.setLevel(logging.INFO)

    def start(self):
        """
        Função de inicialização do RoboJogador com controle via curses.
        """
        # Posiciona o robô antes de iniciar a interface curses
        self.pos = self.grid.place_robot(self.id)
        if self.pos is None:
            self.logger.error(f"Não foi possível posicionar o robô {self.id}. Encerrando.")
            self.running.clear()
            return

        with self.locks['robots_mutex']:
            self.robots_info[self.id] = {'F': self.F, 'E': self.E, 'V': self.V, 'pos': self.pos, 'status': self.status}
        self.logger.info(f"Robo Jogador {self.id} posicionado em {self.pos}")

        self.housekeeping_thread.start() # Inicia a thread de housekeeping

        # Inicia a interface Curses
        curses.wrapper(self.sense_act)

    def sense_act(self, stdscr):
        """
        Lógica de controle do robô pelo usuário usando a biblioteca curses.
        """
        curses.curs_set(0)  # Esconde o cursor
        stdscr.nodelay(1)   # Faz o terminal não bloquear na leitura
        stdscr.timeout(100) # Tempo de espera para captura de tecla (100ms)

        teclas = {'w': 'N', 'a': 'W', 's': 'S', 'd': 'E'}

        while self.running.is_set() and self.status == 'vivo':
            key = stdscr.getch() # Captura a tecla pressionada

            # Verifica se o jogo acabou
            if self.locks['game_over'].is_set():
                winner_id = self.locks['winner_id'].value
                stdscr.clear()
                if winner_id == 'EMPATE':
                    stdscr.addstr(0, 0, "O JOGO TERMINOU! EMPATE!")
                else:
                    stdscr.addstr(0, 0, f"O JOGO TERMINOU! VENCEDOR: {winner_id}!")
                stdscr.refresh()
                time.sleep(5) # Dá tempo para o usuário ver a mensagem
                break # Sai do loop de jogo

            snapshot = self.grid.get_snapshot()

            # Mostra as informações do robô
            stdscr.clear()  # Limpa a tela antes de desenhar novamente
            stdscr.addstr(0, 0, f"Seu Robo [{self.id}] em {self.pos} com E={self.E}, F={self.F}, V={self.V}")
            stdscr.addstr(1, 0, "Use WASD para mover. Pressione 'q' para sair.")

            # Processa a entrada do usuário
            if key != -1: # Se uma tecla foi pressionada
                char_key = chr(key).lower()
                if char_key == 'q':
                    self.running.clear() # Sinaliza para parar as threads
                    self.logger.info("Robo Jogador encerrado pelo usuário.")
                    break
                
                direction = teclas.get(char_key)
                if direction:
                    target = self._calculate_target_pos(self.pos, direction)
                    if target:
                        # 1. Adquirir locks necessários na ordem documentada: grid_mutex > robots_mutex > battery_mutex_k
                        # Assume-se que 'k' para battery_mutex_k é a posição da bateria.

                        # Antes de adquirir locks, verifica o conteúdo da célula alvo
                        cell_content = snapshot[target[1]][target[0]]

                        if cell_content == ' ': # Célula vazia, apenas move
                            with self.locks['grid_mutex']:
                                old_pos = self.pos
                                self.grid.clear_cell(old_pos)
                                self.grid.set_cell(target, self.id)
                                
                                with self.locks['robots_mutex']:
                                    self.pos = target
                                    self.robots_info[self.id]['pos'] = self.pos
                                    self.E -= 1 # Consome energia ao mover
                                    self.robots_info[self.id]['E'] = self.E
                                self.logger.info(f"Robo {self.id} moveu de {old_pos} para {self.pos}. Energia: {self.E}")
                                
                        elif cell_content == '⚡': # Célula com bateria, tenta coletar
                            battery_lock = self.locks['battery_mutexes'].get(target)
                            if battery_lock:
                                with self.locks['grid_mutex']: # grid_mutex para acessar e modificar o grid
                                    with battery_lock: # battery_mutex_k para a bateria específica
                                        # Re-check da célula após adquirir o lock, para evitar corrida na bateria
                                        if self.grid.get_snapshot()[target[1]][target[0]] == '⚡':
                                            self.grid.clear_cell(target) # Remove a bateria do grid
                                            with self.locks['robots_mutex']:
                                                self.E = min(100, self.E + 20) # Coleta bateria +20E (máx 100)
                                                self.robots_info[self.id]['E'] = self.E
                                            self.logger.info(f"Robo {self.id} coletou bateria em {target}. Energia: {self.E}")
                                            # Robô permanece na mesma posição após coletar bateria
                                        else:
                                            self.logger.info(f"Bateria em {target} já foi coletada por outro robô.")
                                    # Libera battery_lock
                                # Libera grid_mutex
                            else:
                                self.logger.warning(f"Lock para bateria em {target} não encontrado.")
                                stdscr.addstr(20, 0, f"Erro: Bateria sem lock em {target}.\\n")

                        elif cell_content != ' ' and cell_content != '⚡' and cell_content != '#': # Encontrou outro robô, duela
                            self.duelo(cell_content, target, stdscr) # Passa stdscr para exibir mensagens
                        else:
                            stdscr.addstr(20, 0, "Movimento inválido ou obstáculo.\\n")
                
            time.sleep(0.05) # Pequena pausa para responsividade do curses e loop do jogo

    def duelo(self, inimigo_id, target_pos, stdscr):
        """
        Lógica de duelo atômico entre dois robôs.
        O robô com maior Poder (2F + E) vence; perdedor marca status = morto e libera célula.
        Empate => ambos destruídos.
        A negociação do duelo deve ocorrer dentro de grid_mutex.
        """
        
        # Garante atomicidade do duelo adquirindo grid_mutex e robots_mutex
        with self.locks['grid_mutex']:
            with self.locks['robots_mutex']:
                # Re-verifica se o inimigo ainda está na posição e vivo
                current_cell_content = self.grid.get_snapshot()[target_pos[1]][target_pos[0]]
                if current_cell_content != inimigo_id:
                    self.logger.info(f"Robô {self.id} tentou duelar com {inimigo_id} em {target_pos}, mas ele não está mais lá.")
                    stdscr.addstr(20, 0, f"Inimigo {inimigo_id} não está mais em {target_pos}.\n")
                    stdscr.refresh()
                    return

                inimigo_data = self.robots_info.get(inimigo_id)
                if not inimigo_data or inimigo_data['status'] == 'morto':
                    self.logger.info(f"Robô {self.id} tentou duelar com {inimigo_id}, mas ele já está morto.")
                    stdscr.addstr(20, 0, f"Inimigo {inimigo_id} já está morto.\n")
                    stdscr.refresh()
                    return

                self.logger.info(f"Duelo iniciado: {self.id} (F={self.F}, E={self.E}) vs {inimigo_id} (F={inimigo_data['F']}, E={inimigo_data['E']})")
                stdscr.addstr(20, 0, f"Duelo iniciado entre {self.id} e {inimigo_id}!\n")
                stdscr.refresh()
                
                poder_atacante = (2 * self.F) + self.E
                poder_inimigo = (2 * inimigo_data['F']) + inimigo_data['E']

                self.logger.info(f"Poder {self.id}: {poder_atacante} | Poder {inimigo_id}: {poder_inimigo}")

                if poder_atacante > poder_inimigo:
                    # Atacante vence
                    self.logger.info(f"{self.id} venceu o duelo contra {inimigo_id}!")
                    stdscr.addstr(20, 0, f"{self.id} venceu o duelo contra {inimigo_id}!\n")
                    stdscr.refresh()
                    # Marcar inimigo como morto e liberar célula
                    self._marcar_morto(inimigo_id, target_pos)
                    
                    # Move o robô atacante para a posição do inimigo
                    old_pos = self.pos
                    self.grid.clear_cell(old_pos)
                    self.grid.set_cell(target_pos, self.id)
                    self.pos = target_pos
                    self.robots_info[self.id]['pos'] = self.pos
                    self.E -= 1 # Consome energia ao mover
                    self.robots_info[self.id]['E'] = self.E


                elif poder_inimigo > poder_atacante:
                    # Inimigo vence
                    self.logger.info(f"{inimigo_id} venceu o duelo contra {self.id}!")
                    stdscr.addstr(20, 0, f"{inimigo_id} venceu o duelo contra {self.id}!\n")
                    stdscr.refresh()
                    # Marcar atacante como morto e liberar sua célula
                    self._marcar_morto(self.id, self.pos)
                    stdscr.addstr(20, 0, f"Você morreu em combate! Fim de jogo.\n")
                    stdscr.refresh()
                    self.running.clear() # Sinaliza para parar as threads do jogador
                    self.status = 'morto' # Atualiza o status local para sair do loop

                else:
                    # Empate - ambos morrem
                    self.logger.info(f"Duelo entre {self.id} e {inimigo_id} resultou em empate. Ambos morrem!")
                    stdscr.addstr(20, 0, f"Empate! Ambos robôs foram destruídos!\n")
                    stdscr.refresh()
                    self._marcar_morto(self.id, self.pos)
                    self._marcar_morto(inimigo_id, target_pos)
                    stdscr.addstr(20, 0, f"Você morreu em combate! Fim de jogo.\n")
                    stdscr.refresh()
                    self.running.clear() # Sinaliza para parar as threads do jogador
                    self.status = 'morto' # Atualiza o status local para sair do loop

    def _marcar_morto(self, robot_id, pos):
        """Marca um robô como morto e libera sua posição no grid."""
        if robot_id not in self.robots_info:
            return
        self.grid.clear_cell(pos)
        self.robots_info[robot_id]['status'] = 'morto'
        self.logger.info(f"Robô {robot_id} marcado como morto.")

    def _calculate_target_pos(self, current_pos, direction):
        """Calcula a próxima posição com base na direção."""
        x, y = current_pos
        if direction == 'N': return (x, y - 1)
        if direction == 'S': return (x, y + 1)
        if direction == 'W': return (x - 1, y)
        if direction == 'E': return (x + 1, y)
        return None
