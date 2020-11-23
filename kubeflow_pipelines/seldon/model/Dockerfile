FROM python:3.7-slim
RUN apt-get update && apt-get install -y gcc python3-dev patch

RUN mkdir /app
WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt

RUN mkdir /.config && chmod 777 /.config && chmod -R 777 /app
EXPOSE 5000

# Define environment variable
ENV MODEL_NAME MNISTModel
ENV API_TYPE REST
ENV SERVICE_TYPE MODEL
ENV PERSISTENCE 0

COPY . /app

CMD exec seldon-core-microservice $MODEL_NAME $API_TYPE --service-type $SERVICE_TYPE --persistence $PERSISTENCE
