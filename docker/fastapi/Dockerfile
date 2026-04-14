FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /home/python
ENV PYTHONPATH=/home/python

COPY requirements.txt .
RUN pip install --no-cache-dir -r /home/python/requirements.txt

COPY ./app /home/python/app
COPY ./tests /home/python/tests
COPY ./.env /home/python/.env

EXPOSE 8000