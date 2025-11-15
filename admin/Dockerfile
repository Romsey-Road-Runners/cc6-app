FROM python:3.14-slim

WORKDIR /workspace/admin

# Upgrade pip
RUN pip install --upgrade pip

# Install pipenv
RUN pip install pipenv

# Install deps
COPY admin/Pipfile admin/Pipfile.lock ./
RUN pipenv install --system --deploy

# Copy shared libraries
COPY shared_libs/ ../shared_libs/

# Copy application files
COPY admin/ .

EXPOSE 8080

CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--preload", "--workers", "1", "--threads", "4", "app:app"]