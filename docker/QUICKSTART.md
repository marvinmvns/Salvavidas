# 🚀 Salvavidas Docker - Guia Rápido

Deploy do Salvavidas em **3 minutos**!

---

## 📋 Pré-requisitos

- Docker 20.10+ instalado
- Docker Compose v2.0+
- 8 GB RAM disponível
- 20 GB espaço em disco

---

## ⚡ Início Rápido

### 1️⃣ Clone e Entre na Pasta

```bash
cd Salvavidas/docker
```

### 2️⃣ Configure Variáveis

```bash
cp .env.example .env
# Edite se necessário (opcional para começar)
```

### 3️⃣ Build

```bash
./build.sh local
```

**Tempo esperado:** 5-10 minutos (primeira vez)

### 4️⃣ Iniciar

```bash
./deploy.sh start
```

**Tempo esperado:** 30-60 segundos

### 5️⃣ Verificar

```bash
./deploy.sh health
```

Deve mostrar:
```
✓ Backend: Healthy
```

### 6️⃣ Acessar

- **Backend:** http://localhost:8000
- **Docs:** http://localhost:8000/docs
- **Health:** http://localhost:8000/health

---

## ✅ Pronto!

Sua instância do Salvavidas está rodando!

### Próximos Passos

**Ver logs:**
```bash
./deploy.sh logs -f
```

**Parar:**
```bash
./deploy.sh stop
```

**Reiniciar:**
```bash
./deploy.sh restart
```

**Atualizar:**
```bash
./deploy.sh update
```

---

## 🎯 Testes Rápidos

### Test 1: API está respondendo

```bash
curl http://localhost:8000/health
```

Deve retornar JSON com `"status": "healthy"`

### Test 2: WebSocket funciona

```bash
# Testar via browser console
ws = new WebSocket('ws://localhost:8000/ws/voice')
ws.onopen = () => console.log('Connected!')
```

### Test 3: Frontend carrega

Abra: http://localhost:8000

Deve ver a interface do Salvavidas.

---

## ❓ Problemas?

### Porta 8000 ocupada

```bash
# Ver o que está usando
sudo lsof -i :8000

# Ou mude a porta em docker-compose.yml
ports:
  - "8080:8000"
```

### Containers não iniciam

```bash
# Ver logs
./deploy.sh logs

# Rebuild
./deploy.sh clean
./build.sh local
./deploy.sh start
```

### Health check falha

```bash
# Verificar status
docker-compose ps

# Ver logs do backend
docker-compose logs backend

# Entrar no container
./deploy.sh shell
```

---

## 📚 Documentação Completa

Ver: [README.md](README.md)

---

## 🆘 Ajuda

**GitHub Issues:** https://github.com/marvinmvns/Salvavidas/issues

---

**Feito! Enjoy Salvavidas! 🎉**
