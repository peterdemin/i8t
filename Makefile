.DEFAULT_GOAL := help

PEX := i8t
PROJ := i8t
PROJ_ROOT := src/$(PROJ) toy

define PRINT_HELP_PYSCRIPT
import re, sys

for line in sys.stdin:
	match = re.match(r'^([a-zA-Z_-]+):.*?## (.*)$$', line)
	if match:
		target, help = match.groups()
		print("%-10s %s" % (target, help))
endef
export PRINT_HELP_PYSCRIPT

.PHONY: virtual_env_set
virtual_env_set:
ifndef VIRTUAL_ENV
	$(error VIRTUAL_ENV not set)
endif

.PHONY: help
help:
	@python -c "$$PRINT_HELP_PYSCRIPT" < $(MAKEFILE_LIST)

.PHONY: clean
clean: ## remove build artifacts
	rm -rf build/ \
	       dist/ \
	       .eggs/
	rm -f $(PEX)
	find . -name '.eggs' -type d -exec rm -rf {} +
	find . -name '*.egg-info' -exec rm -rf {} +
	find . -name '*.egg' -exec rm -f {} +
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

.PHONY: dist
dist: clean ## builds source and wheel package
	python -m build -n

.PHONY: release
release: dist ## package and upload a release
	twine upload dist/*

.PHONY: autorelease
autorelease: ## Release the next patch version through CI
	bumpversion patch
	git push --follow-tags

$(PEX) pex:
	pex . -e $(PROJ).cli:cli --validate-entry-point -o $(PEX)

.PHONY: check
check: fmt lint test ## run lint and test

.PHONY: lint
lint: ## check style with pylint
	pylint $(PROJ_ROOT)
	mypy $(PROJ_ROOT)

.PHONY: test
test: ## run test suite
	pytest --cov=$(PROJ) --cov=toy $(PROJ_ROOT) --cov-fail-under=100

.PHONY: install
install: ## install the package with dev dependencies
	pip install -e . -r requirements/local.txt

.PHONY: sync
sync: ## completely sync installed packages with dev dependencies
	pip-sync requirements/local.txt
	pip install -e .

.PHONY: lock
lock: ## lock versions of third-party dependencies
	pip-compile-multi \
		--allow-unsafe \
		--use-cache \
		--autoresolve \
		--no-upgrade

.PHONY: upgrade
upgrade: ## upgrade versions of third-party dependencies
	pip-compile-multi \
		--allow-unsafe \
		--autoresolve \
		--use-cache

.PHONY: fmt
fmt: ## Reformat all Python files
	isort $(PROJ_ROOT)
	black $(PROJ_ROOT)

.PHONY: init
init: virtual_env_set install
	pre-commit install
