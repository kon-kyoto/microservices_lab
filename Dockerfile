FROM python
WORKDIR /app
COPY generator.py .
CMD ["python", "generator.py"]

