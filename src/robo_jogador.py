# robo_jogador.py

import curses
from robos import Robo
import time

class RoboJogador(Robo):
    def start(self):
        """
        Função de inicialização do RoboJogador com controle via curses.
        """
        curses.wrapper(self.sense_act)  # Usa o wrapper do curses para iniciar a interação com o usuário

    def sense_act(self, stdscr):
        """
        Lógica de controle do robô pelo usuário usando a biblioteca curses.
        """
        curses.curs_set(0)  # Esconde o cursor
        stdscr.nodelay(1)   # Faz o terminal não bloquear na leitura
        stdscr.timeout(100) # Tempo de espera para captura de tecla (100ms)

        teclas = {'w': 'N', 'a': 'W', 's': 'S', 'd': 'E'}

        # Inicializa posição
        self.pos = self.grid.place_robot(self.id)
        self.robots_info[self.id] = {'F': self.F, 'E': self.E, 'V': self.V, 'pos': self.pos, 'status': self.status}

        while self.running.is_set() and self.status == 'vivo':
            snapshot = self.grid.get_snapshot()

            # Mostra as informações do robô
            stdscr.clear()  # Limpa a tela antes de desenhar novamente
            stdscr.addstr(0, 0, f"Seu Robo [{self.id}] em {self.pos} com E={self.E}")
            stdscr.addstr(1, 0, "Mover (W/A/S/D), Q sair: ")
            stdscr.refresh()

            # Exibe o grid no terminal
            for y, row in enumerate(snapshot):
                stdscr.addstr(2 + y, 0, ''.join(row))  # Usando addstr no lugar de print
            stdscr.refresh()

            tecla = stdscr.getch()

            if tecla == ord('q'):
                stdscr.addstr(20, 0, "Saindo do modo jogador.\n")
                self.running.clear()
                break

            if tecla in [ord('w'), ord('a'), ord('s'), ord('d')]:
                cmd = chr(tecla)
                direcao = teclas[cmd]
                target = self.calculate_new_pos(direcao, 1)
                cell = snapshot[target[1]][target[0]]

                if cell == ' ':
                    self.grid.clear_cell(self.pos)
                    self.grid.set_cell(target, self.id)
                    old = self.pos
                    self.pos = target
                    self.robots_info[self.id]['pos'] = self.pos
                    stdscr.addstr(20, 0, f"Você moveu de {old} para {self.pos}.\n")
                elif cell == '⚡':
                    self.grid.clear_cell(self.pos)
                    self.grid.clear_cell(target)
                    self.pos = target
                    self.grid.set_cell(target, self.id)
                    self.E = min(self.E + 20, 100)
                    self.robots_info[self.id]['E'] = self.E
                    stdscr.addstr(20, 0, f"Você coletou bateria em {self.pos}. Energia = {self.E}.\n")
                elif isinstance(cell, str) and cell not in ['#']:
                    stdscr.addstr(20, 0, f"Duelando contra {cell} em {target}...\n")
                    self.duelo(cell, target)
                else:
                    stdscr.addstr(20, 0, "Movimento inválido ou obstáculo.\n")
            
            time.sleep(0.1)  # Pequena pausa entre as iterações

    def duelo(self, inimigo_id, target):
        """
        Lógica de duelo entre dois robôs.
        O robô com maior força (F) vence o duelo.
        """
        # Recupera as informações do robô inimigo
        inimigo = self.robots_info.get(inimigo_id)
        if inimigo:
            self.stdscr.addstr(20, 0, f"Duelo iniciado entre {self.id} e {inimigo_id}!\n")
            if self.F > inimigo['F']:
                self.stdscr.addstr(20, 0, f"{self.id} venceu o duelo contra {inimigo_id}!\n")
                self.robots_info[self.id]['E'] += 10  # Recupera um pouco de energia ao vencer
                self.grid.clear_cell(target)
            elif self.F < inimigo['F']:
                self.stdscr.addstr(20, 0, f"{inimigo_id} venceu o duelo contra {self.id}!\n")
                self.robots_info[self.id]['E'] -= 10  # Perde energia ao perder
            else:
                self.stdscr.addstr(20, 0, f"O duelo entre {self.id} e {inimigo_id} terminou em empate!\n")
        else:
            self.stdscr.addstr(20, 0, f"Inimigo {inimigo_id} não encontrado!\n")
