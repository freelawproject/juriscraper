init:
	pip install -r requirements.txt

test:
	python -m unittest tests.test_everything

doc:
	pandoc --from=markdown --to=rst --output=README.rst readme.md