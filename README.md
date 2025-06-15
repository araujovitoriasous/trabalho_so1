# Simulador de Robôs em Grid com Deadlock

Este projeto simula robôs autônomos e um robô controlado pelo jogador em um grid 40x20, com barreiras, baterias e gerenciamento de concorrência usando memória compartilhada e locks. O sistema também demonstra situações de deadlock para fins didáticos.

## Estrutura do Projeto

```plaintext
src/
    grid.py                 # Lógica do grid (matriz)
    memoria_compartilhada.py# Memória compartilhada entre processos
    robos.py                # Classe base dos robôs automáticos
    robo_jogador.py         # Robô controlado pelo usuário (curses)
    sincronizacao.py        # Inicialização de locks/mutexes
    viewer_process.py       # Visualização do grid em tempo real
    main.py                 # Execução principal do jogo
    deadlock_demo.py        # Demonstração de deadlock
    main_deadlock.py        # Entrada para simulação de deadlock
logs/                       # Logs dos robôs
```

## Como Executar

**Execute o simulador:**

- Para rodar o modo normal (jogo com robôs e jogador):

```sh
python src/main.py
```

- Para rodar a simulação de deadlock:

Edite a variável `modo` em [src/main.py](src/main.py) para `"deadlock"`:

```python
modo = "deadlock"
```

E execute novamente:

```sh
python src/main.py
```

## Controles do Jogador

- Use as teclas **WASD** para mover o robô jogador.
- Pressione **Q** para sair do modo jogador.

## Funcionalidades

- Robôs automáticos se movem aleatoriamente pelo grid, coletando baterias e duelando.
- Robô jogador pode ser controlado pelo usuário via terminal.
- Barreiras e baterias são posicionadas no grid.
- Logs de cada robô são salvos na pasta `logs/`.
- Demonstração de deadlock entre processos usando locks.
