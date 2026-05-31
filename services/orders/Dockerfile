FROM python:3.12
WORKDIR /app
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt
COPY app.py .
COPY gunicorn.conf.py .
RUN addgroup --gid 1000 appuser && adduser --uid 1000 --gid 1000 --disabled-password --gecos "" appuser
USER appuser
CMD ["gunicorn", "--config", "gunicorn.conf.py", "app:app"]
