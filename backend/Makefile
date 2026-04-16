VENV = ../venv
PYTHON = $(VENV)/bin/python
UVICORN = $(VENV)/bin/uvicorn

run:
	$(UVICORN) app.main:app --reload

seed:
	$(PYTHON) -m app.seed

install:
	$(PYTHON) -m pip install -r requirements.txt
