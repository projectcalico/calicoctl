#!/usr/bin/make

build: virtualenv lint

virtualenv: .venv/bin/python
.venv/bin/python:
	sudo apt-get install -y  python-virtualenv
	virtualenv .venv
	.venv/bin/pip install nose flake8 mock pyyaml charmhelpers charm-tools ecdsa ansible ansible-lint

lint: .venv/bin/python
	@.venv/bin/flake8 hooks
	@.venv/bin/ansible-lint playbooks/site.yaml
	@.venv/bin/charm proof

func_test:
	@echo functional tests...
	@juju test

clean:
	rm -rf .venv
	find -name *.pyc -delete
