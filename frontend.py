# frontend.py
import json
import queue
import socket
import threading
import time
import os
from concurrent.futures import ThreadPoolExecutor

# Configurações do servidor
with open("config.json", "r") as f:
    config = json.load(f)
NUM_CORES = config.get("cores", 4)

HOST = config.get("frontend_ip", "127.0.0.1")  # Endereço do servidor
PORT = config.get("frontend_port", 5000)          # Porta do servidor
TIMEOUT = config.get("timeout_minutes", 20) * 60    # Timeout
SAVE_DIR = "melhores_modelos"  # Diretório para salvar arquivos recebidos

# Garante que o diretório existe
os.makedirs(SAVE_DIR, exist_ok=True)

# Fila de tarefas compartilhada
task_queue = queue.Queue()

# Clientes conectados
clients = {}
lock = threading.Lock()

# Função para lidar com clientes
def handle_client(conn, addr):
    try:
        print(f"[CONEXÃO ESTABELECIDA] {addr}")
        while True:
            print('log 1')
            with lock:
                if addr not in clients:
                    clients[addr] = True  # Cliente está disponível
            if clients[addr]:
                print('log 2')
                tasks = []
                for _ in range(4):
                    try:
                        tasks.append(task_queue.get_nowait())
                        print('task_queue: ', task_queue)
                    except queue.Empty:
                        print('entra em fila vazia')
                        break
                if tasks:
                    # Envia tarefas para o cliente
                    conn.sendall(json.dumps(tasks).encode("utf-8"))
                    clients[addr] = False  # Marca cliente como ocupado

                    conn.settimeout(TIMEOUT)
                    # Recebe resultado
                    try:
                        data = conn.recv(4096)
                        result = json.loads(data.decode("utf-8"))
                        print('result: ', result)

                        if result["success"]:
                            print(f"[SUCESSO] Cliente {addr} completou tarefas")
                            print(f"Resultados: Acuracia media: {result['results'][0]['acc_media']} -- path do melhor modelo no cliente: {result['results'][0]['file_path']}")
                            
                            if task_queue.empty():
                                tasksExists = False

                        else:
                            raise Exception("Erro no processamento pelo cliente")

                    except socket.timeout:
                        print(f"[TIMEOUT] Cliente {addr} não respondeu dentro do tempo limite")
                        with lock:
                            for task in tasks:
                                task_queue.put(task)

                    except Exception as e:
                        print(f"[ERRO] Cliente {addr} não completou as tarefas, retornando para a fila")
                        print(f"[DETALHES DO ERRO] {str(e)}")
                        with lock:
                            for task in tasks:
                                task_queue.put(task)

                    finally:
                        # Marca o cliente como disponível novamente em ambos os casos
                        clients[addr] = True



    except ConnectionResetError:
        print(f"[DESCONECTADO] Cliente {addr} desconectado")
    finally:
        conn.close()
        with lock:
            if addr in clients:
                del clients[addr]

# Função principal do servidor
def main():
    # Adicionando tarefas corretamente
    parametro = {
        "model_names": ["Alexnet"],
        "epochs": [10],
        "learning_rates": [0.001],
        "weight_decays": [0],
    }
    task_queue.put(parametro)

    # parametro = {
    #     "model_names": ["Alexnet"],
    #     "epochs": [20],
    #     "learning_rates": [0.001],
    #     "weight_decays": [0],
    # }
    # task_queue.put(parametro)

    # Inicialização do servidor
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.bind((HOST, PORT))
        server.listen(5)
        print(f"[SERVIDOR INICIADO] Escutando em {HOST}:{PORT}")

        with ThreadPoolExecutor() as executor:
            while True:
                conn, addr = server.accept()
                executor.submit(handle_client, conn, addr)

if __name__ == "__main__":
    main()

