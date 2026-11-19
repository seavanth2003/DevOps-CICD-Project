FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY app/ .

ENV DATABASE_PATH=/data/employees.db

RUN mkdir -p /data

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
LABEL org.opencontainers.image.title="Employee Management System"

LABEL org.opencontainers.image.description="A Python Flask Employee Management application with Docker containerization, automated Pytest testing, and GitHub Actions CI/CD pipeline."

LABEL org.opencontainers.image.source="https://github.com/seavanth2003/DevOps-CICD-Project"

LABEL org.opencontainers.image.licenses="MIT"