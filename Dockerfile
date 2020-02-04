FROM python:3.7-alpine

RUN apk add --no-cache bash

RUN pip3 install --upgrade pip

COPY requirements.txt /tmp/
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt

RUN addgroup -S appgroup && adduser -S appuser -G appgroup
WORKDIR /usr
USER appuser

COPY **/*.py lib/rhasspynlu_hermes/

COPY docker/rhasspy-nlu-hermes bin/

ENTRYPOINT ["/usr/bin/rhasspy-nlu-hermes"]
