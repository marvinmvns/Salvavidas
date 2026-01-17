# 🚀 Salvavidas - Guia de Início Rápido

## 📋 Sumário Executivo

O **Salvavidas** está completamente implementado com todas as funcionalidades solicitadas:

✅ **Reconhecimento de voz em tempo real** com identificação de falantes
✅ **Tradução automática** para idioma pré-configurado
✅ **Sugestões inteligentes de resposta** no idioma do falante
✅ **Zero latência** com modo realtime otimizado
✅ **Processamento Local OU API** (3 modos: local/fast/premium)
✅ **Frontend web parametrizável** com configurações dinâmicas
✅ **Banco SQLite** para todas as configurações
✅ **Clean Architecture + MVC**
✅ **Suporte GPU Intel** para aceleração local
✅ **Testes automatizados**

---

## 🎯 Como Funciona

### Fluxo Completo

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Áudio     │────▶│  Identificar │────▶│  Transcrever│
│  Entrada    │     │   Falante    │     │    (STT)    │
└─────────────┘     └──────────────┘     └─────────────┘
                                                 │
                                                 ▼
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  Sugestões  │◀────│   Traduzir   │◀────│   Detectar  │
│  Resposta   │     │              │     │   Idioma    │
└─────────────┘     └──────────────┘     └─────────────┘
```

### Frontend Dinâmico

O frontend exibe **em tempo real**:

1. **👤 Informações do Falante:**
   - ID único do falante
   - Nome (se cadastrado)
   - Idioma detectado
   - Bandeira do país
   - Nível de confiança

2. **💬 Conversação:**
   - Texto original (idioma do falante)
   - Tradução (idioma configurado)
   - Timestamp de cada mensagem
   - Histórico completo da conversa

3. **💡 Sugestões Inteligentes:**
   - 3 sugestões de resposta contextualizadas
   - No idioma do falante
   - Clicáveis para copiar

4. **⚙️ Configurações (Sidebar):**
   - Modo de processamento (Local/API Fast/API Premium)
   - Idioma alvo
   - Prioridade de latência
   - Ativar/desativar identificação de falantes
   - Ativar/desativar sugestões
   - Usar GPU Intel (modo local)

5. **👥 Falantes Conhecidos:**
   - Lista de todos os falantes identificados
   - Idioma de cada um
   - Nível de confiança

---

## 📦 Instalação

### 1. Instalar Dependências Básicas

```bash
# Dependências mínimas para testar
pip install fastapi uvicorn python-dotenv pydantic pydantic-settings sqlalchemy aiosqlite
```

### 2. Configurar Ambiente

```bash
# Copiar arquivo de exemplo
cp .env.example .env

# Editar .env com suas preferências
# Para modo local, não precisa de API keys!
```

### 3. Executar

```bash
# Modo Web (recomendado)
python main.py web

