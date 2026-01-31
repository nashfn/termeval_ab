FROM python:3.11-slim

WORKDIR /app

# Copy project files
COPY pyproject.toml .
COPY src/ src/

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Expose port
EXPOSE 9010

# Run the server
CMD ["python", "src/server.py", "--host", "0.0.0.0", "--port", "9010"]
