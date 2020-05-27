FROM ubuntu:eoan as build-amd64

ENV LANG C.UTF-8

RUN apt-get update && \
    apt-get install --no-install-recommends --yes \
        python3 python3-dev python3-setuptools python3-pip python3-venv \
        build-essential

# -----------------------------------------------------------------------------

FROM ubuntu:eoan as build-armv7

ENV LANG C.UTF-8

RUN apt-get update && \
    apt-get install --no-install-recommends --yes \
        python3 python3-dev python3-setuptools python3-pip python3-venv \
        build-essential

# -----------------------------------------------------------------------------

FROM ubuntu:eoan as build-arm64

ENV LANG C.UTF-8

RUN apt-get update && \
    apt-get install --no-install-recommends --yes \
        python3 python3-dev python3-setuptools python3-pip python3-venv \
        build-essential

# -----------------------------------------------------------------------------

FROM balenalib/raspberry-pi-debian-python:3.7-buster-build as build-armv6

ENV LANG C.UTF-8

# -----------------------------------------------------------------------------

ARG TARGETARCH
ARG TARGETVARIANT
FROM build-$TARGETARCH$TARGETVARIANT as build

ENV APP_DIR=/usr/lib/rhasspy-nlu-hermes
ENV BUILD_DIR=/build

# Directory of prebuilt tools
COPY download/ ${BUILD_DIR}/download/

# Copy source
COPY rhasspynlu_hermes/ ${BUILD_DIR}/rhasspynlu_hermes/

# Autoconf
COPY m4/ ${BUILD_DIR}/m4/
COPY configure config.sub config.guess \
     install-sh missing aclocal.m4 \
     Makefile.in setup.py requirements.txt rhasspy-nlu-hermes.in \
     ${BUILD_DIR}/

RUN cd ${BUILD_DIR} && \
    ./configure --prefix=${APP_DIR}

COPY VERSION README.md LICENSE ${BUILD_DIR}/

RUN cd ${BUILD_DIR} && \
    make && \
    make install

# Strip binaries and shared libraries
RUN (find ${APP_DIR} -type f \( -name '*.so*' -or -executable \) -print0 | xargs -0 strip --strip-unneeded -- 2>/dev/null) || true

# -----------------------------------------------------------------------------

FROM ubuntu:eoan as run

ENV LANG C.UTF-8

RUN apt-get update && \
    apt-get install --yes --no-install-recommends \
        python3 libpython3.7

# -----------------------------------------------------------------------------

FROM run as run-amd64

FROM run as run-armv7

FROM run as run-arm64

# -----------------------------------------------------------------------------

FROM balenalib/raspberry-pi-debian-python:3.7-buster-run as run-armv6

ENV LANG C.UTF-8

RUN install_packages \
        libpython3.7

# -----------------------------------------------------------------------------

ARG TARGETARCH
ARG TARGETVARIANT
FROM run-$TARGETARCH$TARGETVARIANT

ENV APP_DIR=/usr/lib/rhasspy-nlu-hermes
COPY --from=build ${APP_DIR}/ ${APP_DIR}/
COPY --from=build /build/rhasspy-nlu-hermes /usr/bin/

ENTRYPOINT ["bash", "/usr/bin/rhasspy-nlu-hermes"]
