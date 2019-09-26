FROM python:3.5

RUN apt-get update \
      && apt-get install -y sudo

RUN useradd -u 1000 jenkins --no-create-home

RUN echo "jenkins  ALL=(ALL)  NOPASSWD:ALL" >> /etc/sudoers
