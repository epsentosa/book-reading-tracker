FROM alpine:3.13
ENV PYTHONUNBUFFERED=1

RUN apk add --update --no-cache python3 python3-dev mariadb-dev \
    gcc musl-dev libffi-dev && ln -sf python3 /usr/bin/python

RUN python -m ensurepip
RUN pip3 install --no-cache --upgrade pip setuptools

WORKDIR /app

COPY requirements.txt requirements.txt

RUN pip install --no-cache wheel && pip --no-cache-dir install -r requirements.txt

COPY src/ .

CMD ["python","app.py"]
