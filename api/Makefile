.PHONY: test clean format

test:
	docker compose -f docker-compose.test.yml up --build --abort-on-container-exit
	docker compose -f docker-compose.test.yml down

format:
	black *.py

clean:
	docker compose -f docker-compose.test.yml down --volumes --remove-orphans
	docker system prune -f
