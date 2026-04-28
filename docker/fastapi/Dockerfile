FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/home/python

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /home/python

ARG INSTALL_DEV=false

COPY requirements.txt requirements-dev.txt ./

RUN if [ "$INSTALL_DEV" = "true" ]; then \
        pip install --no-cache-dir -r requirements-dev.txt; \
    else \
        pip install --no-cache-dir -r requirements.txt; \
    fi

COPY ./app /home/python/app
COPY ./alembic /home/python/alembic
COPY ./alembic.ini /home/python/alembic.ini

EXPOSE 10000

CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000}"]