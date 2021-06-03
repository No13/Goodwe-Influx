FROM python:3

COPY goodwe.py /goodwe.py

CMD ["python", "-u", "/goodwe.py"]
