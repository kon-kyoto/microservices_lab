FROM python:latest
WORKDIR /app
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install flask
COPY app.py .
CMD ["python", "app.py"]
