FROM rockylinux:8

RUN dnf install -y epel-release && \
    dnf module enable -y python310 && \
    dnf install -y python310 python310-pip python310-devel && \
    dnf clean all

RUN alternatives --set python /usr/bin/python3.10 && \
    alternatives --set pip /usr/bin/pip3.10

WORKDIR /app

COPY lib/ ./lib/

RUN pip install --no-cache-dir \
    ./lib/tgw-1.0.8.7-py3-none-any.whl \
    ./lib/AmazingData-1.1.7-cp310-none-any.whl

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
