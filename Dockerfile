# Using Python 3.10-slim as the base image
FROM python:3.10-slim

# Set /app as the working directory
WORKDIR /app

# Copy only the requriements.txt file to the container (this is a good practice)
COPY requirements.txt .

# Install all required dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy all the code in the working directory
COPY . .

# Expose an HTTP port for the web server
EXPOSE 8080

# Define the run command to start the bot
CMD ["python", "./src/main.py"]
