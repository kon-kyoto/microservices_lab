FROM python:3.12
WORKDIR /app
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir flask
COPY app.py .
CMD ["python", "app.py"]

