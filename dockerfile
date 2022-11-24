FROM python:3.10-slim

WORKDIR /app

COPY ./requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt
RUN apt update && apt install vim -y

COPY . /app

CMD ["python", "Bot.py"]