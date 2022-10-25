FROM pytorch/pytorch:1.11.0-cuda11.3-cudnn8-runtime

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY ModelServer.py .
COPY finbert.py .
COPY utils.py .

EXPOSE 9000

RUN chown -R 8888 /app
RUN mkdir /.cache
RUN chmod 777 /.cache
RUN mkdir /nltk_data
RUN chmod 777 /nltk_data

CMD exec seldon-core-microservice ModelServer --service-type MODEL

ENV PYTHONUNBUFFERED=1
