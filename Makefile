SHELL=/bin/bash

release: venv
	source ./venv/bin/activate && pytest -v && python setup.py bdist_wheel
	python -m twine upload --skip-existing ./dist/*
	
venv:
	virtualenv venv
	source venv/bin/activate && pip install -r ./requirements.txt
