# back-end/Dockerfile

FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy the entire back-end directory to /app in the container
COPY . /app

# Install dependencies
RUN pip install -r requirements.txt

# Expose the FastAPI port (8000 by default for uvicorn)
EXPOSE 8000

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
