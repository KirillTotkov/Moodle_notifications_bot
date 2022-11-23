FROM python:3.10-slim

WORKDIR /app

COPY ./requirements.txt /server/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /server/requirements.txt
RUN apt update && apt install vim -y && apt install postgresql -y

COPY . /app

CMD ["python", "Bot.py"]