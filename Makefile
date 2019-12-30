SHELL := bash

.PHONY: check dist venv test pyinstaller debian

version := $(shell cat VERSION)
architecture := $(shell dpkg-architecture | grep DEB_BUILD_ARCH= | sed 's/[^=]\+=//')

debian_package := rhasspy-nlu-hermes_$(version)_$(architecture)
debian_dir := debian/$(debian_package)

check:
	flake8 rhasspynlu_hermes/*.py rhasspynlu_hermes/test/*.py
	pylint rhasspynlu_hermes/*.py rhasspynlu_hermes/test/*.py
	mypy rhasspynlu_hermes/*.py rhasspynlu_hermes/test/*.py

venv:
	rm -rf .venv/
	python3 -m venv .venv
	.venv/bin/pip3 install wheel setuptools
	.venv/bin/pip3 install -r requirements_all.txt

test:
	python3 -m unittest rhasspynlu_hermes.test

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
