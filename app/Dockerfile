# Build stage
FROM python:3.13-alpine AS builder

WORKDIR /app

# Install build dependencies
RUN apk add --no-cache gcc musl-dev libffi-dev

# Install pipenv
RUN pip install --no-cache-dir pipenv

# Copy dependency files
COPY Pipfile Pipfile.lock* ./

# Install only production dependencies
RUN pipenv install --system --deploy --clear --ignore-pipfile

# Runtime stage
FROM python:3.13-alpine AS runtime

WORKDIR /app

# Install runtime dependencies
RUN apk add --no-cache libffi

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY . .

# Pre-compile Python files
RUN python -m compileall .

EXPOSE 8080

CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--preload", "--workers", "1", "--threads", "4", "app:app"]