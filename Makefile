.PHONY: setup test

setup:
	python3 -m venv .venv
	.venv/bin/pip install -r requirements-dev.txt
	.venv/bin/playwright install chromium

test:
	.venv/bin/pytest tests/ -v
