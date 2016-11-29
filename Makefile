.PHONY: \
	all \
	clean \
	pull \
	requirements \
	update

all:

clean:
	find . -type f -name '*.pyc' -delete
	find . -type d -empty -delete

pull:
	git pull
	git submodule init
	git submodule update

requirements:
	pip install --upgrade -r config/requirements.txt

update: clean pull requirements
