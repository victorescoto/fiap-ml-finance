PY=python3
PIP=pip
UVICORN=uvicorn

SYMBOLS="AAPL,MSFT,AMZN,GOOGL,META,NVDA,TSLA"
REGION="us-east-1"
PREFIX="fiap-fase3"

.PHONY: deps run-api ingest-1d-local ingest-5m-local train-local tf-init tf-apply tf-destroy fmt

deps:
	python3 -m pip install --upgrade pip
	python3 -m pip install -r requirements.txt || true
	python3 -m pip install -e . || true

run-api:
	uvicorn app.fastapi_app.main:app --reload --port 8000

ingest-1d-local:
	$(PY) app/jobs/ingest_1d.py --symbols $(SYMBOLS) --out ./data --to s3://$(PREFIX)-finance-raw --dry-run

ingest-5m-local:
	$(PY) app/jobs/ingest_5m.py --symbols $(SYMBOLS) --out ./data --to s3://$(PREFIX)-finance-raw --dry-run

train-local:
	$(PY) app/jobs/train_daily.py --symbols $(SYMBOLS) --data ./data --models ./models --dry-run

tf-init:
	cd infra/terraform && terraform init

tf-apply:
	cd infra/terraform && terraform apply -auto-approve -var='aws_region=$(REGION)' -var='prefix=$(PREFIX)'

tf-destroy:
	cd infra/terraform && terraform destroy -auto-approve -var='aws_region=$(REGION)' -var='prefix=$(PREFIX)'

fmt:
	cd infra/terraform && terraform fmt -recursive
