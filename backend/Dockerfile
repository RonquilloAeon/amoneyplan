FROM python:3.13-slim AS base

WORKDIR /app

# Install Poetry
RUN pip install --no-cache-dir poetry==2.1.1

# Copy poetry configuration files and source code
COPY pyproject.toml poetry.lock* README.md /app/
COPY src /app/src/

# List contents of /app to debug
RUN echo "Contents of /app:" && ls -la /app && echo "Contents of /app/src:" && ls -la /app/src

# Configure poetry to not use a virtual environment since we're in a container
RUN poetry config virtualenvs.create false

# Install dependencies
RUN poetry install --without dev --no-interaction --no-ansi

# Run as non-root user for better security
RUN useradd --create-home appuser
RUN chown -R appuser:appuser /app
USER appuser

#
# Dev stage
#
FROM base AS dev

COPY --from=base / /

# Expose the port the app runs on
EXPOSE 8000

# Run the application
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

#
# Prod stage
#
FROM base AS prod
ENV PYTHONPATH /app/src
COPY --from=base / /

# Copy the build script
COPY start.sh /app/start.sh

# Expose the port the app runs on
EXPOSE 10000

ENV DJANGO_SETTINGS_MODULE=src.amoneyplan.settings
ENTRYPOINT ["/app/start.sh"]
