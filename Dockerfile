FROM ubuntu:eoan as build

ENV LANG C.UTF-8

# IFDEF PROXY
#! RUN echo 'Acquire::http { Proxy "http://${PROXY}"; };' >> /etc/apt/apt.conf.d/01proxy
# ENDIF

RUN apt-get update && \
    apt-get install --no-install-recommends --yes \
        python3 python3-dev python3-setuptools python3-pip python3-venv \
        build-essential

ENV APP_DIR=/usr/lib/rhasspy-nlu-hermes

# Autoconf
COPY m4/ ${BUILD_DIR}/m4/
COPY configure config.sub config.guess \
     install-sh missing aclocal.m4 \
     Makefile.in setup.py requirements.txt \
     ${BUILD_DIR}/

COPY scripts/create-venv.sh ${APP_DIR}/scripts/

# IFDEF PYPI
#! ENV PIP_INDEX_URL=http://${PYPI}/simple/
#! ENV PIP_TRUSTED_HOST=${PYPI_HOST}
# ENDIF

RUN cd ${APP_DIR} && \
    ./configure --enable-in-place && \
    make install

# -----------------------------------------------------------------------------

FROM ubuntu:eoan as run

ENV LANG C.UTF-8

# IFDEF PROXY
#! RUN echo 'Acquire::http { Proxy "http://${PROXY}"; };' >> /etc/apt/apt.conf.d/01proxy
# ENDIF

RUN apt-get update && \
    apt-get install --yes --no-install-recommends \
        python3 libpython3.7

ENV APP_DIR=/usr/lib/rhasspy-nlu-hermes

# Copy virtual environment
COPY --from=build ${APP_DIR}/.venv/ ${APP_DIR}/.venv/

# Copy source
COPY bin/rhasspy-nlu-hermes ${APP_DIR}/bin/
COPY rhasspynlu_hermes/ ${APP_DIR}/rhasspynlu_hermes/

ENTRYPOINT ["bash", "/usr/lib/rhasspy-nlu-hermes/bin/rhasspy-nlu-hermes"]
