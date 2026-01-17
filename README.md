# 🚁 Salvavidas - Real-time Voice Translation

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Clean Architecture](https://img.shields.io/badge/Architecture-Clean-orange.svg)](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)

**Salvavidas** é uma aplicação de tradução de voz em tempo real com identificação de falantes e sugestões de respostas inteligentes. Desenvolvida com **Clean Architecture** e **MVC**, oferece processamento local ou via API com foco em **zero latência**.

## ✨ Características

- 🎤 **Reconhecimento de Voz em Tempo Real** (STT)
- 👥 **Identificação de Falantes** (Speaker Diarization)
- 🌍 **Tradução Multilíngue** (suporta 30+ idiomas)
- 🤖 **Sugestões Inteligentes de Resposta** (LLM)
- 🔊 **Síntese de Voz** (TTS)
- ⚡ **Zero Latência** (modo realtime otimizado)
- 🖥️ **Frontend Web Parametrizável**
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
│   ├── core/                      # Clean Architecture - Domain
│   │   ├── entities/             # Entidades do domínio
│   │   ├── use_cases/            # Casos de uso
│   │   └── interfaces/           # Interfaces (Ports)
│   ├── adapters/                 # Clean Architecture - Adapters
│   │   ├── controllers/          # MVC - Controllers
│   │   ├── presenters/           # MVC - Views/Presenters (API)
│   │   └── gateways/
│   └── infrastructure/           # Clean Architecture - Infrastructure
│       ├── services/
│       │   ├── stt/             # Speech-to-Text
│       │   ├── tts/             # Text-to-Speech
│       │   ├── speaker_id/      # Speaker Identification
│       │   ├── translation/     # Translation
│       │   └── llm/             # Language Models
│       ├── models/              # MVC - Models (Database)
│       ├── database.py
│       └── service_factory.py
├── frontend/                     # Frontend Web
│   ├── index.html
│   └── app.js
├── tests/                        # Testes
│   ├── unit/
│   └── integration/
├── config/                       # Configurações
├── main.py                       # Ponto de entrada
└── requirements.txt
```

## 🚀 Instalação

### Pré-requisitos

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

#### 1. **Local** (Gratuito)
- **STT**: Whisper (faster-whisper)
- **TTS**: Piper
- **Translation**: Helsinki-NLP models
- **LLM**: Llama.cpp
- **Speaker ID**: Pyannote.audio
- ⚡ **GPU Intel**: Suportado via OpenVINO/oneAPI

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
- **Faster-Whisper** (STT) - Otimizado com CTranslate2
- **Piper** (TTS) - TTS rápido local
- **Pyannote.audio** (Speaker ID) - Identificação de falantes
- **Helsinki-NLP** (Translation) - Modelos MarianMT
- **Llama.cpp** (LLM) - LLM local com quantização

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

| Modo | Latência STT | Latência Total | Custo |
|------|-------------|----------------|-------|
| Local | ~500ms | ~1s | $0 |
| API Fast | ~300ms | ~500ms | ~$0.01/min |
| API Premium | ~200ms | ~300ms | ~$0.05/min |

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