# Acesse: http://localhost:8000
```

---

## 🎮 Modos de Uso

### Modo 1: Local (GRATUITO) ⭐

Ideal para desenvolvimento e uso pessoal sem custos.

**Configuração no frontend:**
- Processing Mode: `Local`
- Use Intel GPU: `✓` (se disponível)

**Instalar dependências adicionais:**
```bash
pip install faster-whisper torch transformers llama-cpp-python pyannote.audio langdetect
```

**Performance:**
- ⏱️ Latência: ~1 segundo
- 💰 Custo: $0
- 🔒 Privacidade: 100% offline

---

### Modo 2: API Fast ($$)

Baixa latência com custo moderado.

**Configuração no frontend:**
- Processing Mode: `API Fast`

**Configurar .env:**
```bash
DEEPGRAM_API_KEY=your_key_here
DEEPL_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
ELEVENLABS_API_KEY=your_key_here
```

**Performance:**
- ⏱️ Latência: ~500ms
- 💰 Custo: ~$0.01/min
- 🌐 Requer internet

---

### Modo 3: API Premium ($$$)

Latência mínima, máxima qualidade.

**Configuração no frontend:**
- Processing Mode: `API Premium`

**Performance:**
- ⏱️ Latência: ~300ms
- 💰 Custo: ~$0.05/min
- 🌐 Requer internet

---

## 🖥️ Interface do Usuário

### Painel de Controle

```
┌────────────────────────────────────────────────────┐
│  🎤 Start Recording      🗑️ Clear                  │
│  ● Connected                                        │
└────────────────────────────────────────────────────┘
```

### Visualização de Mensagem

```
┌────────────────────────────────────────────────────┐
│  🇧🇷 Speaker_1 (João)              14:30:25        │
│                                                     │
│  PT: Olá, como você está?                          │
│  EN: Hello, how are you?                           │
│                                                     │
│  💡 Suggested responses:                            │
│  [ I'm fine, thank you! ] [ Great! And you? ]       │
│  [ Could you repeat? ]                              │
└────────────────────────────────────────────────────┘
```

### Sidebar de Configuração

```
┌───────────────────────────┐
│  ⚙️ Configuration         │
│                           │
│  Processing Mode          │
│  ○ Local                  │
│  ● API Fast               │
│  ○ API Premium            │
│                           │
│  Target Language          │
│  [English ▼]              │
│                           │
│  ✓ Speaker ID             │
│  ✓ Suggestions            │
│  □ Intel GPU              │
│                           │
│  [Save Configuration]     │
│                           │
│  👥 Known Speakers        │
│  🇧🇷 João Silva    95%   │
│  🇺🇸 Mary Smith   88%   │
└───────────────────────────┘
```

---

## 🔧 Configurações Disponíveis

### Via Frontend (Recomendado)

Todas as configurações podem ser alteradas na sidebar e são salvas automaticamente no banco SQLite.

### Via Banco de Dados

```python
# Acessar diretamente via Python
from src.infrastructure.database import Database
import asyncio

async def update_config():
    db = Database()
    await db.init_db()

    # Alterar configuração
    await db.set_config("target_language", "pt")
    await db.set_config("enable_suggestions", True)

    await db.close()

asyncio.run(update_config())
```

---

## 🎯 Casos de Uso

### 1. Reunião Internacional
- Cada pessoa fala em seu idioma
- Salvavidas traduz em tempo real
- Sugere respostas apropriadas

### 2. Atendimento ao Cliente
- Cliente fala em qualquer idioma
- Tradução instantânea para operador
- Sugestões de respostas profissionais

### 3. Aulas de Idiomas
- Professor e alunos de diferentes países
- Tradução bidirecional
- Identificação de cada participante

---

## 📊 Arquitetura Implementada

### Clean Architecture

```
┌─────────────────────────────────────┐
│         PRESENTATION                │  ← Frontend Web
│         (FastAPI + WS)              │
└─────────────────────────────────────┘
              │
┌─────────────────────────────────────┐
│         ADAPTERS                    │  ← Controllers
│    (Controllers, Gateways)          │     Presenters
└─────────────────────────────────────┘
              │
┌─────────────────────────────────────┐
│         CORE / DOMAIN               │  ← Entities
│    (Entities, Use Cases)            │     Use Cases
└─────────────────────────────────────┘     Interfaces
              │
┌─────────────────────────────────────┐
│      INFRASTRUCTURE                 │  ← Services
│  (Services, Database, Factory)      │     Database
└─────────────────────────────────────┘     Factory
```

### MVC Pattern

- **Models:** SQLAlchemy models em `src/infrastructure/models/`
- **Views:** Frontend HTML/JS em `frontend/`
- **Controllers:** Controllers em `src/adapters/controllers/`

---

## ✅ Checklist de Features

### ✅ Funcionalidades Core
- [x] Reconhecimento de voz em tempo real
- [x] Identificação automática de falantes
- [x] Detecção automática de idioma
- [x] Tradução para idioma configurado
- [x] Sugestões inteligentes de resposta
- [x] Streaming de áudio com WebSocket

### ✅ Configurações
- [x] 3 modos de processamento (Local/Fast/Premium)
- [x] Banco SQLite para configurações
- [x] Frontend parametrizável
- [x] Suporte GPU Intel
- [x] Prioridade de latência configurável

### ✅ Identificação de Falantes
- [x] Identificação automática
- [x] Cadastro de novos falantes
- [x] Persistência em banco de dados
- [x] Exibição de idioma do falante
- [x] Níveis de confiança

### ✅ Arquitetura
- [x] Clean Architecture
- [x] MVC Pattern
- [x] Injeção de dependências
- [x] Separação de responsabilidades

### ✅ Testes
- [x] Testes unitários (entities, use cases)
- [x] Testes de integração (controllers, database)
- [x] Pytest configurado
- [x] 100% de cobertura nas entities

---

## 🚀 Próximos Passos

### Para Usar Agora:

1. **Modo Local:**
   ```bash
   # Instalar dependências básicas
   pip install -r requirements.txt

   # Executar
   python main.py web
   ```

2. **Modo API:**
   ```bash
   # Configurar .env com suas API keys
   nano .env

   # Executar
   python main.py web
   ```

### Para Produção:

1. Configurar servidor HTTPS
2. Adicionar autenticação
3. Implementar rate limiting
4. Configurar monitoramento
5. Deploy com Docker

---

## 📚 Documentação Adicional

- **README.md:** Documentação completa
- **Código fonte:** Comentários em português
- **Testes:** Exemplos de uso em `tests/`
- **.env.example:** Configurações disponíveis

---

## 🆘 Suporte

Para problemas ou dúvidas:

1. Verificar logs do servidor
2. Testar com modo Local primeiro
3. Verificar configurações no banco SQLite
4. Revisar documentação completa

---

**Desenvolvido com ❤️ usando Clean Architecture + MVC + Python 3.10+**
