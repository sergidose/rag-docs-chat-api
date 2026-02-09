FROM python:3.12-slim

WORKDIR /app
ENV PYTHONPATH=/app

# dependencias
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# código
COPY app /app/app
COPY src /app/src
COPY scripts /app/scripts
COPY data /app/data

# crea carpeta de modelos persistible
RUN mkdir -p /app/models

ENV PORT=8000
EXPOSE 8000

CMD ["python", "scripts/start_api.py"]
