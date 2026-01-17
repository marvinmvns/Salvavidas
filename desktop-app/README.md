# 🖥️ Salvavidas Desktop App

Aplicação desktop cross-platform com **modo invisível** para compartilhamento de tela.

## ✨ Características

### 🌐 Multi-Plataforma
- ✅ **Windows** (7/8/10/11)
- ✅ **macOS** (10.13+)
- ✅ **Linux** (Ubuntu, Debian, Fedora, etc.)

### 👁️ Modo Invisível
- **Invisível ao compartilhar tela** (Zoom, Meet, Teams)
- Overlay transparente sempre visível
- Não aparece na captura de tela
- Discreto para apresentações profissionais

### ⌨️ Atalhos Globais
- `Ctrl+Shift+O`: Toggle overlay
- `Ctrl+Shift+I`: Ativar modo invisível
- `Ctrl+Shift+S`: Mostrar/ocultar janela principal
- `Ctrl+Shift+H`: Ocultar tudo

### 📊 Funcionalidades
- Todas as funcionalidades web disponíveis
- System tray icon
- Sempre on top (opcional)
- Arrastar e soltar o overlay
- Conecta ao servidor local (Python backend)

---

## 🚀 Instalação

### Opção 1: Binários Pré-Compilados (Recomendado)

Download para seu sistema operacional:

- **Windows**: `Salvavidas-Setup-1.0.0.exe` ou `Salvavidas-1.0.0-portable.exe`
- **macOS**: `Salvavidas-1.0.0.dmg`
- **Linux**: `Salvavidas-1.0.0.AppImage` ou `.deb` / `.rpm`

### Opção 2: Compilar do Código-Fonte

