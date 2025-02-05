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
from datetime import timedelta

# Configurações do servidor
with open("config.json", "r") as f:
    config = json.load(f)
QUANT_TASKS = config.get('quant_tasks', len(config['fila_task']))  # quantas tasks envia por vez

HOST = config['frontend_ip'] # Endereço do servidor
PORT = config['frontend_port']        # Porta do servidor
TIMEOUT = config["timeout_minutes"] * 60    # Timeout

# Fila de tarefas compartilhada
task_queue = queue.Queue()

start_time = None

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
                    clients[addr] = {}
                    clients[addr]["disponivel"] = True  # Cliente está disponível
            if clients[addr]["disponivel"]:
                tasks = []
                for _ in range(QUANT_TASKS):
                    try:
                        tasks.append(task_queue.get_nowait())
                    except queue.Empty:
                        break
                clients[addr]["tarefas"] = tasks #Cliente executará estas tasks
                if tasks:
                    print(f"[ENVIANDO TAKS]: {tasks}")
                    # Envia tarefas para o cliente
                    json_data = json.dumps(tasks)
                    conn.sendall(json_data.encode("utf-8"))
                    clients[addr]["disponivel"] = False  # Marca cliente como ocupado

                    conn.settimeout(TIMEOUT)
                    # Recebe resultado
                    try:
                        data = conn.recv(4096)
                        result = json.loads(data.decode("utf-8"))

                        if result["success"]:
                            print(f"[SUCESSO] Cliente {addr} completou tarefas")
                            try:
                                #AQUI COMEÇA A PARTE DE SALVAR O RESULTADO PARA CASO DE FALAHAR O SERVIDOR, para nao perder tudo que ja processou
                                melhor_task = result["results"]["melhor_task"]
                                tempo_task_Executada = result["results"]["tempo_task_Executada"]

                                print('result["results"]["tempo_task_Executada"]: ', (result["results"]["tempo_task_Executada"]))
                                print('result["results"]: ', (result["results"]))

                                
                                with open("resultados.json", "r") as f:
                                    dados = json.load(f)


                                tasks_executadas = dados.get("tasks_executadas", [])
                                melhores_tasks = dados.get("melhores_tasks", [])  # Retorna uma lista vazia se a chave não existir
                                tempo_total_gasto = dados.get("tempo_total_gasto", 0)  # Retorna None se a chave não existir

                                tasks_executadas.extend(task["id"] for task in tasks)
                                melhores_tasks.append({"id": melhor_task["id"], "acc_media": melhor_task["acc_media"]})
                                tempo_total_gasto += tempo_task_Executada
                                
                                dados["tasks_executadas"] = tasks_executadas
                                dados["melhores_tasks"] = melhores_tasks
                                dados["tempo_total_gasto"] = tempo_total_gasto
                                # Salvando os dados de volta no JSON
                                with open("resultados.json", "w") as f:
                                    json.dump(dados, f, indent=4)

                                print("[SUCESSO] Resultados salvos com sucesso!")
                            except Exception as e:
                                print(f"[ERRO] Falha ao salvar o resultado: {e}")

                            # print('Arquivo .pth será enviado')

                            # save_path = os.path.join(SAVE_DIR, result["results"]["file_name"])
                            # file_size = int(result["results"]["file_size"])  # Novo campo vindo do cliente
                            # received_data = 0

                            # # Receber o arquivo
                            # with open(save_path, 'wb') as file:
                            #     while received_data < file_size:
                            #         file_data = conn.recv(4096)  # 4 KB chunks
                            #         if not file_data:
                            #             break
                            #         file.write(file_data)
                            #         received_data += len(file_data)  # Incrementa o total recebido
                            #         # conn.sendall(b'OK')  # Confirmação de recebimento
                            # if received_data == file_size:
                            #     print(f"[SUCESSO]: Arquivo salvo como {save_path}")
                            #     acc_media = result["results"]["acc_media"]
                            #     melhroes_tasks.append({"acc_media": acc_media, "save_path": save_path})
                            # else:
                            #     print(f"[ERRO] Arquivo não salvo. Recebido: {received_data}, bytes, esperado: {file_size} bytes")

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
                        # Marca o cliente como disponível novamente em ambos os casos
                        clients[addr]["disponivel"] = True
                else:
                    break

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
    
    with open("resultados.json", "r") as f:
        dados = json.load(f)
    tasks_executadas = dados.get('tasks_executadas', [])

    
    if 'fila_task' not in config or not config['fila_task']:
        # Parâmetros para gerar combinações
        modelos = ["alexnet", "mobilenet_v3_large", "mobilenet_v3_small", "resnet18", "resnet101", "vgg11", "vgg19"]
        epocas = [5, 10]
        learning_rates = [0.001, 0.0001, 0.00001]
        weight_decays = [0, 0.0001]

        # Gera todas as combinações possíveis
        combinacoes = product(modelos, epocas, learning_rates, weight_decays)

        # adiciona as combinações a fila
        
        i = 1
        for combinacao in combinacoes:
            tarefa = {
                "id": i,
                "model_names": [combinacao[0]],
                "epochs": [combinacao[1]],
                "learning_rates": [combinacao[2]],
                "weight_decays": [combinacao[3]]
            }
            if any(task == i for task in tasks_executadas):
                i += 1
                continue
            task_queue.put(tarefa)
            i += 1

        # Salva as combinações no arquivo de configuração
        config['fila_task'] = list(task_queue.queue)  # Converte a fila para uma lista antes de salvar
        with open('config.json', 'w') as file:
            json.dump(config, file, indent=4)
        print("Fila gerada e salva no arquivo de configuração.")

    else:
        print("A fila já existe no arquivo de configuração. Carregando...")

    # Exemplo de como acessar a fila a partir do arquivo de configuração
        max_tasks = config.get('max_tasks', len(config['fila_task']))  # Limite de tarefas na fila

        i = 1
        for tarefa in config['fila_task'][:max_tasks]:  # Respeita o limite definido
            if any(task == i for task in tasks_executadas):
                i += 1
                continue
            task_queue.put(tarefa)
            i += 1

