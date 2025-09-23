# Stage 1: Build dependencies in a virtual environment
FROM python:3.11-slim as builder

WORKDIR /app

# Create and activate a virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Create the final, lean image
FROM python:3.11-slim

WORKDIR /app

# Copy the virtual environment from the builder stage
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy the application code
# The '.' copies everything in the build context (the 'backend' directory)
COPY . .

# Expose the port the app runs on
EXPOSE 8080

# Command to run the production server
# We use uvicorn directly, without the --reload flag
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]