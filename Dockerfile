# Use an official Python runtime as a parent image
FROM python:3.9-buster

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

RUN apt-get update && apt-get install -y gcc python3-dev

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

RUN pip install --no-cache-dir python-socketio requests

# Run the script when the container launches
CMD ["python", "Integrator.py"]