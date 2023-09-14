FROM python:3.11.5-bookworm as python

WORKDIR /src

COPY . .

RUN pip install -r ./requirements.txt

ENTRYPOINT python harvest
