FROM mcr.microsoft.com/playwright/python:v1.43.0

WORKDIR /app
COPY . .

RUN pip install -r requirements.txt

CMD ["python", "main.py"]
