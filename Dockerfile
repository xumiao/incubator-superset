FROM nvidia/cuda:9.0-cudnn7-devel-ubuntu16.04

MAINTAINER Xu Miao

# Add a normal user
RUN useradd --user-group --create-home --shell /bin/bash work

# Configure environment
ENV LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    HOME=/home/work

# Copy code over
COPY ./ $HOME/supernorm/
RUN chown -R work:work $HOME

# Install some dependencies
# http://airbnb.io/superset/installation.html#os-dependencies
RUN apt-get update --fix-missing -y && apt-get install -y \
    apt-utils \
    build-essential \
    bzip2 \
    ca-certificates \
    curl \
    gcc \
    git \
    htop \
    iputils-ping \
    libffi-dev \
    libglib2.0-0 \
    libjpeg8-dev \
    libldap2-dev \
    libmysqlclient-dev \
    libsasl2-2 \
    libsasl2-dev \
    libsm6 \
    libssl-dev \
    libxext6 \
    libxml2-dev \
    libxrender1 \
    libxslt1-dev \
    net-tools \
    postgresql-client \
    python3-dev \
    python3-pip \
    redis-tools \
    telnet \
    vim \
    less \
    wget \
    zlib1g-dev

# Install nodejs for custom build
RUN curl -sL https://deb.nodesource.com/setup_8.x | bash -
RUN apt-get install -y nodejs
RUN curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | apt-key add -; \
    echo "deb https://dl.yarnpkg.com/debian/ stable main" | tee /etc/apt/sources.list.d/yarn.list; \
    apt-get update; \
    apt-get install -y yarn


# Install anaconda
RUN echo 'export PATH=/home/work/conda/bin:$PATH' > /etc/profile.d/conda.sh
USER work

RUN wget --quiet https://repo.continuum.io/archive/Anaconda3-5.2.0-Linux-x86_64.sh -O ~/anaconda.sh && \
    /bin/bash ~/anaconda.sh -b -p $HOME/conda && \
    rm ~/anaconda.sh

RUN $HOME/conda/bin/conda install libgcc

ENV PATH $HOME/conda/bin:$PATH

WORKDIR $HOME/supernorm

# Install requirements
RUN pip install -r requirements-dev.txt

ENV PATH=$HOME/supernorm/superset/bin:$HOME/supernorm/:/opt/conda/bin:$PATH \
    PYTHONPATH=$HOME/supernorm/:$PYTHONPATH


HEALTHCHECK CMD ["curl", "-f", "http://localhost:8088/health"]

EXPOSE 8088