install:
	pipenv install

activate:
	pipenv shell

test:
	cd LittleLemon && python3 manage.py test

runserver:
	cd LittleLemon && python manage.py runserver

makemigrations:
	cd LittleLemon && python manage.py makemigrations

migrate:
	cd LittleLemon && python manage.py migrate

fmt:
	ruff format .
	ruff check --select I --fix .

lint:
	ruff check --fix .