# frontend.py
import json
import queue
import socket
import threading
import time
import os
from concurrent.futures import ThreadPoolExecutor

# Configurações do servidor
HOST = "127.0.0.1"  # Endereço do servidor
PORT = 5000          # Porta do servidor
TIMEOUT = 20 * 60    # Timeout de 20 minutos
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
            with lock:
                if addr not in clients:
                    clients[addr] = True  # Cliente está disponível

            if clients[addr]:
                tasks = []
                for _ in range(4):
                    try:
                        tasks.append(task_queue.get_nowait())
                    except queue.Empty:
                        break

                if tasks:
                    # Envia tarefas para o cliente
                    conn.sendall(json.dumps(tasks).encode("utf-8"))
                    clients[addr] = False  # Marca cliente como ocupado

                    # Recebe resultado
                    conn.settimeout(TIMEOUT)
                    try:
                        data = conn.recv(4096)
                        result = json.loads(data.decode("utf-8"))
                        print('result: ', result)

                        if result["success"]:
                            print(f"[SUCESSO] Cliente {addr} completou tarefas")
                            
                            # Salva arquivos enviados pelo cliente
                            # for file_content, file_name in result.get("results", []):
                            #     file_path = os.path.join(SAVE_DIR, file_name)
                            #     with open(file_path, "w") as f:
                            #         f.write(file_content)

                            print(f"Resultados: Acuracia media: {result.get("results", []).acc_media}  --  melhor modelo: {result.get("results", []).rep_max}")

                            clients[addr] = True
                        else:
                            raise Exception("Erro no processamento pelo cliente")

                    except (socket.timeout, Exception):
                        print(f"[ERRO] Cliente {addr} não completou as tarefas, retornando para a fila")
                        with lock:
                            for task in tasks:
                                task_queue.put(task)
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
    # Carregar tarefas para a fila
    # tasks = [f"Task {i}" for i in range(1, 101)]
    # for task in tasks:
    #     task_queue.put(task)

    # Adicionando tarefas corretamente
    parametro = {
        "model_names": ["Alexnet"],
        "epochs": [10],
        "learning_rates": [0.001],
        "weight_decays": [0],
    }
    task_queue.put(parametro)

    parametro = {
        "model_names": ["Alexnet"],
        "epochs": [20],
        "learning_rates": [0.001],
        "weight_decays": [0],
    }
    task_queue.put(parametro)

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

