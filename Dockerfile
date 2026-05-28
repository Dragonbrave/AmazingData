# RockyLinux 9 (RHEL 9 compatible, glibc 2.34) for tgw .so compatibility
FROM rockylinux:9

RUN dnf install -y epel-release && \
    dnf install -y python3.10 python3.10-pip python3.10-devel \
                   gcc gcc-c++ make && \
    dnf clean all

RUN ln -sf /usr/bin/python3.10 /usr/bin/python && \
    ln -sf /usr/bin/pip3.10 /usr/bin/pip

RUN pip install --upgrade pip

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY lib/ ./lib/
RUN pip install --no-cache-dir \
    ./lib/tgw-1.0.8.7-py3-none-any.whl \
    ./lib/AmazingData-1.1.7-cp310-none-any.whl

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
