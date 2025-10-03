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
REGION?=us-east-2
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

# ==================== DOCKER & ECR ====================
AWS_ACCOUNT_ID=$(shell aws sts get-caller-identity --query Account --output text)
ECR_REGISTRY=$(AWS_ACCOUNT_ID).dkr.ecr.$(REGION).amazonaws.com
API_IMAGE=$(ECR_REGISTRY)/$(PREFIX)-api:latest
JOB_IMAGE=$(ECR_REGISTRY)/$(PREFIX)-job:latest

docker-build-api:
	docker build -f Dockerfile.api -t $(PREFIX)-api .
	docker tag $(PREFIX)-api:latest $(API_IMAGE)

docker-build-job:
	docker build -f Dockerfile.job -t $(PREFIX)-job .
	docker tag $(PREFIX)-job:latest $(JOB_IMAGE)

docker-build: docker-build-api docker-build-job

ecr-login:
	aws ecr get-login-password --region $(REGION) | docker login --username AWS --password-stdin $(ECR_REGISTRY)

ecr-push-api: ecr-login docker-build-api
	docker push $(API_IMAGE)

ecr-push-job: ecr-login docker-build-job
	docker push $(JOB_IMAGE)

ecr-push: ecr-push-api ecr-push-job

# Deploy completo: terraform + docker images
deploy: tf-apply ecr-push
	@echo "✅ Deploy completo realizado!"
	@echo "🔗 API URL: https://$(shell cd infra/terraform && terraform output -raw api_gateway_url)/docs"

# Limpar recursos Docker locais
docker-clean:
	docker rmi -f $(PREFIX)-api $(PREFIX)-job $(API_IMAGE) $(JOB_IMAGE) 2>/dev/null || true

# ==================== DASHBOARD DEPLOY ====================
S3_BUCKET?=fiap-fase3-finance-site
CLOUDFRONT_ID?=E2JS6B4CESU8N8

# Deploy rápido do dashboard (só arquivos alterados)
dashboard-deploy:
	@echo "🚀 Deploying dashboard files to S3..."
	aws s3 sync dashboard/ s3://$(S3_BUCKET)/ --delete --exclude "*.tmp" --exclude ".DS_Store"
	@echo "♻️  Invalidating CloudFront cache..."
	aws cloudfront create-invalidation --distribution-id $(CLOUDFRONT_ID) --paths "/*" > /dev/null
	@echo "✅ Dashboard deployed successfully!"
	@echo "🔗 URL: https://d1cvtgdwi1a5l6.cloudfront.net"

# Deploy apenas arquivos JS/CSS (mais rápido para mudanças de código)
dashboard-deploy-js:
	@echo "🚀 Deploying JavaScript/CSS files..."
	aws s3 cp dashboard/app.js s3://$(S3_BUCKET)/app.js
	@test -f dashboard/styles.css && aws s3 cp dashboard/styles.css s3://$(S3_BUCKET)/styles.css || echo "No styles.css found"
	@echo "♻️  Invalidating JS/CSS cache..."
	aws cloudfront create-invalidation --distribution-id $(CLOUDFRONT_ID) --paths "/app.js" "/styles.css" > /dev/null
	@echo "✅ JavaScript/CSS deployed!"
	@echo "🔗 Test: https://d1cvtgdwi1a5l6.cloudfront.net"

# Deploy apenas HTML (para mudanças de layout)
dashboard-deploy-html:
	@echo "🚀 Deploying HTML files..."
	aws s3 cp dashboard/index.html s3://$(S3_BUCKET)/index.html
	@echo "♻️  Invalidating HTML cache..."
	aws cloudfront create-invalidation --distribution-id $(CLOUDFRONT_ID) --paths "/index.html" "/" > /dev/null
	@echo "✅ HTML deployed!"
	@echo "🔗 Test: https://d1cvtgdwi1a5l6.cloudfront.net"

# Verificar status do dashboard
dashboard-status:
	@echo "📊 Dashboard Status:"
	@echo "S3 Bucket: $(S3_BUCKET)"
	@echo "CloudFront ID: $(CLOUDFRONT_ID)"
	@echo ""
	@echo "📁 Files in S3:"
	@aws s3 ls s3://$(S3_BUCKET)/ || echo "❌ S3 bucket not accessible"
	@echo ""
	@echo "🌐 CloudFront Status:"
	@curl -I https://d1cvtgdwi1a5l6.cloudfront.net 2>/dev/null | head -1 || echo "❌ CloudFront not accessible"
	@echo ""
	@echo "🔗 Dashboard URL: https://d1cvtgdwi1a5l6.cloudfront.net"

# Ajuda para comandos do dashboard
dashboard-help:
	@echo "📋 Dashboard Deploy Commands:"
	@echo ""
	@echo "🚀 Deploy Commands:"
	@echo "  make dashboard-deploy       # Deploy completo (todos os arquivos)"
	@echo "  make dashboard-deploy-js    # Deploy apenas JS/CSS (mais rápido)"
	@echo "  make dashboard-deploy-html  # Deploy apenas HTML"
	@echo ""
	@echo "📊 Utility Commands:"
	@echo "  make dashboard-status       # Verificar status do dashboard"
	@echo "  make dashboard-help         # Mostrar esta ajuda"
	@echo ""
	@echo "🔗 Dashboard URL: https://d1cvtgdwi1a5l6.cloudfront.net"
