FROM python:3.12.1-slim

# Path: /app
WORKDIR /app

# Path: /app/requirements.txt
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "main.py"]
