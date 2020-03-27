FROM python:3.7-alpine as build

RUN apk add --no-cache build-base swig

ENV RHASSPY=/usr/lib/rhasspy
ENV VENV=$RHASSPY/.venv

RUN python3 -m venv $VENV
RUN $VENV/bin/pip3 install --upgrade pip
RUN $VENV/bin/pip3 install --upgrade wheel setuptools

COPY Makefile requirements.txt $RHASSPY/
COPY scripts $RHASSPY/scripts/
RUN cd $RHASSPY && make

# -----------------------------------------------------------------------------

FROM python:3.7-alpine

ENV RHASSPY=/usr/lib/rhasspy
ENV VENV=$RHASSPY/.venv

WORKDIR $RHASSPY

COPY --from=build $VENV $VENV
COPY rhasspynlu_hermes/ $RHASSPY/rhasspynlu_hermes/

ENTRYPOINT ["$VENV/bin/python3", "-m", "rhasspynlu_hermes"]
