FROM python:3.10-slim

# Install system dependencies for llama-cpp-python
RUN apt-get update && apt-get install -y \
    build-essential \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Set up a non-root user (Hugging Face Space requirement)
RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH"

WORKDIR /app

# Copy requirements and install them
COPY --chown=user:user requirements.txt .
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY --chown=user:user . .

# Set environment variables
ENV HOST=0.0.0.0
ENV PORT=7860

# Expose port
EXPOSE 7860

# Start the application
CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "7860"]
