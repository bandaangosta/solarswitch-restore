all: run

clean:
	rm -rf venv && rm -rf *.egg-info && rm -rf dist && rm -rf *.log*

venv:
	sudo pip3 install --upgrade pip
	sudo pip3 install virtualenv
	virtualenv --python=python3 venv
	venv/bin/pip install -r requirements.txt

run: venv
	./backup_to_influx.sh ${zip}

