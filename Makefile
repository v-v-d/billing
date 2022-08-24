start:
	docker-compose up --build -d

stop:
	docker-compose down

stop-tests:
	docker-compose -f docker-compose.local.yml down

start-api:
	docker-compose up --build -d app

start-r-worker:
	docker-compose up --build -d receipts-worker

start-s-worker:
	docker-compose up --build -d subscription-worker

stop-api:
	docker-compose stop app

stop-r-worker:
	docker-compose stop receipts-worker

stop-s-worker:
	docker-compose stop subscription-worker

tests:
	docker-compose -f docker-compose.local.yml up --build --exit-code-from sut

migrate:
	docker-compose up -d app && docker-compose exec app alembic revision --autogenerate -m "$(name)"

upgrade:
	docker-compose up -d app && docker-compose exec app alembic upgrade head

downgrade:
	docker-compose up -d app && docker-compose exec app alembic downgrade -1

db-shell:
	docker-compose up -d db && docker-compose exec db psql -U postgres -W billing