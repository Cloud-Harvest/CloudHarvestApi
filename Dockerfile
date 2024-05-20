FROM python:3.12-bookworm as python

WORKDIR /src

ENV PIP_ROOT_USER_ACTION=ignore

COPY . .

# TODO: add pytest tests/ to the RUN command
RUN pip install setuptools \
    && pip install -r requirements.txt

ENTRYPOINT python CloudHarvestApi/wsgi.py
