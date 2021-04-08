FROM nvidia/cuda:10.2-cudnn7-devel-ubuntu18.04

# Use New Zealand mirrors
RUN sed -i 's/archive/nz.archive/' /etc/apt/sources.list

RUN apt update

# Set timezone to Auckland
ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get install -y locales tzdata
RUN locale-gen en_NZ.UTF-8
RUN dpkg-reconfigure locales
RUN echo "Pacific/Auckland" > /etc/timezone
RUN dpkg-reconfigure -f noninteractive tzdata
ENV LANG en_NZ.UTF-8
ENV LANGUAGE en_NZ:en

# Install apt packages
RUN apt update
RUN apt install -y libxml-xpath-perl cmake build-essential pkg-config libgoogle-perftools-dev

# Install python + other things
RUN apt install -y python3-dev python3-pip gcc

# Set number of threads
ARG NUM_CORES
RUN echo Using ${NUM_CORES} threads..

# Install sentencepiece
COPY submodules/sentencepiece /code/submodules/sentencepiece
RUN mkdir /code/submodules/sentencepiece/build
WORKDIR /code/submodules/sentencepiece/build
RUN cmake .. && make -j ${NUM_CORES} && make install && ldconfig -v

# cython>=0.29
RUN pip3 install -U numpy cython pip setuptools wheel
RUN pip3 install -U spacy
RUN pip3 install natas

COPY requirements.txt /root/requirements.txt
RUN pip3 install -r /root/requirements.txt

ENV NLTK_DATA /nltk_data
RUN python3 -c "import nltk;nltk.download('punkt', download_dir='$NLTK_DATA')"

RUN python3 -m natas.download
RUN python3 -m spacy download en_core_web_md
