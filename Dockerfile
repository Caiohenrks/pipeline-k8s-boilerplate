# Use uma imagem base do Python
FROM python:3.9-slim

# Defina o diretório de trabalho
WORKDIR /app

# Copie os arquivos de requisitos
COPY requirements.txt requirements.txt

# Instale as dependências
RUN pip install -r requirements.txt

# Copie o código da aplicação
COPY app.py app.py

# Exponha a porta que a aplicação irá rodar
EXPOSE 5000

# Comando para rodar a aplicação
CMD ["python", "app.py"]
