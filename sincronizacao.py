from memoria_compartilhada import MemoriaCompartilhada

def inicializar_sincronizacao(posicoes_baterias=None):
    """
    Inicializa a memória compartilhada e todos os mutexes necessários.
    :param posicoes_baterias: Lista opcional de posições de baterias a inicializar.
    :return: Instância de MemoriaCompartilhada pronta para uso.
    """
    memoria = MemoriaCompartilhada()

    if posicoes_baterias:
        memoria.inicializar_baterias(posicoes_baterias)

    return memoria
