FROM python:3
COPY requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt
COPY goodwe.py /app/goodwe.py
CMD ["python", "-u", "/app/goodwe.py"]
