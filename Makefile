ROOT_DIR := $(shell dirname $(realpath $(firstword $(MAKEFILE_LIST))))

.PHONY: test clean format lint

test:
	cd $(ROOT_DIR) && docker compose -f docker-compose.test.yml up test-app test-api test-admin --build --abort-on-container-exit
	cd $(ROOT_DIR) && docker compose -f docker-compose.test.yml down

test-app:
	cd $(ROOT_DIR) && docker compose -f docker-compose.test.yml up test-app --build --abort-on-container-exit
	cd $(ROOT_DIR) && docker compose -f docker-compose.test.yml down

test-api:
	cd $(ROOT_DIR) && docker compose -f docker-compose.test.yml up test-api --build --abort-on-container-exit
	cd $(ROOT_DIR) && docker compose -f docker-compose.test.yml down

test-admin:
	cd $(ROOT_DIR) && docker compose -f docker-compose.test.yml up test-admin --build --abort-on-container-exit
	cd $(ROOT_DIR) && docker compose -f docker-compose.test.yml down

test-local:
	cd $(ROOT_DIR)/app && python -m pytest test_app.py test_database.py --cov=. --cov-report=term-missing --cov-report=xml --junit-xml=test-results.xml
	cd $(ROOT_DIR)/api && python -m pytest test_api.py --cov=. --cov-report=term-missing
	cd $(ROOT_DIR)/admin && python -m pytest test_admin.py --cov=. --cov-report=term-missing

test-local-app:
	cd $(ROOT_DIR)/app && python -m pytest test_app.py test_database.py --cov=. --cov-report=term-missing --cov-report=xml --junit-xml=test-results.xml

test-local-api:
	cd $(ROOT_DIR)/api && python -m pytest test_api.py --cov=. --cov-report=term-missing

test-local-admin:
	cd $(ROOT_DIR)/admin && python -m pytest test_admin.py --cov=. --cov-report=term-missing

test-coverage:
	cd $(ROOT_DIR)/app && pytest test_app.py test_database.py --cov=. --cov-report=term-missing --cov-report=html
	cd $(ROOT_DIR)/api && pytest test_api.py --cov=. --cov-report=term-missing --cov-report=html
	cd $(ROOT_DIR)/admin && pytest test_admin.py --cov=. --cov-report=term-missing --cov-report=html

format:
	cd $(ROOT_DIR)/app && black *.py
	cd $(ROOT_DIR)/api && black *.py
	cd $(ROOT_DIR)/admin && black *.py
	cd $(ROOT_DIR)/shared_libs && black *.py

format-app:
	cd $(ROOT_DIR)/app && black *.py

format-api:
	cd $(ROOT_DIR)/api && black *.py

format-admin:
	cd $(ROOT_DIR)/admin && black *.py

format-check:
	cd $(ROOT_DIR)/app && black --check *.py
	cd $(ROOT_DIR)/api && black --check *.py
	cd $(ROOT_DIR)/admin && black --check *.py
	cd $(ROOT_DIR)/shared_libs && black --check *.py

format-check-app:
	cd $(ROOT_DIR)/app && black --check *.py

format-check-api:
	cd $(ROOT_DIR)/api && black --check *.py

format-check-admin:
	cd $(ROOT_DIR)/admin && black --check *.py

lint:
	cd $(ROOT_DIR)/app && ruff check *.py --fix
	cd $(ROOT_DIR)/api && ruff check *.py --fix
	cd $(ROOT_DIR)/admin && ruff check *.py --fix
	cd $(ROOT_DIR)/shared_libs && ruff check *.py --fix

lint-app:
	cd $(ROOT_DIR)/app && ruff check *.py --fix

lint-api:
	cd $(ROOT_DIR)/api && ruff check *.py --fix

lint-admin:
	cd $(ROOT_DIR)/admin && ruff check *.py --fix

lint-check:
	cd $(ROOT_DIR)/app && ruff check *.py
	cd $(ROOT_DIR)/api && ruff check *.py
	cd $(ROOT_DIR)/admin && ruff check *.py
	cd $(ROOT_DIR)/shared_libs && ruff check *.py

lint-check-app:
	cd $(ROOT_DIR)/app && ruff check *.py

lint-check-api:
	cd $(ROOT_DIR)/api && ruff check *.py

lint-check-admin:
	cd $(ROOT_DIR)/admin && ruff check *.py

clean:
	cd $(ROOT_DIR) && docker compose -f docker-compose.test.yml down --volumes --remove-orphans
	docker system prune -f