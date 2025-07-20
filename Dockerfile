FROM python:3.11-slim

WORKDIR /app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONNUMBUFFERED 1
ENV PYTHONUNBUFFERED 1
ENV PORT 8080

# install system dependencies
RUN apt-get update \
    && apt-get -y install netcat-openbsd gcc curl \
    && apt-get clean

# install python dependencies
RUN pip install --upgrade pip
COPY ./requirements.txt .
RUN pip install -r requirements.txt

# Copy source code
COPY . .

# Create and set permissions for log file
RUN touch /app/bot.log && chmod 666 /app/bot.log

# Use a shell script to handle signals properly
COPY ./entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

EXPOSE ${PORT}

ENTRYPOINT ["/app/entrypoint.sh"]