SHELL=/bin/bash

release: venv
	source ./venv/bin/activate && pytest -v && python setup.py bdist_wheel
	python -m twine upload --skip-existing ./dist/*

rlz:
	poetry run pytest -v
	poetry build
	poetry publish

venv:
	virtualenv venv
	source venv/bin/activate && pip install -r ./requirements.txt
