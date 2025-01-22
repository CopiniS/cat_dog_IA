
# client.py
import json
import socket
import multiprocessing
import time
import main
import os

# Carregar configuração
with open("config.json", "r") as f:
    config = json.load(f)

# Configurações do cliente
HOST = config.get("frontedn_ip", "127.0.0.1")
PORT = config.get("frontend_port", 5000)
NUM_CORES = config.get("cores", 1)

# Função para processar uma tarefa
def process_task(task):
    print(f"[PROCESSANDO] {task}")

    #chama a funcao de treinamento do Wilson
    acc_media, rep_max = main.fazTreinamento(task)

    # result_file_content = f"Resultado da {task}"
    # result_file_name = f"result_{task}.txt"
    # return result_file_content, result_file_name

    print('log 2')

    file_path = f'/modelos/{task.model_names}_{task.epochs}_{task.learning_rates}_{task.weight_decays}_{rep_max}'

    print('log 3')

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"O arquivo {file_path} não foi encontrado.")

    print (acc_media, rep_max)
    return {'acc_media': acc_media, 'file_path': file_path}

# Função principal do cliente
def run_client():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
        client.connect((HOST, PORT))
        print(f"[CONECTADO AO SERVIDOR] {HOST}:{PORT}")

        while True:
            try:
                # Recebe tarefas
                data = client.recv(4096)
                tasks = json.loads(data.decode("utf-8"))

                if not tasks:
                    print("[NENHUMA TAREFA] Nenhuma tarefa recebida, aguardando...")
                    time.sleep(5)
                    continue

                # Processa tarefas
                with multiprocessing.Pool(NUM_CORES) as pool:
                    results = pool.map(process_task, tasks)

                # Envia resultados
                result_data = {"success": True, "results": results}
                print('result_data: ', result_data)
                client.sendall(json.dumps(result_data).encode("utf-8"))

            except Exception as e:
                print(f"[ERRO] {e}")
                break

if __name__ == "__main__":
    run_client()
