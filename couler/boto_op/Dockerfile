FROM python:alpine3.6
RUN pip install boto3

RUN mkdir /cmd/
WORKDIR /cmd/
COPY . /cmd/

ENTRYPOINT ["/bin/sh"]
