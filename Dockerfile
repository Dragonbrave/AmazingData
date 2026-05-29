FROM rockylinux:9

RUN dnf install -y epel-release && \
    dnf install -y python3.11 python3.11-pip python3.11-devel \
                   gcc gcc-c++ make && \
    dnf clean all

RUN ln -sf /usr/bin/python3.11 /usr/bin/python && \
    ln -sf /usr/bin/pip3.11 /usr/bin/pip

RUN pip install --upgrade pip

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY lib/ ./lib/
RUN pip install --no-cache-dir \
    ./lib/tgw-1.0.8.7-py3-none-any.whl \
    ./lib/AmazingData-1.1.7-cp311-none-any.whl

ENV LD_LIBRARY_PATH=/usr/local/lib/python3.11/site-packages/tgw/common_linux_lib64:$LD_LIBRARY_PATH

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
