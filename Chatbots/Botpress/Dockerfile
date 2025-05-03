FROM python:3.9-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ARG BOTPRESS_WEBHOOK_ID
ENV BOTPRESS_WEBHOOK_ID=${BOTPRESS_WEBHOOK_ID}


EXPOSE 8888

CMD ["python", "chat.py"]
