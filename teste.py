def parameter_combinations():
    param1 = range(1, 5)  # Exemplo de intervalo
    param2 = range(10, 15)
    param3 = range(100, 105)
    param4 = range(1000, 1005)

    for p1 in param1:
        for p2 in param2:
            for p3 in param3:
                for p4 in param4:
                    yield {"param1": p1, "param2": p2, "param3": p3, "param4": p4}
                    print('dentor de comb')

# Função para produzir tarefas dinamicamente
def produce_tasks():
    for combination in parameter_combinations():
        print(f"Tarefa adicionada: {combination}")


if __name__ == "__main__":
    produce_tasks()