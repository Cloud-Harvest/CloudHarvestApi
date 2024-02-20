FROM python:3.12-bookworm as python

WORKDIR /src

ENV PIP_ROOT_USER_ACTION=ignore

COPY . .

RUN pip install -r ./requirements.txt

RUN mkdir -pv /etc/harvest.d/

# copy the default harvest.yaml unless it already exists (previously mounted)
RUN cp -vn /src/harvest/harvest.yaml /etc/harvest.d/harvest.yaml

RUN chmod 600 /etc/harvest.d/*

ENTRYPOINT python harvest/wsgi.py
