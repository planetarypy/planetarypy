all: convert tests

convert:
	jupyter nbconvert --to python test_*.ipynb

tests:
	py.test --cov

