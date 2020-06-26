#!/bin/bash
sudo yum install -y python3-devel.x86_64

sudo mkdir /home/.config/

sudo chmod -R 777 /home/.config/

sudo pip3 install torch==1.5.0+cpu torchvision==0.6.0+cpu -f https://download.pytorch.org/whl/torch_stable.html

sudo pip3 install -U \
    boto3 \
    Pillow \
    numpy \
    pandas \
    determined==0.12.4 \
    pyarrow==0.14.1

sudo aws s3 cp s3://<YOUR STARTUP BUCKET>/delta-core_2.11-0.6.0.jar /usr/lib/spark/jars/
