ROOT_DIR := $(shell dirname $(realpath $(firstword $(MAKEFILE_LIST))))

.PHONY: test clean format lint

test:
	cd $(ROOT_DIR) && docker compose -f docker-compose.test.yml up --build --abort-on-container-exit
	cd $(ROOT_DIR) && docker compose -f docker-compose.test.yml down

test-local:
	cd $(ROOT_DIR)/app && python -m pytest test_app.py test_database.py --cov=. --cov-report=term-missing --cov-report=xml --junit-xml=test-results.xml

test-coverage:
	cd $(ROOT_DIR)/app && pytest test_app.py test_database.py --cov=. --cov-report=term-missing --cov-report=html

format:
	cd $(ROOT_DIR)/app && black *.py
	cd $(ROOT_DIR)/api && black *.py
	cd $(ROOT_DIR)/admin && black *.py
	cd $(ROOT_DIR)/shared_libs && black *.py

format-check:
	cd $(ROOT_DIR)/app && black --check *.py
	cd $(ROOT_DIR)/api && black --check *.py
	cd $(ROOT_DIR)/admin && black --check *.py
	cd $(ROOT_DIR)/shared_libs && black --check *.py

lint:
	cd $(ROOT_DIR)/app && ruff check *.py --fix
	cd $(ROOT_DIR)/api && ruff check *.py --fix
	cd $(ROOT_DIR)/admin && ruff check *.py --fix
	cd $(ROOT_DIR)/shared_libs && ruff check *.py --fix

lint-check:
	cd $(ROOT_DIR)/app && ruff check *.py
	cd $(ROOT_DIR)/api && ruff check *.py
	cd $(ROOT_DIR)/admin && ruff check *.py
	cd $(ROOT_DIR)/shared_libs && ruff check *.py

clean:
	cd $(ROOT_DIR) && docker compose -f docker-compose.test.yml down --volumes --remove-orphans
	docker system prune -f