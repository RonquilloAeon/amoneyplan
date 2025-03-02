FROM python:3.13-slim

WORKDIR /app

# Install system dependencies
# RUN apt-get update \
#     && apt-get install -y --no-install-recommends \
#         gcc \
#         postgresql-client \
#     && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install --no-cache-dir poetry==2.1.1

# Copy poetry configuration files
COPY pyproject.toml poetry.lock* /app/

# Configure poetry to not use a virtual environment since we're in a container
RUN poetry config virtualenvs.create false

# Install dependencies
RUN poetry install --no-dev --no-interaction --no-ansi

# Copy the application code
COPY . /app/

# Run as non-root user for better security
RUN useradd --create-home appuser
RUN chown -R appuser:appuser /app
USER appuser

# Expose the port the app runs on
EXPOSE 8000

# Run the application
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]