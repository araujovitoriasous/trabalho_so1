import time

# Função que imprime o grid
def renderiza_grid(memoria):
    ESC = "\033"
    limpar_tela = f"{ESC}[H{ESC}[J"

    while True:
        border = "+" + "-" * 40 + "+"
        with memoria.grid_mutex:
            snapshot = [list(row) for row in memoria.grid]

        print(limpar_tela, end="")
        print(border)
        for row in snapshot:
            print("|" + "".join(row) + "|")
        print(border)
        
        time.sleep(0.3)