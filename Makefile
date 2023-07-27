.PHONY: format
format:
	black .

.PHONY: lint
lint:
	ruff check .

.PHONY: dev
dev:
	uvicorn main:app --reload

.PHONY: test
test:
	pytest
