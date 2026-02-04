# 🎯 Guía Visual: Acceder a GUARDIAN Web

## Paso 1️⃣: Instalar

```bash
git clone https://github.com/Sugusdaddy/GUARDIAN.git
cd GUARDIAN
pip install -e .
```

## Paso 2️⃣: Iniciar Servidor

### Opción A: Script de inicio (Más fácil)
```bash
./start_web.sh
```

### Opción B: Python directo
```bash
python app/api/main.py
```

### Opción C: Con Make
```bash
make run-api
```

## Paso 3️⃣: Abrir en Navegador

Abre tu navegador favorito y ve a:

```
🌐 http://localhost:8000
```

## 📸 Capturas de Pantalla

### Dashboard Principal
```
┌────────────────────────────────────────────────────────────┐
│  🛡️ GUARDIAN - Solana Security Platform                   │
├────────────────────────────────────────────────────────────┤
│  Dashboard  |  Threats  |  Agents  |  Scanner  |  Intel   │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  📊 Active Threats: 5      ✅ Resolved: 120               │
│  🤖 Agents Active: 16      📈 Risk Index: 45              │
│                                                            │
│  ┌──────────────────────────────────────────────────┐    │
│  │  📈 Threat Activity (24h)                        │    │
│  │  [Interactive Chart.js Graph]                    │    │
│  └──────────────────────────────────────────────────┘    │
│                                                            │
│  Recent Threats:                                           │
│  🔴 Rug Pull - ScamToken (Severity: 94)                   │
│  🟡 Suspicious Transfer - Wallet (Severity: 62)           │
│  🟢 Investigation - Token (Severity: 30)                  │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

## 🔗 URLs Importantes

| Función | URL |
|---------|-----|
| **Dashboard** | http://localhost:8000 |
| **API Docs** | http://localhost:8000/docs |
| **Status** | http://localhost:8000/api/status |
| **Health** | http://localhost:8000/health |

## ⚡ Atajos de Teclado

Una vez en el dashboard:

- `Tab 1` - Vista Dashboard
- `Tab 2` - Lista de Amenazas
- `Tab 3` - Estado de Agentes
- `Tab 4` - Scanner
- `Tab 5` - Inteligencia

## 🎨 Características del Dashboard

### 1. Monitoreo en Tiempo Real
- ✅ Actualizaciones cada 15 segundos
- ✅ WebSocket para eventos en vivo
- ✅ Indicador de conexión (verde = conectado)

### 2. Panel de Amenazas
- 🔴 Crítico (Severity > 70)
- 🟠 Alto (Severity 50-70)
- 🟡 Medio (Severity 30-50)
- 🟢 Bajo (Severity < 30)

### 3. Scanner de Direcciones
```
┌─────────────────────────────────────────┐
│  Enter Solana Address:                  │
│  [_________________________________]     │
│  [Scan Address]                         │
│                                         │
│  Risk Score: 45.5 🟡                    │
│  Level: MEDIUM                          │
└─────────────────────────────────────────┘
```

### 4. Agentes AI (16 Activos)
```
🔭 SENTINEL   ✅  |  🔍 SCANNER    ✅
🔮 ORACLE     ✅  |  🎯 COORDINATOR ✅
🛡️ GUARDIAN   ✅  |  📚 INTEL      ✅
📢 REPORTER   ✅  |  ✅ AUDITOR    ✅
🔎 HUNTER     ✅  |  💚 HEALER     ✅
🍯 HONEYPOT   ✅  |  🇰🇵 LAZARUS   ✅
🌐 NETWORK    ✅  |  ⚛️ QUANTUM    ✅
🛡️ SWAPGUARD  ✅  |  🚨 EVACUATOR  ✅
```

## 🚀 Próximos Pasos

1. ✅ Acceder al dashboard
2. 📊 Explorar las estadísticas
3. 🔍 Probar el scanner
4. 👀 Ver amenazas en tiempo real
5. 🤖 Monitorear los 16 agentes

## 💡 Tips

- **Mantén el servidor corriendo** para actualizaciones en tiempo real
- **Refresca la página** si la conexión se pierde
- **Usa Ctrl+C** en la terminal para detener el servidor
- **Abre múltiples pestañas** para ver diferentes vistas

## 🆘 ¿Problemas?

Si no puedes acceder:

1. ✅ Verifica que el servidor esté corriendo
2. ✅ Revisa que sea http://localhost:8000 (no https)
3. ✅ Intenta otro navegador
4. ✅ Revisa los logs en la terminal

**Ver más**: [WEB_ACCESS.md](WEB_ACCESS.md)

---

**¡Disfruta monitoreando Solana con GUARDIAN! 🛡️**
