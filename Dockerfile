# mssql-python-pyodbc
# Python runtime with pyodbc to connect to SQL Server
FROM ubuntu:16.04

# apt-get and system utilities
RUN apt-get update && apt-get install -y \
    curl apt-utils apt-transport-https debconf-utils gcc build-essential g++-5\
    && rm -rf /var/lib/apt/lists/*

# adding custom MS repository
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
RUN curl https://packages.microsoft.com/config/ubuntu/16.04/prod.list > /etc/apt/sources.list.d/mssql-release.list

# install SQL Server drivers
RUN apt-get update && ACCEPT_EULA=Y apt-get install -y msodbcsql unixodbc-dev

# install SQL Server tools
RUN apt-get update && ACCEPT_EULA=Y apt-get install -y mssql-tools
RUN echo 'export PATH="$PATH:/opt/mssql-tools/bin"' >> ~/.bashrc
RUN /bin/bash -c "source ~/.bashrc"

RUN apt-get update \
  && apt-get install -y python3-pip python3-dev \
  && cd /usr/local/bin \
  && ln -s /usr/bin/python3 python \
  && pip3 install --upgrade pip
RUN apt-get update && apt-get install -y \
        vim \
        curl \
        wget \
        git \
        make \
        netcat \
        g++ \
        bzip2 \
        binutils
RUN apt-get install -y portaudio19-dev libopenblas-base libopenblas-dev pkg-config git-core cmake python-dev liblapack-dev libatlas-base-dev libblitz0-dev libboost-all-dev libhdf5-serial-dev libqt4-dev libsvm-dev libvlfeat-dev  python-nose python-setuptools python-imaging build-essential libmatio-dev python-sphinx python-matplotlib python-scipy
# additional dependencies
RUN apt-get install -y \
        libasound2 \
        libasound-dev \
        libssl-dev

RUN pip install pyaudio
RUN pip3 install flask
RUN pip3 install ibm-cos-sdk
RUN pip3 install pyodbc
RUN pip3 install wave
RUN pip3 install requests

WORKDIR /app
COPY . /app
CMD ["python3","main.py"]
