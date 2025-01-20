import socket
import json
import multiprocessing

# Função para processar a tarefa
def process_task(task):
    # Simula processamento pesado
    return f"Resultado para {task}"

# Função que processa múltiplas tarefas usando multiprocessing
def worker_main(task_queue, result_queue):
    while not task_queue.empty():
        task = task_queue.get()
        result = process_task(task)
        result_queue.put(result)

# Configuração do cliente
def client_main():
    with open("config.json", "r") as f:
        config = json.load(f)

    host = "127.0.0.1"  # Endereço do servidor
    port = 5000         # Porta do servidor

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((host, port))
    print("Cliente conectado ao servidor")

    try:
        while True:
            # Receber uma tarefa do servidor
            task = client_socket.recv(1024).decode('utf-8')
            if not task:
                break

            print(f"Tarefa recebida: {task}")

            # Criar filas para o multiprocessing
            task_queue = multiprocessing.Queue()
            result_queue = multiprocessing.Queue()

            # Adicionar a tarefa na fila
            task_queue.put(task)

            # Iniciar os processos
            cores = config["computers"][0]["cores"]  # Exemplo: usar config para cores
            processes = []
            for _ in range(cores):
                p = multiprocessing.Process(target=worker_main, args=(task_queue, result_queue))
                p.start()
                processes.append(p)

            # Aguardar os processos terminarem
            for p in processes:
                p.join()

            # Obter resultados
            results = []
            while not result_queue.empty():
                results.append(result_queue.get())

            # Enviar resultados ao servidor
            result_message = ", ".join(results)
            client_socket.send(result_message.encode('utf-8'))

    except KeyboardInterrupt:
        print("Cliente desconectado")
    finally:
        client_socket.close()

if __name__ == "__main__":
    client_main()
