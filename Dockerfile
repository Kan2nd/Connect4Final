FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
COPY server.py .
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 12345
CMD ["python", "server.py"]