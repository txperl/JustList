FROM python:3.8-slim

WORKDIR /usr/src

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

VOLUME [ "/usr/src/app/config/", "/usr/src/app/templates/" ]
COPY . .

CMD [ "python", "-u", "./main.py" ]
