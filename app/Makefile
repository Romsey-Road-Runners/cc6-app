.PHONY: test clean format lint

test:
	docker compose -f docker-compose.test.yml up --build --abort-on-container-exit
	docker compose -f docker-compose.test.yml down

test-coverage:
	pytest test_app.py test_database.py --cov=. --cov-report=term-missing --cov-report=html

format:
	black *.py

lint:
	ruff check *.py --fix

clean:
	docker compose -f docker-compose.test.yml down --volumes --remove-orphans
	docker system prune -f
