CURRENT_DIR = $(shell pwd)

help:
	ehco "make clean, sdist, upload"


clean:
	rm -fr dist/
	find . -name '*.egg-info' -exec rm -fr {} +
	py3clean .


sdist: clean
	python setup.py sdist


upload:
	twine upload --repository-url http://pypi.tport.cf dist/rpc_helper-* --skip-existing --verbose
