SHELL := bash
PYTHON_NAME = rhasspynlu_hermes
PACKAGE_NAME = rhasspy-nlu-hermes
SOURCE = $(PYTHON_NAME)
PYTHON_FILES = $(SOURCE)/*.py tests/*.py *.py
SHELL_FILES = bin/* debian/bin/*
PIP_INSTALL ?= install

.PHONY: reformat check dist venv test pyinstaller debian deploy

version := $(shell cat VERSION)
architecture := $(shell bash architecture.sh)

ifneq (,$(findstring -dev,$(version)))
	DOCKER_TAGS = -t "rhasspy/$(PACKAGE_NAME):$(version)"
else
	DOCKER_TAGS = -t "rhasspy/$(PACKAGE_NAME):$(version)" -t "rhasspy/$(PACKAGE_NAME):latest"
endif

DOCKER_PLATFORMS = linux/amd64,linux/arm64,linux/arm/v7,linux/arm/v6

# -----------------------------------------------------------------------------
# Python
# -----------------------------------------------------------------------------

reformat:
	scripts/format-code.sh $(PYTHON_FILES)

check:
	scripts/check-code.sh $(PYTHON_FILES)

venv:
	scripts/create-venv.sh

test:
	scripts/run-tests.sh $(SOURCE)

dist: sdist debian

sdist:
	python3 setup.py sdist

# -----------------------------------------------------------------------------
# Docker
# -----------------------------------------------------------------------------

docker-deploy:
	docker login --username rhasspy --password "$$DOCKER_PASSWORD"
	docker buildx build . --platform $(DOCKER_PLATFORMS) --push $(DOCKER_TAGS)

# -----------------------------------------------------------------------------
# Debian
# -----------------------------------------------------------------------------

pyinstaller:
	scripts/build-pyinstaller.sh "${architecture}" "${version}"

debian:
	scripts/build-debian.sh "${architecture}" "${version}"
