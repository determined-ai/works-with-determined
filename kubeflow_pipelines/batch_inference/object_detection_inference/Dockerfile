FROM determinedai/environments:cuda-10.0-pytorch-1.4-tf-1.15-gpu-0.5.0

RUN pip install determined-cli==0.13.0 determined==0.13.0  Pillow
RUN pip install -U ruamel.yaml --ignore-installed

RUN mkdir /cmd/
WORKDIR /cmd/

COPY . /cmd/

ENTRYPOINT ["/bin/sh"]
