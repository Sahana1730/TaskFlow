# Use Python 3.11 as the base environment
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the dependency file first
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application files
COPY app.py .
COPY templates/ ./templates/
COPY static/ ./static/

# Make port 5000 available
EXPOSE 5000

# Start the Flask application
CMD ["python", "app.py"]