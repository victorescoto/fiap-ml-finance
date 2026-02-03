#!/bin/bash
# Script para destruir toda infraestrutura AWS do projeto FIAP Fase 4
# Execute: ./destroy-aws.sh

echo "Destruindo infraestrutura AWS FIAP Fase 4..."
echo "=================================================="

REGION="us-east-2"

# 1. Deletar Lambda functions
echo ""
echo "Deletando Lambda functions..."
aws lambda delete-function --function-name fiap-fase4-api --region $REGION 2>/dev/null && echo "OK: fiap-fase4-api deletada"
aws lambda delete-function --function-name fiap-fase4-job --region $REGION 2>/dev/null && echo "OK: fiap-fase4-job deletada"

# 2. Esvaziar e deletar S3 buckets
echo ""
echo "Deletando S3 buckets..."
aws s3 rb s3://fiap-fase4-athena-output --force 2>/dev/null && echo "OK: fiap-fase4-athena-output deletado"
aws s3 rb s3://fiap-fase4-finance-models --force 2>/dev/null && echo "OK: fiap-fase4-finance-models deletado"
aws s3 rb s3://fiap-fase4-finance-raw --force 2>/dev/null && echo "OK: fiap-fase4-finance-raw deletado"
aws s3 rb s3://fiap-fase4-finance-site --force 2>/dev/null && echo "OK: fiap-fase4-finance-site deletado"

# 3. Deletar imagens ECR e repositorio
echo ""
echo "Deletando ECR repository..."
aws ecr delete-repository --repository-name fiap-fase4-api --region $REGION --force 2>/dev/null && echo "OK: ECR repo deletado"

# 4. Deletar API Gateway
echo ""
echo "Deletando API Gateway..."
API_ID=$(aws apigatewayv2 get-apis --region $REGION --query "Items[?Name=='fiap-fase4-http'].ApiId" --output text 2>/dev/null)
if [ -n "$API_ID" ] && [ "$API_ID" != "None" ]; then
    aws apigatewayv2 delete-api --api-id $API_ID --region $REGION && echo "OK: API Gateway deletado"
fi

# 5. Deletar CloudWatch Log Groups
echo ""
echo "Deletando Log Groups..."
aws logs delete-log-group --log-group-name /aws/lambda/fiap-fase4-api --region $REGION 2>/dev/null && echo "OK: Logs API deletados"
aws logs delete-log-group --log-group-name /aws/lambda/fiap-fase4-job --region $REGION 2>/dev/null && echo "OK: Logs Job deletados"

# 6. CloudFront - precisa desabilitar primeiro
echo ""
echo "CloudFront precisa ser deletado manualmente:"
echo "  1. Acesse: https://console.aws.amazon.com/cloudfront/"
echo "  2. Selecione a distribution E3PJF2PKJVP4RU"
echo "  3. Clique em Disable"
echo "  4. Aguarde 15 minutos"
echo "  5. Clique em Delete"

echo ""
echo "=================================================="
echo "Limpeza concluida!"
echo ""
echo "Para usar Terraform (mais completo):"
echo "  cd infra/terraform && terraform destroy"
