FROM python:3.11.5-bookworm as python

WORKDIR /src

COPY . .

RUN pip install -r ./requirements.txt

RUN mkdir -p /etc/harvest.d/api/

# copy the default harvest.yaml unless it already exists (previously mounted)
RUN cp -vn /src/harvest/harvest.yaml /etc/harvest.d/api/harvest.yaml

RUN chmod 600 /etc/harvest.d/*

ENTRYPOINT python harvest
