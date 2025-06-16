from collections import deque

def find_path(grid_snapshot, start_pos, target_pos, obstacles):
    """
    Encontra o caminho mais curto usando o algoritmo BFS.

    Args:
        grid_snapshot (list of lists): Uma cópia local do grid.
        start_pos (tuple): Posição inicial (x, y) do robô.
        target_pos (tuple): Posição alvo (x, y).
        obstacles (list): Lista de caracteres que representam obstáculos (ex: '#').

    Returns:
        list or None: Uma lista de tuplas representando o caminho do start_pos
                      ao target_pos (excluindo start_pos), ou None se não houver caminho.
    """
    rows = len(grid_snapshot)
    cols = len(grid_snapshot[0])
    
    # Verifica se a posição alvo é um obstáculo
    if grid_snapshot[target_pos[1]][target_pos[0]] in obstacles:
        return None

    queue = deque([(start_pos, [])])  # (posição_atual, caminho_até_aqui)
    visited = {start_pos}

    # Direções de movimento: (dx, dy) para N, S, L, O
    directions = [(0, -1), (0, 1), (-1, 0), (1, 0)] # Cima, Baixo, Esquerda, Direita

    while queue:
        (current_x, current_y), path = queue.popleft()

        if (current_x, current_y) == target_pos:
            return path

        for dx, dy in directions:
            next_x, next_y = current_x + dx, current_y + dy

            # Verifica limites do grid
            if 0 <= next_x < cols and 0 <= next_y < rows:
                next_pos = (next_x, next_y)
                # Verifica se não é um obstáculo e não foi visitado
                if grid_snapshot[next_y][next_x] not in obstacles and next_pos not in visited:
                    visited.add(next_pos)
                    queue.append((next_pos, path + [next_pos]))
    return None