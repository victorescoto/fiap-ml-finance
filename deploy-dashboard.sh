#!/bin/bash

# FIAP Finance Dashboard Deploy Script
# Simplifica o deploy de alterações no dashboard

set -e  # Exit on any error

# Configurações
S3_BUCKET="fiap-fase3-finance-site"
CLOUDFRONT_ID="E2JS6B4CESU8N8"
DASHBOARD_URL="https://d1cvtgdwi1a5l6.cloudfront.net"
DASHBOARD_DIR="dashboard"

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Funções utilitárias
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Verificar se AWS CLI está configurado
check_aws() {
    if ! aws sts get-caller-identity &> /dev/null; then
        log_error "AWS CLI não está configurado ou sem permissões"
        exit 1
    fi
}

# Verificar se arquivos do dashboard existem
check_files() {
    if [ ! -d "$DASHBOARD_DIR" ]; then
        log_error "Diretório '$DASHBOARD_DIR' não encontrado"
        exit 1
    fi
    
    if [ ! -f "$DASHBOARD_DIR/index.html" ]; then
        log_error "Arquivo index.html não encontrado em $DASHBOARD_DIR"
        exit 1
    fi
    
    if [ ! -f "$DASHBOARD_DIR/app.js" ]; then
        log_error "Arquivo app.js não encontrado em $DASHBOARD_DIR"
        exit 1
    fi
}

# Deploy completo
deploy_full() {
    log_info "Iniciando deploy completo do dashboard..."
    
    log_info "Sincronizando arquivos com S3..."
    aws s3 sync "$DASHBOARD_DIR/" "s3://$S3_BUCKET/" --delete \
        --exclude "*.tmp" --exclude ".DS_Store" --exclude "*.swp"
    
    log_info "Invalidando cache do CloudFront..."
    INVALIDATION_ID=$(aws cloudfront create-invalidation \
        --distribution-id "$CLOUDFRONT_ID" \
        --paths "/*" \
        --query 'Invalidation.Id' --output text)
    
    log_success "Deploy completo realizado!"
    log_info "Invalidation ID: $INVALIDATION_ID"
    log_success "Dashboard disponível em: $DASHBOARD_URL"
}

# Deploy apenas JavaScript
deploy_js() {
    log_info "Fazendo deploy apenas dos arquivos JavaScript/CSS..."
    
    aws s3 cp "$DASHBOARD_DIR/app.js" "s3://$S3_BUCKET/app.js"
    
    if [ -f "$DASHBOARD_DIR/styles.css" ]; then
        aws s3 cp "$DASHBOARD_DIR/styles.css" "s3://$S3_BUCKET/styles.css"
        PATHS="/app.js /styles.css"
    else
        PATHS="/app.js"
    fi
    
    log_info "Invalidando cache dos arquivos JS/CSS..."
    aws cloudfront create-invalidation \
        --distribution-id "$CLOUDFRONT_ID" \
        --paths $PATHS > /dev/null
    
    log_success "Arquivos JavaScript/CSS atualizados!"
    log_success "Dashboard disponível em: $DASHBOARD_URL"
}

# Deploy apenas HTML
deploy_html() {
    log_info "Fazendo deploy apenas do arquivo HTML..."
    
    aws s3 cp "$DASHBOARD_DIR/index.html" "s3://$S3_BUCKET/index.html"
    
    log_info "Invalidando cache do HTML..."
    aws cloudfront create-invalidation \
        --distribution-id "$CLOUDFRONT_ID" \
        --paths "/index.html" "/" > /dev/null
    
    log_success "Arquivo HTML atualizado!"
    log_success "Dashboard disponível em: $DASHBOARD_URL"
}

# Verificar status
check_status() {
    log_info "Verificando status do dashboard..."
    echo ""
    
    echo "📊 Configuração:"
    echo "   S3 Bucket: $S3_BUCKET"
    echo "   CloudFront ID: $CLOUDFRONT_ID"
    echo "   Dashboard URL: $DASHBOARD_URL"
    echo ""
    
    echo "📁 Arquivos no S3:"
    if aws s3 ls "s3://$S3_BUCKET/" &> /dev/null; then
        aws s3 ls "s3://$S3_BUCKET/" | while read -r line; do
            echo "   $line"
        done
    else
        log_error "Não foi possível acessar o bucket S3"
    fi
    echo ""
    
    echo "🌐 Status do CloudFront:"
    HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$DASHBOARD_URL")
    if [ "$HTTP_STATUS" = "200" ]; then
        log_success "Dashboard acessível (HTTP $HTTP_STATUS)"
    else
        log_warning "Dashboard retornou HTTP $HTTP_STATUS"
    fi
}

# Ajuda
show_help() {
    echo "🚀 FIAP Finance Dashboard Deploy"
    echo ""
    echo "Uso: $0 [COMANDO]"
    echo ""
    echo "Comandos disponíveis:"
    echo "  full, all     Deploy completo (todos os arquivos)"
    echo "  js, css       Deploy apenas JavaScript/CSS"
    echo "  html          Deploy apenas HTML"
    echo "  status        Verificar status do dashboard"
    echo "  help          Mostrar esta ajuda"
    echo ""
    echo "Exemplos:"
    echo "  $0 full       # Deploy completo"
    echo "  $0 js         # Atualizar apenas JavaScript"
    echo "  $0 status     # Verificar status"
    echo ""
    echo "🔗 Dashboard: $DASHBOARD_URL"
}

# Main
main() {
    echo "🚀 FIAP Finance Dashboard Deploy Script"
    echo ""
    
    # Verificações iniciais
    check_aws
    check_files
    
    # Processar comando
    case "${1:-full}" in
        "full"|"all")
            deploy_full
            ;;
        "js"|"css"|"javascript")
            deploy_js
            ;;
        "html")
            deploy_html
            ;;
        "status"|"check")
            check_status
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            log_error "Comando desconhecido: $1"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# Executar script
main "$@"