install-requirements:
	pip install -r requirements.txt

install-binaries:

clearpycache:
	python .Makefile/clearpycache.py

clearguildsdata:
	python .Makefile/clearguildsdata.py

run:
	python main.py