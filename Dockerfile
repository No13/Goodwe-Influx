FROM python:3
COPY requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt
COPY main.py goodwe.py /app/
CMD ["python", "-u", "/app/main.py"]
