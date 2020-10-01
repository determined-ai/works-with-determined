FROM davidhershey/squad-inference:1.0

RUN pip install determined-cli==0.13.0 determined==0.13.0  Pillow
RUN pip install -U ruamel.yaml --ignore-installed
RUN pip install transformers==3.0.2

WORKDIR /cmd/
RUN rm -r /cmd/*

COPY . /cmd/
ENTRYPOINT ["/bin/sh"]