# def verifica_modelos_dir(diretorio: str):
#     if os.path.exists(diretorio):
#     # Remove todos os arquivos dentro do diretório
#         for arquivo in os.listdir(diretorio):
#             caminho_arquivo = os.path.join(diretorio, arquivo)
#             try:
#                 if os.path.isfile(caminho_arquivo) or os.path.islink(caminho_arquivo):
#                     os.unlink(caminho_arquivo)  # Apaga arquivos e links simbólicos
#             except Exception as e:
#                 print(f"[ERRO]: Erro ao apagar {caminho_arquivo}: {e}")
#     else:
#         # Cria o diretório se ele não existir
#         os.makedirs(diretorio)
#         print(f"Diretório modelos criado com sucesso.")

def should_stop_server():
    with lock:
        # Verifica se a fila está vazia e todos os clientes estão disponíveis
        all_disponiveis = all(clients[addr]["disponivel"] for addr in clients)
        if task_queue.empty() and (all_disponiveis or not clients):
            return True
    return False

def exibir_resultados():
    # Encontrando o objeto com o maior valor em acc_media
    with open('resultados.json', 'r') as f:
        dados = json.load(f)

    melhores_tasks = dados.get('melhores_tasks', [])
    tempo_tasks_somado = dados.get('tempo_total_gasto', 0)
    melhor_task = dados.get('melhor_task', None)
    
    end_time = time.time()
    execution_time = end_time - start_time
    #Maior o tempo de execução por tasks somado e o tempo de execução sequencial
    correct_time = max(tempo_tasks_somado, execution_time)
    formatted_time = str(timedelta(seconds=int(correct_time)))

    if melhores_tasks:
        melhor_task = max(melhores_tasks, key=lambda x: x["acc_media"])

        with open('config.json', 'r') as f:
            dados_fila = json.load(f)

        melhor_task_completa = next((task for task in dados_fila['fila_task'] if task["id"] == melhor_task["id"]), None)

        if melhor_task_completa:
            print('[RESULTADOS]')
            print(f"A melhor combinação foi:")
            print(f"model_names: {melhor_task_completa['model_names']}")
            print(f"epochs: {melhor_task_completa['epochs']}")
            print(f"learning_rates: {melhor_task_completa['learning_rates']}")
            print(f"weight_decays: {melhor_task_completa['weight_decays']}")
            print(f"Teve a Acurácia média de { melhor_task['acc_media'] }")
    else:
        print('[ERRO]: não conseguiu achar o melhor modelo')
    print(f"Tempo de execução de { formatted_time }")

    


# Função principal do servidor
def main():
    global start_time
    # Adicionando tarefas a queue
    config_queue()
    # verifica_modelos_dir('melhores_modelos')

    # Inicialização do servidor
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.bind((HOST, PORT))
        server.listen(5)
        print(f"[SERVIDOR INICIADO] Escutando em {HOST}:{PORT}")

        start_time = time.time()
        print("[INICIANDO O TIMER]")

        with ThreadPoolExecutor() as executor:
            while True:

                if should_stop_server():
                    print("[FINALIZANDO] Todas as tarefas foram concluídas e todos os clientes estão disponíveis.")
                    exibir_resultados()
                    break

                # Aceita novas conexões
                try:
                    server.settimeout(1)  # Timeout curto para verificar condições periodicamente
                    conn, addr = server.accept()
                    executor.submit(handle_client, conn, addr)
                except socket.timeout:
                    pass  # Permite verificar novamente as condições para encerrar
    print('END')

if __name__ == "__main__":
    main()

