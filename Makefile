install:
	pip install -r requirements.txt

uninstall:
	pip uninstall -y -r requirements.txt

clearpycache:
	python ./src/.make/clearpycache.py

run:
	python ./src/main.py