ifeq ($(OS), Windows_NT)
	PYTHON := python
	PIP := pip
else
	PYTHON := python3
	PIP := pip3
endif



venv:
	$(PYTHON) -m venv .venv && cd .venv/Scripts && activate

install:
	cd .venv/Scripts && activate && cd ../.. && $(PIP) install --require-virtualenv -r requirements.txt

uninstall:
	cd .venv/Scripts && activate && cd ../.. && $(PIP) uninstall -y --require-virtualenv -r requirements.txt

freeze: 
	cd .venv/Scripts && activate && cd ../.. && $(PIP) freeze --require-virtualenv > requirements.txt

clearpycache:
	$(PYTHON) ./scripts/clearpycache.py

test:
	set PYTHONPATH=src && pytest -v ./tests/

run:
	cd .venv/Scripts && activate && cd ../.. && $(PYTHON) ./src/main.py

runbot:
	cd .venv/Scripts && activate && cd ../.. && $(PYTHON) ./src/main.py --bot

runweb:
	cd .venv/Scripts && activate && cd ../.. && $(PYTHON) ./src/main.py --web --address 127.0.0.1 --port 8080 --debug