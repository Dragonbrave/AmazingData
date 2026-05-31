FROM rockylinux:8

RUN dnf install -y python3.11 python3.11-pip && \
    dnf clean all

RUN ln -sf /usr/bin/python3.11 /usr/bin/python && \
    ln -sf /usr/bin/pip3.11 /usr/bin/pip

RUN pip install --upgrade pip -i https://mirrors.cloud.tencent.com/pypi/simple --trusted-host mirrors.cloud.tencent.com

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i https://mirrors.cloud.tencent.com/pypi/simple --trusted-host mirrors.cloud.tencent.com

COPY lib/ ./lib/
RUN pip install --no-cache-dir \
    ./lib/tgw-1.0.8.7-py3-none-any.whl \
    ./lib/AmazingData-1.1.7-cp311-none-any.whl -i https://mirrors.cloud.tencent.com/pypi/simple --trusted-host mirrors.cloud.tencent.com && \
    TGW_LIB=$(python -c "import tgw, os; print(os.path.join(os.path.dirname(tgw.__file__), 'common_linux_lib64'))") && \
    echo "tgw common lib dir: $TGW_LIB" && \
    ls "$TGW_LIB/libtgw.so" > /dev/null && \
    echo "$TGW_LIB" > /etc/ld.so.conf.d/tgw.conf && \
    ldconfig

ENV LD_LIBRARY_PATH=/usr/lib/python3.11/site-packages/tgw/common_linux_lib64:/usr/local/lib/python3.11/site-packages/tgw/common_linux_lib64

COPY . .

EXPOSE 8000

CMD ["python", "main.py"]
