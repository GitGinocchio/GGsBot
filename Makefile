

install:
	python -m venv .venv
	cd ./.venv/Scripts/ && activate && cd ../.. && pip install -r requirements.txt

uninstall:
	pip uninstall -y -r requirements.txt

freeze: 
	pip freeze > requirements.txt

clearpycache:
	python ./src/.make/clearpycache.py

run:
	python ./src/main.py

runbot:
	python ./src/main.py --bot

runweb:
	python ./src/main.py --web --address 127.0.0.1 --port 8080 --debug
