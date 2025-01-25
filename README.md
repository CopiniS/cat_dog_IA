# Como Rodar:

## Instalar o python:
1- vai na microsoft store e baixa o python, eu instalei o 3.12

## Clona o repositório

2- Faz o git clone do repositorio:

  ```bash
  git clone https://github.com/CopiniS/cat_dog_IA.git
  ```

## Adicionar uma venv:

3- Na raiz do projeto utilizar o comando:

  ```bash
  python -m venv venvs
  ```

## Adicionar as libs na venvs

4- Usar os comandos:

  ```bash
  venvs/Scripts/activate
  ```

  ```bash
  pip install numpy
  ```

  ```bash
  pip install torch torchvision
  ```

## Configurar o arquivo config.json:

5- O que cada atributo faz:

- cores: a quantidade de tasks que será enviado pra cada cliente por vez. Que será também a quantidade de processos criados pelo cliente.
- frontend_ip e frontend_port: o ip e a porta em que vai rodar o servidor na rede 
- timeout_minutes: o tempo que o servidor aguarda o retorno dos dados pelo cliente, em minutos. Se ultrapassar ele vai retornar as tasks pra fila
- replicacoes: quantidade de vezes que o cliente vai testar a mesma combinação de parametros. Para testes aconselho que deixe um valor baixo
- max_tasks: A quantidade de tasks que o servidor irá pegar da fila de tasks. Para testes aconselho que deixe um valor baixo
- fila_task: Não precisa mexer em nada, o servidor cuida sozinho dela. 

## Rodar

6- Rodar o servidor 'frontend.py':

  ```bash
  python frontend.py
  ```

7- Rode quantos clientes 'cleint.py' quiser, em quantas máquinas quiser, que o servidor vai separando as tasks para os mesmos:

  ```bash
  venvs/Scripts/activate
  ```

  ```bash
  python client.py
  ```
