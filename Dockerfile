# RockyLinux 8 (RHEL 8 compatible, glibc 2.28) for tgw .so compatibility
FROM rockylinux:8

RUN dnf install -y epel-release && \
    dnf module enable -y python39 && \
    dnf install -y python39 python39-pip python39-devel \
                   gcc gcc-c++ make && \
    dnf clean all

RUN ln -sf /usr/bin/python3.9 /usr/bin/python && \
    ln -sf /usr/bin/pip3.9 /usr/bin/pip

RUN pip install --upgrade pip

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY lib/ ./lib/
RUN pip install --no-cache-dir \
    ./lib/tgw-1.0.8.7-py3-none-any.whl \
    ./lib/AmazingData-1.1.7-cp39-none-any.whl

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
