FROM python:3.14-slim

WORKDIR /workspace/api

# Upgrade pip
RUN pip install --upgrade pip

# Install pipenv
RUN pip install pipenv

# Install deps
COPY api/Pipfile api/Pipfile.lock ./
RUN pipenv install --system --deploy

# Copy shared libraries
COPY shared_libs/ ../shared_libs/

# Copy application files
COPY api/ .

EXPOSE 8080

CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--preload", "--workers", "1", "--threads", "4", "app:app"]