FROM python:latest
WORKDIR /app
COPY app.py .
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install flask
CMD ["python", "app.py"]
