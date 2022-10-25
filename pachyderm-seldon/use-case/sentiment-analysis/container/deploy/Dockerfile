FROM python:3.8

WORKDIR /app

COPY requirements.txt /app
RUN pip install -r requirements.txt

COPY deploy.py /app

ENV PYTHONUNBUFFERED=1
