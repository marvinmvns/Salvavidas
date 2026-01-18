# 🐳 Salvavidas Docker Deployment

Infraestrutura Docker completa para deploy do Salvavidas em produção.

---

## 📋 Índice

- [Visão Geral](#visão-geral)
- [Arquitetura](#arquitetura)
- [Pré-requisitos](#pré-requisitos)
- [Início Rápido](#início-rápido)
- [Configuração](#configuração)
- [Comandos](#comandos)
- [Ambientes](#ambientes)
- [Monitoramento](#monitoramento)
- [Troubleshooting](#troubleshooting)
- [Produção](#produção)

---

## 🎯 Visão Geral

Este diretório contém toda a infraestrutura Docker para deploy do Salvavidas:

```
docker/
├── backend/
│   └── Dockerfile          # Backend Python/FastAPI
├── nginx/
│   └── nginx.conf          # Reverse proxy configuration
├── docker-compose.yml      # Orquestração principal
├── docker-compose.prod.yml # Overrides para produção
├── .env.example            # Template de variáveis de ambiente
├── build.sh                # Script de build
├── deploy.sh               # Script de deploy
└── README.md               # Esta documentação
```

---

## 🏗️ Arquitetura

### Serviços

**Backend (FastAPI):**
- Python 3.10
- FastAPI + Uvicorn
- WebSocket support
- 4 workers (8 em produção)
- Auto-restart
- Health checks

**Nginx (Reverse Proxy):**
- Alpine Linux
- Load balancer
- Static file serving
- WebSocket proxy
- Gzip compression
- Security headers

**PostgreSQL (Opcional):**
- Habilitado em produção
- Dados persistentes
- Auto-backup

**Redis (Opcional):**
- Cache layer
- Session storage
- Pub/Sub para WebSockets

### Network

```
┌─────────────────────────────────────────────┐
│              Internet                       │
└────────────────┬────────────────────────────┘
                 │
       ┌─────────▼─────────┐
       │    Nginx :80/443   │
       │  Reverse Proxy     │
       └─────────┬──────────┘
                 │
    ┌────────────┴────────────┐
    │                         │
┌───▼────┐              ┌─────▼────┐
│Backend │◄─────────────┤WebSocket │
│  :8000 │              │          │
└───┬────┘              └──────────┘
    │
    ├──────┬──────────┬──────────┐
    │      │          │          │
┌───▼──┐ ┌▼────┐  ┌──▼───┐  ┌──▼────┐
│Volumes│ │Redis│  │Postgres│ │Models │
└──────┘ └─────┘  └───────┘  └───────┘
```

---

## 📦 Pré-requisitos

### Sistema Operacional
- Linux (Ubuntu 20.04+, Debian 11+, CentOS 8+)
- macOS 11+
- Windows 10+ com WSL2

### Software Necessário

**Docker:**
```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# macOS
brew install docker
```

**Docker Compose:**
```bash
# Linux
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# macOS (já incluído no Docker Desktop)
```

**Verificar instalação:**
```bash
docker --version        # Docker 20.10+
docker-compose --version  # v2.0+
```

### Hardware Recomendado

**Desenvolvimento:**
- CPU: 4 cores
- RAM: 8 GB
- Disco: 20 GB

**Produção:**
- CPU: 8 cores
- RAM: 16 GB
- Disco: 50 GB
- GPU: Opcional (NVIDIA com CUDA para Whisper local)

---

## 🚀 Início Rápido

### 1. Clone o repositório

```bash
git clone https://github.com/marvinmvns/Salvavidas.git
cd Salvavidas/docker
```

### 2. Configure as variáveis de ambiente

```bash
# Copiar template
cp .env.example .env

# Editar configurações
nano .env
```

**Configurações mínimas:**
```env
PROCESSING_MODE=local
TARGET_LANGUAGE=en
```

### 3. Build das imagens

```bash
# Tornar scripts executáveis
chmod +x build.sh deploy.sh

# Build (primeira vez)
./build.sh local
```

### 4. Iniciar serviços

```bash
./deploy.sh start
```

### 5. Verificar status

```bash
./deploy.sh status
./deploy.sh health
```

### 6. Acessar aplicação

- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs
- **Frontend:** http://localhost (se nginx habilitado)

---

## ⚙️ Configuração

### Arquivo .env

Edite `.env` com suas configurações:

```env
# Modo de processamento
PROCESSING_MODE=local  # local | fast | premium

# Modelos de IA (PROCESSING_MODE=local)
WHISPER_MODEL=large-v3  # Whisper v3-turbo para STT
SKIP_MODEL_DOWNLOAD=false  # Pular download automático de modelos

# API Keys (opcionais)
OPENAI_API_KEY=sk-xxxxx
DEEPGRAM_API_KEY=xxxxx
HUGGINGFACE_TOKEN=hf_xxxxx

# Configurações da aplicação
TARGET_LANGUAGE=en
ENABLE_SPEAKER_ID=true
ENABLE_SUGGESTIONS=true
```

### 🤖 Download Automático de Modelos

Quando `PROCESSING_MODE=local`, o Docker baixa automaticamente os modelos de IA necessários:

**Modelos baixados:**
- **Whisper large-v3** (~1.5GB) - Speech-to-Text
- **Helsinki-NLP/opus-mt-en-pt** (~500MB) - Tradução
- **Pyannote embedding** (~200MB) - Identificação de falantes
- **Llama-2-7B-Chat** (~4GB) - LLM local
- **Piper TTS voice** (~50MB) - Text-to-Speech

**Total:** ~6-7GB de modelos

O download ocorre automaticamente no **primeiro start** do container:

```bash
# Logs mostram o download
docker-compose logs -f backend

🤖 Salvavidas Model Downloader
📦 Processing mode: local
📁 Models directory: /app/data/models

[1/5] Whisper v3-turbo (STT)
📥 Downloading Whisper model: large-v3...
✅ Whisper large-v3 downloaded successfully!

[2/5] Translation
📥 Downloading Translation model...
✅ Translation model downloaded successfully!

...
✅ Model download complete!
```

**Configurações:**

```env
# Usar Whisper base (menor, mais rápido)
WHISPER_MODEL=base

# Usar Whisper large-v3 (melhor qualidade - PADRÃO)
WHISPER_MODEL=large-v3

# Pular download (se já tiver os modelos)
SKIP_MODEL_DOWNLOAD=true
```

**Volumes persistentes:**
Os modelos são salvos no volume `model-cache` e **não precisam ser baixados novamente** em restarts.

### Portas

Por padrão:
- `8000` - Backend FastAPI
- `80` - Nginx (opcional)
- `443` - Nginx HTTPS (com certificado)

Para alterar:
```yaml
# Em docker-compose.yml
services:
  backend:
    ports:
      - "8080:8000"  # Porta customizada
```

### Volumes Persistentes

Dados são salvos em volumes Docker:

```bash
# Listar volumes
docker volume ls | grep salvavidas

# Backup de um volume
docker run --rm -v salvavidas_speaker-data:/data -v $(pwd):/backup ubuntu tar cvf /backup/speakers-backup.tar /data

# Restore
docker run --rm -v salvavidas_speaker-data:/data -v $(pwd):/backup ubuntu tar xvf /backup/speakers-backup.tar -C /
```

---

## 🎮 Comandos

### Deploy Script (`./deploy.sh`)

```bash
# Iniciar todos os serviços
./deploy.sh start

# Parar serviços
./deploy.sh stop

# Reiniciar serviços
./deploy.sh restart

# Ver status
./deploy.sh status

# Ver logs (últimas 100 linhas)
./deploy.sh logs

# Seguir logs em tempo real
./deploy.sh logs -f

# Abrir shell no container backend
./deploy.sh shell

# Verificar saúde dos serviços
./deploy.sh health

# Atualizar aplicação
./deploy.sh update

# Limpar tudo (CUIDADO!)
./deploy.sh clean
```

### Build Script (`./build.sh`)

```bash
# Build local (desenvolvimento)
./build.sh local

# Build para produção
./build.sh production

# Build rápido (usa cache)
./build.sh fast
```

### Docker Compose Direto

```bash
# Iniciar em background
docker-compose up -d

# Iniciar com logs
docker-compose up

# Parar serviços
docker-compose stop

# Parar e remover containers
docker-compose down

# Ver logs de um serviço específico
docker-compose logs -f backend

# Executar comando em container
docker-compose exec backend python --version

# Rebuild de um serviço
docker-compose build backend

# Escalar serviço
docker-compose up -d --scale backend=3
```

---

## 🌍 Ambientes

### Desenvolvimento (Local)

```bash
# Build e start
./build.sh local
./deploy.sh start

# Ver logs
./deploy.sh logs -f

# Hot reload (mount code as volume)
# Edite docker-compose.yml:
volumes:
  - ../src:/app/src
  - ../frontend:/app/frontend
```

### Staging

```bash
# Mesmo que produção mas com menos recursos
docker-compose -f docker-compose.yml up -d
```

### Produção

```bash
# Build para produção
./build.sh production

# Iniciar com overrides de produção
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Verificar saúde
./deploy.sh health

# Monitorar logs
./deploy.sh logs -f
```

**Diferenças de produção:**
- 8 workers (vs 4)
- PostgreSQL habilitado
- Redis habilitado
- Logging otimizado
- Mais recursos (CPU/RAM)
- Restart policies
- Health checks agressivos

---

## 📊 Monitoramento

### Health Checks

Backend tem endpoint de saúde:

```bash
# Via curl
curl http://localhost:8000/health

# Via deploy script
./deploy.sh health
```

Resposta:
```json
{
  "status": "healthy",
  "timestamp": "2026-01-18T10:30:00Z",
  "services": {
    "stt": "ready",
    "translation": "ready",
    "speaker_id": "ready"
  }
}
```

### Logs

```bash
# Todos os serviços
docker-compose logs -f

# Apenas backend
docker-compose logs -f backend

# Últimas 50 linhas
docker-compose logs --tail=50 backend

# Desde uma data
docker-compose logs --since="2026-01-18T10:00:00"
```

### Métricas

```bash
# Stats em tempo real
docker stats

# Stats de um container específico
docker stats salvavidas-backend
```

### Prometheus + Grafana (Futuro)

Template para monitoring stack:

```yaml
# docker-compose.monitoring.yml
services:
  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    volumes:
      - grafana-data:/var/lib/grafana
```

---

## 🔧 Troubleshooting

### Container não inicia

```bash
# Ver logs
docker-compose logs backend

# Ver status detalhado
docker-compose ps

# Inspecionar container
docker inspect salvavidas-backend
```

### Problemas de porta

```bash
# Verificar portas em uso
sudo lsof -i :8000

# Matar processo ocupando porta
sudo kill -9 <PID>

# Alterar porta no docker-compose.yml
```

### Problemas de memória

```bash
# Ver uso de memória
docker stats

# Aumentar limite em docker-compose.yml
deploy:
  resources:
    limits:
      memory: 16G
```

### Rebuild completo

```bash
# Parar tudo
./deploy.sh stop

# Remover containers e volumes
./deploy.sh clean

# Rebuild do zero
./build.sh local

# Restart
./deploy.sh start
```

### Logs não aparecem

```bash
# Verificar driver de logging
docker inspect salvavidas-backend | grep LogConfig

# Alterar para json-file em docker-compose.yml
logging:
  driver: "json-file"
```

### Conexão WebSocket falha

```bash
# Verificar nginx config
docker-compose exec nginx nginx -t

# Reload nginx
docker-compose exec nginx nginx -s reload

# Ver logs nginx
docker-compose logs -f nginx
```

---

## 🏭 Produção

### Checklist de Deploy

- [ ] `.env` configurado corretamente
- [ ] API keys configuradas (se necessário)
- [ ] SSL/TLS certificates instalados
- [ ] Firewall configurado (portas 80, 443)
- [ ] DNS apontando para servidor
- [ ] Backup automático configurado
- [ ] Monitoring habilitado
- [ ] Logs rotacionados
- [ ] Health checks funcionando

### SSL/TLS (HTTPS)

#### Opção 1: Let's Encrypt (Certbot)

```bash
# Instalar certbot
sudo apt-get install certbot python3-certbot-nginx

# Obter certificado
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Copiar para pasta nginx
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem docker/nginx/ssl/cert.pem
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem docker/nginx/ssl/key.pem

# Descomentar bloco HTTPS em nginx.conf
# Restart nginx
docker-compose restart nginx
```

#### Opção 2: Certificado próprio

```bash
# Gerar certificado self-signed (desenvolvimento)
mkdir -p nginx/ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx/ssl/key.pem \
  -out nginx/ssl/cert.pem
```

### Backup Automático

Crie um cron job:

```bash
# Editar crontab
crontab -e

# Adicionar backup diário às 3am
0 3 * * * /path/to/Salvavidas/docker/backup.sh

# Criar script de backup
cat > backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR=/backups/salvavidas
DATE=$(date +%Y%m%d_%H%M%S)

# Backup volumes
docker run --rm \
  -v salvavidas_speaker-data:/data \
  -v $BACKUP_DIR:/backup \
  ubuntu tar czf /backup/speakers-$DATE.tar.gz /data

# Backup database (se PostgreSQL habilitado)
docker-compose exec -T postgres pg_dump -U salvavidas salvavidas | gzip > $BACKUP_DIR/db-$DATE.sql.gz

# Manter apenas últimos 7 dias
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
find $BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete
EOF

chmod +x backup.sh
```

### Scaling

#### Horizontal Scaling (Load Balancing)

```bash
# Escalar backend para 4 instâncias
docker-compose up -d --scale backend=4

# Nginx automaticamente faz load balancing
```

#### Vertical Scaling (Mais recursos)

```yaml
# Em docker-compose.prod.yml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '16.0'
          memory: 32G
```

### Monitoring em Produção

Ferramentas recomendadas:
- **Prometheus + Grafana** - Métricas
- **ELK Stack** - Logs centralizados
- **Sentry** - Error tracking
- **Uptime Robot** - Monitoring externo

### CI/CD Pipeline

Exemplo GitLab CI:

```yaml
# .gitlab-ci.yml
stages:
  - build
  - test
  - deploy

build:
  stage: build
  script:
    - cd docker
    - ./build.sh production
  only:
    - main

deploy-production:
  stage: deploy
  script:
    - ssh user@server 'cd /app/Salvavidas && git pull && cd docker && ./deploy.sh update'
  only:
    - main
  when: manual
```

---

## 📝 Notas

### Segurança

- **Nunca commitar** `.env` com secrets
- Usar **secrets managers** em produção (Vault, AWS Secrets Manager)
- Manter **Docker atualizado**
- **Escanear imagens** regularmente (`docker scan`)
- Usar **networks isoladas** para serviços

### Performance

- **Multi-stage builds** para imagens menores
- **Layer caching** para builds rápidos
- **Health checks** para auto-recovery
- **Resource limits** para evitar OOM
- **Log rotation** para economizar espaço

### Best Practices

- Um serviço por container
- Usar volumes nomeados (não bind mounts em produção)
- Environment variables para configuração
- Logs para stdout/stderr
- Graceful shutdown handling
- Health checks em todos os serviços

---

## 🆘 Suporte

**Documentação:**
- [Docker Docs](https://docs.docker.com/)
- [Docker Compose Docs](https://docs.docker.com/compose/)
- [Salvavidas Main README](../README.md)

**Problemas:**
- GitHub Issues: https://github.com/marvinmvns/Salvavidas/issues
- Email: suporte@salvavidas.com

---

## 📄 Licença

MIT License - Ver [LICENSE](../LICENSE) para detalhes.

---

**🎉 Pronto! Seu Salvavidas está dockerizado e pronto para produção!**
