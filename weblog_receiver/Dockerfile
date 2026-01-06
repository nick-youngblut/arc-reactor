FROM python:3.11-slim

WORKDIR /app

COPY weblog_receiver/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY weblog_receiver/ /app/weblog_receiver/
COPY backend/__init__.py /app/backend/__init__.py
COPY backend/models/ /app/backend/models/

ENV PYTHONUNBUFFERED=1

EXPOSE 8080

CMD ["uvicorn", "weblog_receiver.main:app", "--host", "0.0.0.0", "--port", "8080"]
