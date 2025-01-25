# Como Rodar:

## Instalar o python:
- vai na microsoft store e baixa o python, eu instalei o 3.12

## Clona o repositório

- Faz o git clone do repositorio:

  git clone https://github.com/CopiniS/cat_dog_IA.git

## Na raiz do projeto adicionar uma venv com o comando:

  python -m venv venvs

## Adicionar as libs na venvs:

  venvs/Scripts/activate

  pip install numpy

  pip install torch torchvision

## Configurar o arquivo config.json:
- cores: a quantidade de tasks que será enviado pra cada cliente por vez. Que será também a quantidade de processos criados pelo cliente.
- frontend_ip e frontend_port: o ip e a porta em que vai rodar o servidor na rede 
- timeout_minutes: o tempo que o servidor aguarda o retorno dos dados pelo cliente, em minutos. Se ultrapassar ele vai retornar as tasks pra fila
- replicacoes: quantidade de vezes que o cliente vai testar a mesma combinação de parametros. Para testes aconselho que deixe um valor baixo
- max_tasks: A quantidade de tasks que o servidor irá pegar da fila de tasks. Para testes aconselho que deixe um valor baixo
- fila_task: Não precisa mexer em nada, o servidor cuida sozinho dela. 

## Rodar

- Rodar o servidor 'frontend.py':

  python frontend.py

- Rode quantos clientes 'cleint.py' quiser, em quantas máquinas quiser, que o servidor vai separando as tasks para os mesmos:

  venvs/Scripts/activate

  python client.py

