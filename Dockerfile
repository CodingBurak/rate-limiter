# Use an official Python runtime as a parent image
FROM python:3.11

# Set the working directory in the container
WORKDIR .

# Copy the current directory contents into the container
COPY . .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 8080 available to the world outside this container
EXPOSE 8080
ENV ALGORITHM_TYPE tbl

# Run main.py when the container launches
CMD ["python", "main/main.py", "-limiteralgo", "$ALGORITHM_TYPE"]