FROM python:3.8-slim
RUN pip install seldon-deploy-sdk==1.5.0
RUN pip install kubernetes==23.3.0
ADD "https://www.random.org/cgi-bin/randbyte?nbytes=10&format=h" skipcache
ADD ./deploy.py /
ADD ./add_shadow.py /
ENTRYPOINT [ "/bin/bash" ]
