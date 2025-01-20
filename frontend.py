import socket
import json
import multiprocessing
from threading import Thread

# Função para distribuir tarefas para um cliente
def handle_client(client_socket, address):
    print(f"Cliente conectado: {address}")
    try:
        while True:
            # Enviar uma tarefa ao cliente
            task = "Processar essa tarefa"
            client_socket.send(task.encode('utf-8'))
            
            # Receber o resultado do cliente
            result = client_socket.recv(1024).decode('utf-8')
            print(f"Resultado do cliente {address}: {result}")
    except ConnectionResetError:
        print(f"Cliente {address} desconectado.")
    finally:
        client_socket.close()

# Configuração do servidor
def server_main():
    with open("config.json", "r") as f:
        config = json.load(f)

    host = "127.0.0.1"  # Endereço do servidor
    port = 5000         # Porta do servidor

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen()

    print(f"Servidor iniciado em {host}:{port}")

    while True:
        client_socket, address = server_socket.accept()
        thread = Thread(target=handle_client, args=(client_socket, address))
        thread.start()

if __name__ == "__main__":
    server_main()