#### Pré-requisitos
- Node.js 16+ ([Download](https://nodejs.org/))
- NPM (incluído com Node.js)

#### Passos

```bash
# 1. Entre na pasta desktop-app
cd desktop-app

# 2. Instale dependências
npm install

# 3. Execute em modo desenvolvimento
npm start

# 4. Compile para produção
# Windows:
npm run build:win

# macOS:
npm run build:mac

# Linux:
npm run build:linux
```

Os binários estarão em `desktop-app/dist/`

---

## 📖 Como Usar

### Primeira Execução

1. **Inicie o backend Python:**
   ```bash
   cd ..  # Voltar para raiz do Salvavidas
   python main.py web
   ```

2. **Inicie a aplicação desktop:**
   - Clique duplo no executável
   - Ou execute `npm start` no terminal

3. **A aplicação irá:**
   - Conectar ao servidor local (localhost:8000)
   - Mostrar ícone na system tray
   - Abrir janela principal

### Modo Invisível para Apresentações

**Cenário:** Você está em uma reunião no Zoom/Meet/Teams e quer usar o Salvavidas sem que os participantes vejam.

#### Método 1: Atalho de Teclado
1. Pressione `Ctrl+Shift+I`
2. A janela principal se oculta
3. Um overlay discreto aparece no canto da tela
4. **Este overlay NÃO aparece ao compartilhar tela!**

#### Método 2: System Tray
1. Clique com botão direito no ícone da bandeja
2. Marque "Invisible Mode"

#### Como Funciona?
- **Windows**: Usa janela `type: 'panel'` + `skipTaskbar`
- **macOS**: Usa `type: 'panel'` + `vibrancy`
- **Linux**: Usa `skipTaskbar` + configurações especiais

O overlay fica **sempre visível para você**, mas **invisível** em:
- Compartilhamento de tela (Zoom, Meet, Teams)
- Print Screen / capturas de tela
- Gravações de tela

### Posicionamento do Overlay

O overlay é **draggable** (arrastável):
1. Clique e arraste a área do cabeçalho
2. Posicione onde preferir
3. A posição é salva automaticamente

---

## 🎮 Controles

### Janela Principal
- Todas as funcionalidades web
- Configurações completas
- Histórico de conversas
- Gerenciamento de falantes

### Overlay (Modo Invisível)
- 🎤 Indicador de escuta (tempo real)
- 💡 Top 2 sugestões
- 📋 Copiar sugestão com 1 clique
- ✨ Animações suaves

### System Tray
- Show/Hide: Clique simples
- Menu: Clique direito
- Quit: Menu → Quit

---

## ⚙️ Configuração

### Conectar a Servidor Remoto

Se o backend Python está em outro computador:

```javascript
// Desktop app irá conectar ao servidor configurado
// Por padrão: http://localhost:8000

// Para mudar, edite o arquivo de configuração:
// Windows: %APPDATA%/salvavidas-desktop/config.json
// macOS: ~/Library/Application Support/salvavidas-desktop/config.json
// Linux: ~/.config/salvavidas-desktop/config.json

{
  "serverUrl": "http://192.168.1.100:8000"
}
```

### Configurações Disponíveis

Via interface gráfica ou arquivo de configuração:
- URL do servidor
- Modo de processamento
- Idioma alvo
- Ativar/desativar features

---

## 🛠️ Desenvolvimento

### Estrutura

```
desktop-app/
├── src/
│   ├── main.js           # Processo principal Electron
│   └── preload.js        # Script de segurança
├── public/
│   └── overlay.html      # Overlay invisível
├── build/                # Ícones e recursos
│   ├── icon.ico         # Windows
│   ├── icon.icns        # macOS
│   └── icon.png         # Linux
└── package.json
```

### Tecnologias

- **Electron 28**: Framework multi-plataforma
- **electron-store**: Persistência de configurações
- **ws**: WebSocket client

### Build Process

O `electron-builder` cria instaladores:

- **Windows**: `.exe` (NSIS installer) + portable
- **macOS**: `.dmg` + `.zip`
- **Linux**: `.AppImage`, `.deb`, `.rpm`

---

## 🔒 Privacidade e Segurança

### Dados Locais
- Configurações salvas localmente
- Nenhum dado enviado para servidores externos
- Conexão apenas com backend local/configurado

### Modo Invisível
- **NÃO é um keylogger ou spyware**
- Apenas exibe sugestões do backend
- Você controla quando ativar/desativar

### Permissões
- Acesso à internet (conectar ao backend)
- System tray
- Global shortcuts
- Nenhuma permissão sensível

---

## 🐛 Troubleshooting

### Overlay não fica invisível ao compartilhar

**Solução:**
- No Zoom/Meet, selecione "Screen" (não "Window")
- Reinicie a aplicação
- No macOS, conceda permissões de acessibilidade

### Não conecta ao backend

**Verificar:**
1. Backend Python está rodando?
   ```bash
   python main.py web
   ```

2. URL correta?
   - Padrão: `http://localhost:8000`

3. Firewall bloqueando?
   - Adicione exceção para a porta 8000

### Atalhos não funcionam

**Solução:**
- Conceda permissões de acessibilidade (macOS)
- Execute como administrador (Windows)
- Verifique conflitos com outros apps

---

## 📊 Comparação: Desktop vs Web

| Feature | Desktop App | Web App |
|---------|-------------|---------|
| **Instalação** | Binário executável | Browser |
| **Performance** | Nativa | Depende do browser |
| **Modo Invisível** | ✅ Sim | ❌ Não |
| **Atalhos Globais** | ✅ Sim | ⚠️ Limitado |
| **System Tray** | ✅ Sim | ❌ Não |
| **Always on Top** | ✅ Sim | ⚠️ Depende |
| **Offline** | ⚠️ Precisa backend | ⚠️ Precisa backend |
| **Cross-platform** | ✅ Win/Mac/Linux | ✅ Qualquer SO |

**Recomendação:** Use desktop app para **apresentações profissionais** onde precisa do modo invisível.

---

## 🎯 Casos de Uso

### 1. Reunião de Vendas (Zoom)
1. Inicie o Zoom
2. Ative modo invisível (`Ctrl+Shift+I`)
3. Compartilhe sua tela
4. O overlay fica visível para você, invisível para clientes
5. Receba sugestões em tempo real sem expor

### 2. Entrevista de Emprego (Google Meet)
1. Entre na chamada
2. Ative modo invisível
3. Compartilhe apresentação
4. Receba sugestões de respostas discretamente

### 3. Apresentação Multilíngue (Teams)
1. Apresentação com audiência internacional
2. Use tradutor em tempo real
3. Receba sugestões no idioma de cada pessoa
4. Modo invisível mantém profissionalismo

---

## 🚀 Roadmap

### v1.1 (Próximo)
- [ ] Auto-update integrado
- [ ] Múltiplos perfis/configurações
- [ ] Sincronização na nuvem (opcional)
- [ ] Gravação de reuniões

### v1.2
- [ ] Integração nativa Zoom/Meet
- [ ] Plugin para aplicativos de vídeo
- [ ] OCR de tela (ler texto da tela)
- [ ] Modo colaborativo (múltiplos usuários)

### v2.0
- [ ] IA completamente offline
- [ ] Modelos personalizados
- [ ] Enterprise features
- [ ] Mobile companion app

---

## 📄 Licença

MIT License - Veja `../LICENSE`

---

## 🆘 Suporte

- **Issues**: [GitHub Issues](https://github.com/marvinmvns/Salvavidas/issues)
- **Documentação**: `../README.md`
- **Email**: support@salvavidas.com (fictício)

---

**Desenvolvido com ❤️ usando Electron + Python**

🚁 **Salvavidas Desktop** - Seu assistente invisível para apresentações profissionais!
