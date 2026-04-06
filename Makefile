up:
	docker compose up -d

down:
	docker compose down

api:
	cd apps/api && poetry run uvicorn app.main:app --reload --port 8000

web:
	cd apps/web && pnpm dev

db:
	docker exec -it groundediq-db psql -U groundediq -d groundediq