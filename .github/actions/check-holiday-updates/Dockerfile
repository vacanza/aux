FROM python:3.13-slim

# Set working directory
WORKDIR /action

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the action script and template
COPY check_holiday_updates.py .
COPY issue_body_template.md .

# Make the script executable
RUN chmod +x check_holiday_updates.py

# Set the entrypoint
ENTRYPOINT ["python", "/action/check_holiday_updates.py"]
