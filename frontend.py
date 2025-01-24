# frontend.py
import json
import queue
import socket
import threading
import time
import os
from itertools import product
from concurrent.futures import ThreadPoolExecutor
import time

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

start_time = None
end_time = None

# Clientes conectados
clients = {}
lock = threading.Lock()
melhroes_tasks = []

# Função para lidar com clientes
def handle_client(conn, addr):
    global start_time
    try:
        print(f"[CONEXÃO ESTABELECIDA] {addr}")

        # Inicia o timer no primeiro cliente
        if start_time is None:
            start_time = time.time()
            print("Iniciando o timer!")

        print(f"fila de tasks atual: {task_queue.queue}")
        while True:
            with lock:
                if addr not in clients:
                    clients[addr] = {}
                    clients[addr]["disponivel"] = True  # Cliente está disponível
            if clients[addr]["disponivel"]:
                tasks = []
                for _ in range(4):
                    try:
                        tasks.append(task_queue.get_nowait())
                    except queue.Empty:
                        break
                clients[addr]["tarefas"] = tasks #Cliente executará estas tasks
                if tasks:
                    # Envia tarefas para o cliente
                    conn.sendall(json.dumps(tasks).encode("utf-8"))
                    clients[addr]["disponivel"] = False  # Marca cliente como ocupado

                    conn.settimeout(TIMEOUT)
                    # Recebe resultado
                    try:
                        data = conn.recv(4096)
                        result = json.loads(data.decode("utf-8"))

                        if result["success"]:
                            print(f"[SUCESSO] Cliente {addr} completou tarefas")
                            print('Arquivo .pth será enviado')

                            save_path = os.path.join(SAVE_DIR, result["results"]["file_name"])

                            print('log 1')

                            # Receber o arquivo
                            with open(save_path, 'wb') as file:
                                print('log 2')
                                while True:
                                    print('log 3')
                                    file_data = conn.recv(4096)  # 4 KB chunks
                                    print('log 4')
                                    if not file_data:
                                        print('log 5')
                                        break
                                    print('log 6')
                                    file.write(file_data)
                                    print('log 7')
                                    conn.sendall(b'OK')  # Confirm receiving chunk
                                    print('log 8')

                            print(f"Arquivo salvo como {save_path}")
                            acc_media = result["results"]["acc_media"]
                            
                            melhroes_tasks.push({"acc_media": acc_media, "save_path": save_path})

                        else:
                            print(f"[ERRO] Cliente {addr} não completou as tarefas, retornando para a fila")
                            with lock:
                                for task in tasks:
                                    task_queue.put(task)

                    except socket.timeout:
                        print(f"[TIMEOUT] Cliente {addr} não respondeu dentro do tempo limite, retornando para a fila")
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
                        print('entra aqui no finaly')
                        # Marca o cliente como disponível novamente em ambos os casos
                        clients[addr]["disponivel"] = True

    except ConnectionResetError:
        print(f"[DESCONECTADO] Cliente {addr} desconectado")
        #talvez adicionar uma verificação para ver se essas tasks ja nao estao na fila seja necessario

        #retornando as tasks para a fila
        tasks = clients[addr]["tarefas"]

        with lock:
            for task in tasks:
                task_queue.put(task)

    finally:
        conn.close()
        #retirando o cliente na lista de cliente
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

def verifica_modelos_dir(diretorio: str):
    if os.path.exists(diretorio):
    # Remove todos os arquivos dentro do diretório
        for arquivo in os.listdir(diretorio):
            caminho_arquivo = os.path.join(diretorio, arquivo)
            try:
                if os.path.isfile(caminho_arquivo) or os.path.islink(caminho_arquivo):
                    os.unlink(caminho_arquivo)  # Apaga arquivos e links simbólicos
            except Exception as e:
                print(f"Erro ao apagar {caminho_arquivo}: {e}")
    else:
        # Cria o diretório se ele não existir
        os.makedirs(diretorio)
        print(f"Diretório modelos criado com sucesso.")

def should_stop_server():
    with lock:
        # Verifica se a fila está vazia e todos os clientes estão disponíveis
        all_disponiveis = all(clients[addr]["disponivel"] for addr in clients)
        if task_queue.empty() and (all_disponiveis or not clients):
            return True
    return False

def exibir_resultados():
    global end_time
    # Encontrando o objeto com o maior valor em acc_media
    melhor_task = max(melhroes_tasks, key=lambda x: x["acc_media"])

    end_time = time.time()
    execution_time = end_time - start_time

    print(f"O melhor modelo treinado é o arquivo { melhor_task.save_path }")
    print(f"Acurácia média de { melhor_task.acc_media }")
    print(f"Tempo de execução de { execution_time }")

    


# Função principal do servidor
def main():
    # Adicionando tarefas a queue
    config_queue()
    verifica_modelos_dir('melhores_modelos')

    # Inicialização do servidor
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.bind((HOST, PORT))
        server.listen(5)
        print(f"[SERVIDOR INICIADO] Escutando em {HOST}:{PORT}")

        with ThreadPoolExecutor() as executor:
            while True:

                if should_stop_server():
                    print("[FINALIZANDO] Todas as tarefas foram concluídas e todos os clientes estão disponíveis.")
                    break

                # Aceita novas conexões
                try:
                    server.settimeout(1)  # Timeout curto para verificar condições periodicamente
                    conn, addr = server.accept()
                    executor.submit(handle_client, conn, addr)
                except socket.timeout:
                    pass  # Permite verificar novamente as condições para encerrar

    exibir_resultados()

if __name__ == "__main__":
    main()

