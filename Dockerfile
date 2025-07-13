FROM python:3.8.13-slim-buster
RUN mkdir /app \
    mkdir /store
COPY requerments.txt /app/requerments.txt
RUN pip3 install -r /app/requerments.txt
COPY src /app
#CMD ["sleep", "100"]
CMD ["python3", "/app/main.py"]