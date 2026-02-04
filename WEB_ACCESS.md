# 🌐 Cómo Acceder a la Web de GUARDIAN / How to Access GUARDIAN Web

## 🇪🇸 ESPAÑOL

### 📍 ¿Dónde puedo ver la web?

La interfaz web de GUARDIAN está disponible en tu navegador después de iniciar el servidor API.

### 🚀 Inicio Rápido

#### Opción 1: Servidor FastAPI (Recomendado)

```bash
# 1. Instalar dependencias (solo la primera vez)
pip install -e .

# 2. Iniciar el servidor
python app/api/main.py

# 3. Abrir en tu navegador
# http://localhost:8000
```

El dashboard estará disponible en: **http://localhost:8000**

#### Opción 2: Script de Inicio Rápido

```bash
# Ejecutar script de inicio
./start_web.sh

# O con Make
make run-api
```

#### Opción 3: Usando uvicorn directamente

```bash
cd app/api
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 📋 Requisitos Previos

1. **Python 3.10+** instalado
2. **Dependencias instaladas**:
   ```bash
   pip install fastapi uvicorn aiohttp structlog python-dotenv
   # O instalar todo con:
   pip install -e ".[dev]"
   ```

3. **Archivo .env configurado** (opcional pero recomendado):
   ```bash
   cp .env.example .env
   # Editar .env con tus claves API
   ```

### 🔗 URLs Disponibles

Una vez el servidor esté corriendo:

- **Dashboard Principal**: http://localhost:8000
- **API Status**: http://localhost:8000/api/status
- **Documentación API**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

### 🎨 Características del Dashboard

El dashboard incluye:
- ✅ Monitoreo en tiempo real de amenazas
- ✅ 16 agentes AI especializados
- ✅ Gráficos interactivos con Chart.js
- ✅ Actualizaciones en vivo por WebSocket
- ✅ Scanner de direcciones Solana
- ✅ Panel de inteligencia de amenazas
- ✅ Estadísticas del sistema

### 🐛 Solución de Problemas

#### Error: "ModuleNotFoundError: No module named 'fastapi'"

```bash
# Instalar dependencias faltantes
pip install fastapi uvicorn aiohttp structlog
```

#### Error: "Address already in use"

```bash
# El puerto 8000 ya está en uso, usar otro puerto
python app/api/main.py --port 8001

# O encontrar y detener el proceso
lsof -ti:8000 | xargs kill -9  # macOS/Linux
netstat -ano | findstr :8000   # Windows
```

#### La página no carga

1. Verificar que el servidor esté corriendo
2. Revisar los logs en la terminal
3. Intentar limpiar caché del navegador
4. Verificar que el puerto 8000 no esté bloqueado por firewall

### 📱 Acceso desde Otros Dispositivos

Para acceder desde otro dispositivo en la misma red:

```bash
# Iniciar con host 0.0.0.0
python app/api/main.py

# Luego acceder desde otro dispositivo usando:
# http://[TU_IP_LOCAL]:8000
# Ejemplo: http://192.168.1.100:8000
```

---

## 🇬🇧 ENGLISH

### 📍 Where Can I See the Web?

The GUARDIAN web interface is available in your browser after starting the API server.

### 🚀 Quick Start

#### Option 1: FastAPI Server (Recommended)

```bash
# 1. Install dependencies (first time only)
pip install -e .

# 2. Start the server
python app/api/main.py

# 3. Open in your browser
# http://localhost:8000
```

The dashboard will be available at: **http://localhost:8000**

#### Option 2: Quick Start Script

```bash
# Run startup script
./start_web.sh

# Or with Make
make run-api
```

#### Option 3: Using uvicorn directly

```bash
cd app/api
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 📋 Prerequisites

1. **Python 3.10+** installed
2. **Dependencies installed**:
   ```bash
   pip install fastapi uvicorn aiohttp structlog python-dotenv
   # Or install everything with:
   pip install -e ".[dev]"
   ```

3. **Configure .env file** (optional but recommended):
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

### 🔗 Available URLs

Once the server is running:

- **Main Dashboard**: http://localhost:8000
- **API Status**: http://localhost:8000/api/status
- **API Documentation**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

### 🎨 Dashboard Features

The dashboard includes:
- ✅ Real-time threat monitoring
- ✅ 16 specialized AI agents
- ✅ Interactive charts with Chart.js
- ✅ Live updates via WebSocket
- ✅ Solana address scanner
- ✅ Threat intelligence panel
- ✅ System statistics

### 🐛 Troubleshooting

#### Error: "ModuleNotFoundError: No module named 'fastapi'"

```bash
# Install missing dependencies
pip install fastapi uvicorn aiohttp structlog
```

#### Error: "Address already in use"

```bash
# Port 8000 is already in use, use another port
python app/api/main.py --port 8001

# Or find and stop the process
lsof -ti:8000 | xargs kill -9  # macOS/Linux
netstat -ano | findstr :8000   # Windows
```

#### Page doesn't load

1. Verify the server is running
2. Check logs in terminal
3. Try clearing browser cache
4. Verify port 8000 isn't blocked by firewall

### 📱 Access from Other Devices

To access from another device on the same network:

```bash
# Start with host 0.0.0.0
python app/api/main.py

# Then access from another device using:
# http://[YOUR_LOCAL_IP]:8000
# Example: http://192.168.1.100:8000
```

---

## 🎯 Quick Reference

| What | Command | URL |
|------|---------|-----|
| Start Server | `python app/api/main.py` | - |
| Dashboard | - | http://localhost:8000 |
| API Docs | - | http://localhost:8000/docs |
| Stop Server | `Ctrl+C` | - |

## 📞 Need Help?

- 📖 Documentation: See [docs/](../docs/) folder
- 🐛 Issues: https://github.com/Sugusdaddy/GUARDIAN/issues
- 💬 Discussions: https://github.com/Sugusdaddy/GUARDIAN/discussions

---

**Happy monitoring! 🛡️**
