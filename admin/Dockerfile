FROM python:3.14-alpine

WORKDIR /app

# Install dependencies
RUN apk add --no-cache libffi
RUN pip install --upgrade pip

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared modules
COPY ../shared_libs/database.py ./
COPY ../shared_libs/auth.py ./

# Copy application
COPY app.py .

EXPOSE 8081

CMD ["gunicorn", "--bind", "0.0.0.0:8081", "--preload", "--workers", "1", "--threads", "4", "app:app"]