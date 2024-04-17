FROM python:3.9-slim

WORKDIR /app

EXPOSE 5000

COPY pull_request_summary.py requirements.txt /app/

RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir -r requirements.txt

CMD ["python", "./pull_request_summary.py"]
