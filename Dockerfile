FROM centos:7

RUN sed -i 's/mirrorlist/#mirrorlist/g' /etc/yum.repos.d/CentOS-*.repo && \
    sed -i 's|#baseurl=http://mirror.centos.org|baseurl=http://vault.centos.org|g' /etc/yum.repos.d/CentOS-*.repo

RUN yum install -y gcc gcc-c++ make wget perl-core bzip2-devel libffi-devel \
                   zlib-devel && \
    yum clean all

RUN wget -q https://www.openssl.org/source/openssl-1.1.1w.tar.gz && \
    tar xzf openssl-1.1.1w.tar.gz && \
    cd openssl-1.1.1w && \
    ./config --prefix=/usr/local/openssl --openssldir=/usr/local/openssl shared zlib && \
    make -j$(nproc) && make install && \
    cd / && rm -rf openssl-1.1.1w openssl-1.1.1w.tar.gz

RUN wget -q https://www.python.org/ftp/python/3.11.9/Python-3.11.9.tgz && \
    tar xzf Python-3.11.9.tgz && \
    cd Python-3.11.9 && \
    ./configure --enable-optimizations \
        --with-system-ffi \
        --with-openssl=/usr/local/openssl \
        --with-openssl-rpath=auto && \
    make -j$(nproc) && \
    make altinstall && \
    cd / && rm -rf Python-3.11.9 Python-3.11.9.tgz

RUN ln -sf /usr/local/bin/python3.11 /usr/bin/python && \
    ln -sf /usr/local/bin/pip3.11 /usr/bin/pip

RUN pip install --upgrade pip

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY lib/ ./lib/
RUN pip install --no-cache-dir \
    ./lib/tgw-1.0.8.7-py3-none-any.whl \
    ./lib/AmazingData-1.1.7-cp311-none-any.whl

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
