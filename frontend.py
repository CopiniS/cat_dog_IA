# frontend.py
import json
import queue
import socket
import threading
import time
import os
from itertools import product
from concurrent.futures import ThreadPoolExecutor

# Configurações do servidor
with open("config.json", "r") as f:
    config = json.load(f)
NUM_CORES = config['cores']

HOST = config['frontend_ip'] # Endereço do servidor
PORT = config['frontend_port']        # Porta do servidor
TIMEOUT = config["timeout_minutes"] * 60    # Timeout
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

                    conn.settimeout(TIMEOUT)
                    # Recebe resultado
                    try:
                        data = conn.recv(4096)
                        result = json.loads(data.decode("utf-8"))

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

def config_queue():
    if 'fila_task' not in config or not config['fila_task']:
        # Parâmetros para gerar combinações
        modelos = ["alexnet", "mobilenet_v3_large", "mobilenet_v3_small", "resnet18", "resnet101", "vgg11", "vgg19"]
        epocas = [10, 20]
        learning_rates = [0.001, 0.0001, 0.00001]
        weight_decays = [0, 0.0001]

        # Gera todas as combinações possíveis
        combinacoes = product(modelos, epocas, learning_rates, weight_decays)

        # adiciona as combinações a fila
        for combinacao in combinacoes:
            tarefa = {
                "model_names": [combinacao[0]],
                "epochs": [combinacao[1]],
                "learning_rates": [combinacao[2]],
                "weight_decays": [combinacao[3]]
            }
            task_queue.put(tarefa)

        # Salva as combinações no arquivo de configuração
        config['fila_task'] = list(task_queue.queue)  # Converte a fila para uma lista antes de salvar
        with open('config.json', 'w') as file:
            json.dump(config, file, indent=4)
        print("Fila gerada e salva no arquivo de configuração.")

    else:
        print("A fila já existe no arquivo de configuração. Carregando...")

    # Exemplo de como acessar a fila a partir do arquivo de configuração
    max_tasks = config.get('max_tasks', len(config['fila_task']))  # Limite de tarefas na fila

    for tarefa in config['fila_task'][:max_tasks]:  # Respeita o limite definido
        task_queue.put(tarefa)


# Função principal do servidor
def main():
    # Adicionando tarefas a queue
    config_queue()

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

