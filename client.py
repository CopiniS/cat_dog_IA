
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
HOST = config['frontend_ip']
PORT = config['frontend_port']
NUM_CORES = config['cores']

# Função para processar uma tarefa
def process_task(task):
    print(f"[PROCESSANDO] {task}")

    #chama a funcao de treinamento do Wilson
    acc_media, rep_max = main.fazTreinamento(task)

    # result_file_content = f"Resultado da {task}"
    # result_file_name = f"result_{task}.txt"
    # return result_file_content, result_file_name


    file_path = os.path.join('modelos', f"{task['model_names'][0]}_{task['epochs'][0]}_{task['learning_rates'][0]}_{task['weight_decays'][0]}_{rep_max}.pth")
    file_name = f"{task['model_names'][0]}_{task['epochs'][0]}_{task['learning_rates'][0]}_{task['weight_decays'][0]}_{rep_max}.pth"
    file_size = os.path.getsize(file_path)

    if not os.path.exists(file_path):
        print(f"O arquivo {file_path} não foi encontrado.")
        return None

    return {'acc_media': acc_media, 'file_path': file_path, 'file_name': file_name, 'file_size': file_size}

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

# Função principal do cliente
def run_client():
    verifica_modelos_dir('modelos')
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
                if not results:
                    result_data = {"success": False}
                    client.sendall(json.dumps(result_data).encode("utf-8"))

                #Verifica a melhor task, entre as que executaram em paralelo
                melhor_task = None
                maior_acc_media = 0
                for result in results:
                    if result["acc_media"] > maior_acc_media:
                        melhor_task = result
                        maior_acc_media = result["acc_media"]

                result_data = {"success": True, "results": melhor_task}
                print('result_data: ', result_data)
                client.sendall(json.dumps(result_data).encode("utf-8"))

                if result_data['success']:
                    print("Treinamento realizado com sucesso. Enviando o arquivo pth...")

                    # Enviar o arquivo em pedaços de 4KB
                    with open(result_data["results"]["file_path"], 'rb') as file:
                        while chunk := file.read(4096):  # 4 KB chunks
                            client.sendall(chunk)
                            # Esperar pela confirmação do servidor
                            response = client.recv(2)
                            if response != b'OK':
                                print("Erro na transmissão. Tentando novamente...")
                                break
                    
                    print("Arquivo enviado com sucesso")
                else:
                    print("falha no treinamento. Nenhum arquivo será enviado.")

            except Exception as e:
                print(f"[ERRO] {e}")
                break

if __name__ == "__main__":
    run_client()
