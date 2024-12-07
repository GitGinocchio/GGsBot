install-requirements:
	pip install -r requirements.txt

install-binaries:

clearpycache:
	python .Makefile/clearpycache.py

run:
	python ./src/main.py