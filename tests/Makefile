all: convert tests

convert:
	jupyter nbconvert --to python test_config.ipynb

tests:
	py.test --cov

