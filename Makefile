SHELL := bash
SOURCE = rhasspynlu_hermes
PYTHON_FILES = $(SOURCE)/*.py tests/*.py *.py
SHELL_FILES = bin/* debian/bin/*

.PHONY: reformat check dist venv test pyinstaller debian deploy

version := $(shell cat VERSION)
architecture := $(shell dpkg-architecture | grep DEB_BUILD_ARCH= | sed 's/[^=]\+=//')

debian_package := rhasspy-nlu-hermes_$(version)_$(architecture)
debian_dir := debian/$(debian_package)

reformat:
	black .
	isort $(PYTHON_FILES)

check:
	flake8 $(PYTHON_FILES)
	pylint $(PYTHON_FILES)
	mypy $(PYTHON_FILES)
	black --check .
	isort --check-only $(PYTHON_FILES)
	bashate $(SHELL_FILES)
	yamllint .
	pip list --outdated

venv:
	rm -rf .venv/
	python3 -m venv .venv
	.venv/bin/pip3 install --upgrade pip
	.venv/bin/pip3 install wheel setuptools
	.venv/bin/pip3 install -r requirements.txt
	.venv/bin/pip3 install -r requirements_dev.txt

test:
	coverage run --source=$(SOURCE) -m unittest discover tests
	coverage report -m
	coverage xml

coverage:
	coverage report -m

dist: sdist debian

sdist:
	python3 setup.py sdist

pyinstaller:
	mkdir -p dist
	pyinstaller -y --workpath pyinstaller/build --distpath pyinstaller/dist rhasspynlu_hermes.spec
	tar -C pyinstaller/dist -czf dist/rhasspy-nlu-hermes_$(version)_$(architecture).tar.gz rhasspynlu_hermes/

debian: pyinstaller
	mkdir -p dist
	rm -rf "$(debian_dir)"
	mkdir -p "$(debian_dir)/DEBIAN" "$(debian_dir)/usr/bin" "$(debian_dir)/usr/lib"
	cat debian/DEBIAN/control | version=$(version) architecture=$(architecture) envsubst > "$(debian_dir)/DEBIAN/control"
	cp debian/bin/* "$(debian_dir)/usr/bin/"
	cp -R pyinstaller/dist/rhasspynlu_hermes "$(debian_dir)/usr/lib/"
	cd debian/ && fakeroot dpkg --build "$(debian_package)"
	mv "debian/$(debian_package).deb" dist/

docker: pyinstaller
	docker build . -t "rhasspy/rhasspy-nlu-hermes:$(version)"

deploy:
	echo "$$DOCKER_PASSWORD" | docker login -u "$$DOCKER_USERNAME" --password-stdin
	docker push rhasspy/rhasspy-nlu-hermes:$(version)
