.PHONY: test clean format lint

test:
	docker compose -f docker-compose.test.yml up --build --abort-on-container-exit
	docker compose -f docker-compose.test.yml down

test-local:
	python -m pytest test_app.py test_database.py --cov=. --cov-report=term-missing --cov-report=xml --junit-xml=test-results.xml

test-coverage:
	pytest test_app.py test_database.py --cov=. --cov-report=term-missing --cov-report=html

format:
	black *.py

format-check:
	black --check *.py

lint:
	ruff check *.py --fix

lint-check:
	ruff check *.py

clean:
	docker compose -f docker-compose.test.yml down --volumes --remove-orphans
	docker system prune -f
