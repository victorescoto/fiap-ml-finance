# Carregar variáveis do .env se existir
ifneq (,$(wildcard ./.env))
    include .env
    export
endif

UV=uv
PY=uv run python
UVICORN=uv run uvicorn

# Usar variáveis do .env ou valores padrão
SYMBOLS?=AAPL,MSFT,AMZN,GOOGL,META,NVDA,TSLA
REGION?=us-east-1
PREFIX?=fiap-fase3
API_PORT?=8000
DATA_DIR?=./data
MODELS_DIR?=./models

.PHONY: deps run-api ingest-1d-local ingest-5m-local train-local tf-init tf-apply tf-destroy fmt

deps:
	uv sync

run-api:
	$(UVICORN) app.fastapi_app.main:app --reload --port $(API_PORT)

ingest-1d-local:
	$(PY) app/jobs/ingest_1d.py --out $(DATA_DIR) --dry-run

ingest-5m-local:
	$(PY) app/jobs/ingest_5m.py --out $(DATA_DIR) --dry-run

train-local:
	$(PY) app/jobs/train_daily.py --data $(DATA_DIR) --models $(MODELS_DIR) --dry-run

tf-init:
	cd infra/terraform && terraform init

tf-apply:
	cd infra/terraform && terraform apply -auto-approve -var='aws_region=$(REGION)' -var='prefix=$(PREFIX)'

tf-destroy:
	cd infra/terraform && terraform destroy -auto-approve -var='aws_region=$(REGION)' -var='prefix=$(PREFIX)'

fmt:
	cd infra/terraform && terraform fmt -recursive
