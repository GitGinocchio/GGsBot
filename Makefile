

install:
	python -m venv .venv && \
	.venv\Scripts\activate && \
	pip install -r requirements.txt

uninstall:
	.venv\Scripts\activate && \
	pip uninstall -y -r requirements.txt

freeze: 
	.venv\Scripts\activate && \
	pip freeze > requirements.txt

clearpycache:
	python ./src/.make/clearpycache.py

run:
	.venv\Scripts\activate && \
	python ./src/main.py

runbot:
	.venv\Scripts\activate && \
	python ./src/main.py --bot

runweb:
	.venv\Scripts\activate && \
	python ./src/main.py --web --address 127.0.0.1 --port 8080 --debug
