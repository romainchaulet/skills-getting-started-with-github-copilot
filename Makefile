PYTHON=python3
REQ=requirements.txt

.PHONY: install run test

install:
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -r $(REQ)

run:
	uvicorn src.app:app --reload

test:
	pytest tests
