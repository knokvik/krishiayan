.PHONY: install train seed test dev api frontend figures eval

install:
	python -m pip install -e ".[dev]"

train:
	python ml/train.py

seed:
	python scripts/seed.py

eval:
	python ml/evaluate.py

figures:
	python scripts/make_figures.py

test:
	pytest

api:
	uvicorn krishiayan.api.main:app --reload --port 8000

dev:
	uvicorn krishiayan.api.main:app --reload --port 8000

frontend:
	cd frontend && npm install && npm run dev
