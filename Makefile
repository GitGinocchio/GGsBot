install:
	pip install -r requirements.txt

uninstall:
	pip uninstall -y -r requirements.txt

clearpycache:
	python .Makefile/clearpycache.py

run:
	python ./src/main.py