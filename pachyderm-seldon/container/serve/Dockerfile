FROM pytorch/pytorch:1.11.0-cuda11.3-cudnn8-runtime

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY ModelServer.py .
COPY service-account.json .

EXPOSE 9000

# Define environment variable
ENV MODEL_NAME   ModelServer
ENV SERVICE_TYPE MODEL

RUN chown -R 8888 /app

CMD exec seldon-core-microservice $MODEL_NAME --service-type $SERVICE_TYPE
