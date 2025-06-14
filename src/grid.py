class Grid:
    def __init__(self, memoria):
        self.memoria = memoria
        self.width, self.height = 40, 20  # Largura e altura do grid

    def get_snapshot(self):
        """
        Retorna uma cópia do grid, de forma que quem lê não altera o estado original.
        """
        return [list(row) for row in self.memoria.grid]

    def set_cell(self, pos, valor):
        """
        Marca a célula em `pos` com o valor fornecido (exemplo: '#' para barreiras).
        """
        x, y = pos
        self.memoria.grid[y][x] = valor

    def clear_cell(self, pos):
        """
        Limpa a célula em `pos`, marcando como espaço vazio `' '`.
        """
        x, y = pos
        self.memoria.grid[y][x] = ' '

    def place_robot(self, id_robo):
        """
        Coloca o robô no primeiro espaço vazio do grid e retorna a posição (x, y).
        """
        for y in range(self.height):
            for x in range(self.width):
                if self.memoria.grid[y][x] == ' ':
                    self.memoria.grid[y][x] = id_robo
                    return (x, y)
        return None  # Se não houver espaço

    def place_barreiras(self, posicoes):
        """
        Coloca barreiras (`#`) nas posições fornecidas.
        """
        for pos in posicoes:
            self.set_cell(pos, '#')

    def place_baterias(self, posicoes):
        """
        Coloca baterias (`⚡`) nas posições fornecidas.
        """
        for pos in posicoes:
            self.set_cell(pos, '⚡')

