FROM python:3.12-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1

COPY server_main.py ./
COPY config/settings.json ./config/settings.json
COPY src/__init__.py ./src/__init__.py
COPY src/core/ ./src/core/
COPY src/network/ ./src/network/
COPY src/utils/ ./src/utils/

EXPOSE 5000/tcp

CMD ["python", "server_main.py"]