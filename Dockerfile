# Use a lightweight Python image
FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Copy only requirements first to leverage caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Ensure data folder exists and is writable
RUN mkdir -p /app/data
RUN chmod -R 777 /app/data

# Expose the port defined by the environment variable
EXPOSE 80

# Run the app
CMD ["python", "app.py"]
