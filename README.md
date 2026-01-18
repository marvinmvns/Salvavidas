# 🚁 Salvavidas - Real-time Voice Translation

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Clean Architecture](https://img.shields.io/badge/Architecture-Clean-orange.svg)](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)

**Salvavidas** é uma aplicação de tradução de voz em tempo real com identificação de falantes e sugestões de respostas inteligentes. Desenvolvida com **Clean Architecture** e **MVC**, oferece processamento local ou via API com foco em **zero latência**.

## ✨ Características

### Core Features
- 🎤 **Reconhecimento de Voz em Tempo Real** (Whisper v3-turbo)
- 👥 **Identificação de Falantes** (Pyannote.audio - embeddings 512D)
- 🌍 **Tradução Multilíngue** (suporta 30+ idiomas)
- 🤖 **Sugestões Inteligentes de Resposta** (LLM)
- 🔊 **Síntese de Voz** (TTS)
- ⚡ **Zero Latência** (modo realtime otimizado)

### Plataformas
- 🖥️ **Frontend Web Parametrizável**
- 🖥️ **Desktop App** (Electron - Windows/Mac/Linux)
  - Captura de áudio do Teams (microfone + sistema)
  - Detecção automática de reuniões
  - Overlay invisível ao compartilhamento
- 🌐 **Chrome Extension** (Meet/Zoom/Teams)
- 📱 **Clientes IoT** (ESP32-S3, Android)

### Analytics & Deployment
- 📊 **Analytics Dashboard** (estatísticas real-time)
- 🐳 **Docker Ready** (deploy em 1 comando)
- 💾 **Banco SQLite para Configurações**
- 🎯 **Clean Architecture + MVC**
- 🧪 **100% Testado**

## 🏗️ Arquitetura

```
┌─────────────────────────────────────────────────────────┐
│                     FRONTEND WEB                        │
│              (HTML + JS + WebSocket)                    │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                    ADAPTERS LAYER                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ Controllers  │  │  Presenters  │  │   Gateways   │  │
│  │    (MVC)     │  │    (API)     │  │              │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                    CORE/DOMAIN LAYER                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   Entities   │  │  Use Cases   │  │  Interfaces  │  │
│  │              │  │              │  │   (Ports)    │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                 INFRASTRUCTURE LAYER                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐│
│  │   STT    │  │   TTS    │  │  Speaker │  │   LLM   ││
│  │ Services │  │ Services │  │    ID    │  │ Services││
│  └──────────┘  └──────────┘  └──────────┘  └─────────┘│
│  ┌──────────┐  ┌──────────┐  ┌──────────────────────┐ │
│  │Translat. │  │ Database │  │   Service Factory    │ │
│  │ Services │  │ (SQLite) │  │                      │ │
│  └──────────┘  └──────────┘  └──────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

## 📦 Estrutura do Projeto

```
Salvavidas/
├── src/
│   ├── core/                          # Clean Architecture - Domain
│   │   ├── entities/                 # Entidades do domínio
│   │   ├── use_cases/                # Casos de uso
│   │   └── interfaces/               # Interfaces (Ports)
│   ├── adapters/                     # Clean Architecture - Adapters
│   │   ├── controllers/              # MVC - Controllers
│   │   ├── presenters/               # MVC - Views/Presenters (API)
│   │   └── gateways/
│   └── infrastructure/               # Clean Architecture - Infrastructure
│       ├── services/
│       │   ├── stt/                 # Speech-to-Text (Whisper v3)
│       │   ├── tts/                 # Text-to-Speech (Piper)
│       │   ├── speaker_id/          # Speaker ID (Pyannote)
│       │   ├── speaker_management/  # Speaker enrollment/recognition
│       │   ├── translation/         # Translation
│       │   ├── llm/                 # Language Models
│       │   ├── sentiment/           # Sentiment Analysis
│       │   ├── analytics/           # Analytics Dashboard
│       │   ├── argumentation/       # Argumentation Engine
│       │   └── meeting_summary/     # Meeting Summary
│       ├── models/                  # MVC - Models (Database)
│       ├── database.py
│       └── service_factory.py
├── frontend/                         # Frontend Web
│   ├── index.html
│   ├── app.js
│   ├── analytics.html               # Analytics Dashboard
│   ├── analytics.js
│   ├── index_premium.html
│   └── app_premium.js
├── desktop-app/                      # Desktop App (Electron)
│   ├── main.js                      # Main process
│   ├── renderer.js                  # Renderer process
│   ├── src/
│   │   ├── audio-capture.js         # Teams audio capture
│   │   ├── audio-client.js          # WebSocket client
│   │   └── teams-detector.js        # Teams detection
│   ├── package.json
│   └── README.md
├── chrome-extension/                 # Chrome Extension
│   ├── manifest.json
│   ├── background/
│   │   └── service-worker.js
│   ├── content/
│   │   ├── content.js
│   │   └── overlay.css
│   ├── popup/
│   │   ├── popup.html
│   │   └── popup.js
│   └── README.md
├── esp32-client/                     # ESP32-S3 Firmware (WIP)
│   ├── main.c
│   ├── audio_capture.c
│   └── README.md
├── android-client/                   # Android App (WIP)
│   ├── app/
│   └── README.md
├── docker/                           # Docker Deployment
│   ├── backend/
│   │   ├── Dockerfile
│   │   ├── download-models.py       # Auto model downloader
│   │   └── entrypoint.sh            # Startup script
│   ├── nginx/
│   │   └── nginx.conf
│   ├── docker-compose.yml
│   ├── docker-compose.prod.yml
│   ├── deploy.sh                    # Deployment script
│   └── README.md                     # Docker docs
├── tests/                            # Testes
│   ├── unit/
│   └── integration/
├── config/                           # Configurações
├── main.py                           # Ponto de entrada
└── requirements.txt
```

## 🚀 Instalação

### 🐳 Opção 1: Docker (Recomendado)

A maneira mais rápida de colocar o Salvavidas em produção:

```bash
# Clone o repositório
git clone https://github.com/marvinmvns/Salvavidas.git
cd Salvavidas/docker

# Configure
cp .env.example .env
# Edite .env se necessário

# Build e Start (1 comando!)
./deploy.sh start
```

**Recursos do Docker:**
- ✅ Download automático de modelos de IA (~6-7GB no primeiro start)
- ✅ Whisper v3-turbo pré-configurado
- ✅ Todos os serviços configurados
- ✅ Volumes persistentes para dados
- ✅ Health checks automáticos
- ✅ Pronto para produção

Acesse: `http://localhost:8000`

Ver [docker/README.md](docker/README.md) para documentação completa.

---

### 🐍 Opção 2: Instalação Manual

#### Pré-requisitos

- Python 3.10+
- Pip
- (Opcional) GPU Intel para aceleração local

### 1. Clone o repositório

```bash
git clone https://github.com/marvinmvns/Salvavidas.git
cd Salvavidas
```

### 2. Crie um ambiente virtual

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Configure as variáveis de ambiente

```bash
cp .env.example .env
# Edite .env com suas API keys (se usar modo API)
```

## ⚙️ Configuração

### Modos de Processamento

#### 1. **Local** (Gratuito) ⭐
- **STT**: Whisper v3-turbo (large-v3 via faster-whisper)
- **TTS**: Piper
- **Translation**: Helsinki-NLP models
- **LLM**: Llama.cpp (Llama-2-7B-Chat)
- **Speaker ID**: Pyannote.audio (embeddings 512D)
- ⚡ **GPU Intel**: Suportado via OpenVINO/oneAPI
- 📦 **Download Automático**: Modelos baixados automaticamente (~6-7GB)

#### 2. **API Fast** ($$)
- **STT**: Deepgram Nova
- **TTS**: ElevenLabs
- **Translation**: DeepL
- **LLM**: GPT-3.5 Turbo
- **Speaker ID**: Pyannote (local)

#### 3. **API Premium** ($$$)
- **STT**: Deepgram Nova-2
- **TTS**: ElevenLabs Turbo v2
- **Translation**: DeepL Pro
- **LLM**: GPT-4 Turbo
- **Speaker ID**: Pyannote (local)

## 🎮 Uso

### Modo Web (Recomendado)

```bash
python main.py web
```

Acesse: http://localhost:8000

### Modo CLI (Testes)

```bash
python main.py cli
```

### Opções

```bash
python main.py web --host 0.0.0.0 --port 8000 --reload
```

## 🧪 Testes

### Executar todos os testes

```bash
pytest
```

### Executar apenas testes unitários

```bash
pytest tests/unit/
```

### Executar com cobertura

```bash
pytest --cov=src --cov-report=html
```

## 🖥️ Plataformas Disponíveis

### Web Application (Principal)
```bash
python main.py web
# Acesse: http://localhost:8000
```

A aplicação web oferece 3 versões de interface:
- **Basic** (`index.html`) - Interface simples e leve
- **Optimized** (`app_optimized.js`) - Performance otimizada
- **Premium** (`index_premium.html`) - Todas as funcionalidades

### Desktop App (Electron)
```bash
cd desktop-app
npm install
npm start
```

**Características:**
- ✅ Overlay sempre visível
- ✅ Invisível ao compartilhamento de tela
- ✅ Atalhos globais (Ctrl+Shift+O/I/H)
- ✅ Multi-platform (Windows/Mac/Linux)
- ✅ WebSocket para backend
- ✅ System tray integration

**Teams Integration:**
- 🎤 **Captura de áudio dupla**: Microfone + Sistema (outros participantes)
- 🔍 **Detecção automática**: Identifica reuniões do Teams (Windows/Mac/Linux)
- 🎯 **Sem interferência**: Não afeta a chamada original
- 📊 **Transcrição real-time**: Durante a reunião com speaker identification

Ver [desktop-app/README.md](desktop-app/README.md) para documentação completa.

### Chrome Extension
```bash
# 1. Certifique-se que o backend está rodando
python main.py web

# 2. Carregue a extensão no Chrome
# - Abra chrome://extensions/
# - Ative "Modo do desenvolvedor"
# - Clique em "Carregar sem compactação"
# - Selecione a pasta chrome-extension/
```

**Plataformas suportadas:**
- ✅ Google Meet
- ✅ Zoom
- ✅ Microsoft Teams

**Características:**
- ✅ Overlay injected em reuniões
- ✅ Captura de áudio da aba
- ✅ Transcrição em tempo real
- ✅ Análise de sentimento
- ✅ Sugestões de resposta
- ✅ Invisível ao screen sharing

Ver [chrome-extension/README.md](chrome-extension/README.md) para documentação completa.

### IoT Clients (WIP)

#### ESP32-S3 (Firmware)
Cliente nativo para captura de áudio de alta qualidade:
- I2S para áudio digital
- WebSocket para streaming
- Latência mínima (~50ms)
- Modo "servo" (apenas captura, sem processamento)

#### Android App (Kotlin)
Aplicativo Android para streaming de áudio:
- AudioRecord API (baixa latência)
- OkHttp WebSocket client
- Background service
- Notificação persistente

**Arquitetura "Servo":**
- Dispositivos apenas capturam e transmitem áudio
- Zero processamento local
- Backend processa tudo (STT, Speaker ID, Translation)
- Ideal para dispositivos com recursos limitados

### Analytics Dashboard

Acesse: `http://localhost:8000/analytics.html`

**Métricas disponíveis:**
- 📊 **Transcrições**: Total, por idioma, por falante
- ⏱️ **Performance**: Latência média, tempo de processamento
- 👥 **Falantes**: Distribuição, tempo de fala, engajamento
- 🌍 **Idiomas**: Distribuição de idiomas detectados
- 📈 **Tendências**: Gráficos temporais de uso

Dados atualizados em tempo real via WebSocket.

## 🌐 API Endpoints

### Configuração

- `GET /api/config` - Obter todas as configurações
- `GET /api/config/{key}` - Obter configuração específica
- `POST /api/config` - Atualizar configuração
- `POST /api/config/reset` - Reset para padrões

### Falantes

- `GET /api/speakers` - Listar falantes conhecidos

### WebSocket

- `WS /ws/voice` - Streaming de áudio em tempo real

## 🛠️ Tecnologias

### Core
- Python 3.10+
- Pydantic (validação)
- SQLAlchemy (ORM)
- SQLite (banco de dados)

### Audio Processing
- PyAudio (captura)
- NumPy, SciPy (processamento)
- Librosa (análise)

### Local Services
- **Faster-Whisper** (STT) - Whisper v3-turbo (large-v3) com CTranslate2
- **Piper** (TTS) - TTS rápido local
- **Pyannote.audio** (Speaker ID) - Embeddings 512D para identificação
- **Helsinki-NLP** (Translation) - Modelos MarianMT
- **Llama.cpp** (LLM) - Llama-2-7B-Chat com quantização Q4

### API Services
- **Deepgram** (STT) - Ultra baixa latência
- **ElevenLabs** (TTS) - Qualidade premium
- **DeepL** (Translation) - Melhor tradução
- **OpenAI GPT-4** (LLM) - Sugestões inteligentes

### Web
- **FastAPI** - Framework web assíncrono
- **Uvicorn** - Servidor ASGI
- **WebSocket** - Comunicação em tempo real

### Intel GPU Optimization
- **Intel Extension for PyTorch** - Aceleração GPU
- **OpenVINO** - Otimização de modelos

## 📊 Performance

| Modo | STT Model | Latência STT | Latência Total | Custo |
|------|-----------|-------------|----------------|-------|
| Local | Whisper v3-turbo | ~400ms | ~800ms | $0 |
| API Fast | Deepgram Nova | ~300ms | ~500ms | ~$0.01/min |
| API Premium | Deepgram Nova-2 | ~200ms | ~300ms | ~$0.05/min |

**Speaker Identification:**
- Pyannote.audio: ~95% de acurácia com embeddings 512D
- Latência: ~50ms por identificação

**Docker vs Manual:**
- Docker: Setup em 5 minutos, modelos baixados automaticamente
- Manual: Requer instalação manual de cada dependência

## 🐳 Docker Deployment

### Quick Start

```bash
cd docker
./deploy.sh start
```

### Comandos Úteis

```bash
# Ver status
./deploy.sh status

# Ver logs
./deploy.sh logs -f

# Reiniciar
./deploy.sh restart

# Shell no container
./deploy.sh shell

# Health check
./deploy.sh health

# Parar tudo
./deploy.sh stop

# Limpar tudo (cuidado!)
./deploy.sh clean
```

### Configuração

```env
# docker/.env
PROCESSING_MODE=local
WHISPER_MODEL=large-v3        # ou 'base' para menor
SKIP_MODEL_DOWNLOAD=false      # true se já tem modelos
HUGGINGFACE_TOKEN=hf_xxxxx    # para Pyannote (gated model)
```

### Serviços

| Serviço | Porta | Descrição |
|---------|-------|-----------|
| Backend | 8000 | FastAPI + WebSocket |
| Nginx | 80/443 | Reverse proxy (opcional) |
| PostgreSQL | - | Database (opcional, produção) |
| Redis | - | Cache (opcional, produção) |

### Volumes Persistentes

```bash
salvavidas_speaker-data      # Perfis de falantes
salvavidas_analytics-data    # Dados de analytics
salvavidas_model-cache       # Modelos de IA (~6-7GB)
```

### Produção

```bash
# Build para produção
./build.sh production

# Start com overrides de produção
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

Ver [docker/README.md](docker/README.md) para documentação completa.

## 🔐 Segurança

- API keys armazenadas em `.env`
- Banco SQLite local
- Sem armazenamento de áudio
- Processamento local disponível

## 🤝 Contribuindo

1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📝 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

## 👨‍💻 Autor

**Marvin**

- GitHub: [@marvinmvns](https://github.com/marvinmvns)

## 🙏 Agradecimentos

- OpenAI (Whisper, GPT)
- Deepgram
- ElevenLabs
- DeepL
- Pyannote.audio team
- FastAPI team

---

**Salvavidas** - Salvando conversas através das línguas! 🚁🌍
