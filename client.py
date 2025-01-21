
# client.py
import json
import socket
import multiprocessing
import time

# Configurações do cliente
HOST = "127.0.0.1"
PORT = 5000

# Carregar configuração de núcleos
with open("config.json", "r") as f:
    config = json.load(f)
NUM_CORES = config.get("cores", 4)

# Função para processar uma tarefa
def process_task(task):
    print(f"[PROCESSANDO] {task}")
    time.sleep(5)  # Simula processamento
    result_file_content = f"Resultado da {task}"
    result_file_name = f"result_{task}.txt"
    return result_file_content, result_file_name

# Função principal do cliente
def main():
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
                client.sendall(json.dumps(result_data).encode("utf-8"))

            except Exception as e:
                print(f"[ERRO] {e}")
                break

if __name__ == "__main__":
    main()
