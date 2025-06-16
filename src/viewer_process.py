import time
import random
import threading
from grid import Grid # Importa a classe Grid
# from robos import Robo # Não necessário diretamente aqui
# from collections import defaultdict # Não necessário diretamente aqui
import sys

def render_grid(grid_instance, memoria_instance): # Alterado: recebe grid_instance e memoria_instance
    """
    Renderiza o grid em tempo real.
    Adquire grid_mutex para um snapshot consistente.
    """
    clear_screen = "\033[H\033[J" # Limpa a tela de forma mais robusta (para terminais compatíveis com ANSI)
    
    # Agora acessa width e height diretamente do objeto grid_instance
    border_width = grid_instance.width + 2 
    border = "+" + "-" * (grid_instance.width) + "+\n"

    while True:
        # Adquirir o grid_mutex antes de fazer a cópia (snapshot)
        with memoria_instance.grid_mutex: # Usa o mutex da memoria_instance
            snapshot = grid_instance.get_snapshot() # Usa get_snapshot() do grid_instance
        # O grid_mutex é liberado imediatamente ao sair do bloco 'with'

        # Imprime o grid
        sys.stdout.write(clear_screen)
        sys.stdout.write(border)
        for row_idx, row in enumerate(snapshot):
            display_row = ""
            for char_val in row:
                display_row += str(char_val)
            sys.stdout.write("|" + display_row + "|\n")
        sys.stdout.write(border)

        # Exibir informações dos robôs (ex: energia, status) se disponível na memória compartilhada
        try:
            with memoria_instance.robots_mutex: # Acessa robots_info com seu próprio mutex da memoria_instance
                info_line = "Robôs: "
                for r_id, r_info in memoria_instance.robots_info.items():
                    info_line += f"{r_id}(E:{r_info['E']}, S:{r_info['status']}) "
                sys.stdout.write(info_line + "\n")
        except Exception as e:
            sys.stdout.write(f"Erro ao ler info dos robôs: {e}\n")

        # Verifica condição de game_over se a flag estiver disponível na memória
        try:
            # Verifica se init_done está true e se o vencedor já foi definido
            if memoria_instance.flags.get('init_done') and memoria_instance.flags.get('vencedor') is not None:
                winner_id = memoria_instance.flags['vencedor']
                if winner_id == 'EMPATE':
                    sys.stdout.write("\n*** O JOGO TERMINOU! EMPATE! ***\n")
                else:
                    sys.stdout.write(f"\n*** O JOGO TERMINOU! VENCEDOR: {winner_id}! ***\n")
                sys.stdout.flush()
                time.sleep(5)
                break
        except KeyError:
            pass # As flags ainda não foram inicializadas ou não possuem a chave 'vencedor'

        sys.stdout.flush()
        time.sleep(0.05)

# Código para teste local do viewer (manter para depuração, remover em produção ou adaptar)
def main_viewer_test():
    from multiprocessing import Manager, Lock # Importa para o teste isolado do viewer
    
    class MockMemoriaCompleta:
        def __init__(self):
            self.manager = Manager()
            self.grid_proxy = self.manager.list([self.manager.list([' '] * 40) for _ in range(20)])
            self.robots_info = self.manager.dict()
            self.grid_mutex = Lock()
            self.robots_mutex = Lock()
            self.flags = self.manager.dict({'init_done': False, 'vencedor': None})
            
        # O get_snapshot para o mock precisa ser no próprio objeto que será passado para Grid
        def get_grid_proxy(self):
            return self.grid_proxy

    class MockGrid: # Novo mock para simular o Grid
        def __init__(self, memoria_mock_completa):
            self.memoria = memoria_mock_completa # Mantém a referência ao mock da memória
            self.width, self.height = 40, 20
        
        def get_snapshot(self):
            # No mock, o snapshot vem direto do grid_proxy da memoria_mock
            return [list(row) for row in self.memoria.get_grid_proxy()]

    mock_memoria_completa = MockMemoriaCompleta()
    mock_grid_instance = MockGrid(mock_memoria_completa)
    
    # Exemplo: popular o grid e robots_info para teste
    mock_memoria_completa.grid_proxy[5][5] = '#'
    mock_memoria_completa.grid_proxy[10][10] = '⚡'
    mock_memoria_completa.grid_proxy[2][2] = 'R1'
    mock_memoria_completa.robots_info['R1'] = {'E': 50, 'status': 'vivo', 'pos': (2,2), 'F': 5, 'V': 2}
    mock_memoria_completa.flags['init_done'] = True # Sinaliza que a inicialização está feita

    print("Iniciando teste do Viewer. Pressione Ctrl+C para encerrar.")
    try:
        render_grid(mock_grid_instance, mock_memoria_completa) # Passa ambos os mocks
    except KeyboardInterrupt:
        print("Teste do Viewer encerrado.")

if __name__ == "__main__":
    main_viewer_test()