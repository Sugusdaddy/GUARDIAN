#!/bin/bash

# GUARDIAN Web Interface Startup Script
# Este script inicia el servidor web de GUARDIAN

echo "╔══════════════════════════════════════════════════════════════════════╗"
echo "║                                                                      ║"
echo "║   ██████╗ ██╗   ██╗ █████╗ ██████╗ ██████╗ ██╗ █████╗ ███╗   ██╗   ║"
echo "║  ██╔════╝ ██║   ██║██╔══██╗██╔══██╗██╔══██╗██║██╔══██╗████╗  ██║   ║"
echo "║  ██║  ███╗██║   ██║███████║██████╔╝██║  ██║██║███████║██╔██╗ ██║   ║"
echo "║  ██║   ██║██║   ██║██╔══██║██╔══██╗██║  ██║██║██╔══██║██║╚██╗██║   ║"
echo "║  ╚██████╔╝╚██████╔╝██║  ██║██║  ██║██████╔╝██║██║  ██║██║ ╚████║   ║"
echo "║   ╚═════╝  ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝ ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝   ║"
echo "║                                                                      ║"
echo "║                   🌐 Iniciando Web Interface                        ║"
echo "║                                                                      ║"
echo "╚══════════════════════════════════════════════════════════════════════╝"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 no está instalado"
    echo "   Por favor instala Python 3.10 o superior"
    exit 1
fi

echo "✅ Python encontrado: $(python3 --version)"
echo ""

# Check if dependencies are installed
echo "📦 Verificando dependencias..."
if ! python3 -c "import fastapi" &> /dev/null; then
    echo "⚠️  Dependencias no encontradas. Instalando..."
    pip install fastapi uvicorn aiohttp structlog python-dotenv
    echo ""
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  Archivo .env no encontrado"
    if [ -f ".env.example" ]; then
        echo "📝 Copiando .env.example a .env"
        cp .env.example .env
    else
        echo "💡 Tip: Crea un archivo .env con tus configuraciones"
    fi
    echo ""
fi

# Start the server
echo "🚀 Iniciando servidor GUARDIAN..."
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Dashboard:  http://localhost:8000"
echo "  API Docs:   http://localhost:8000/docs"
echo "  Status:     http://localhost:8000/api/status"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "💡 Tip: Presiona Ctrl+C para detener el servidor"
echo ""

# Run the server
cd "$(dirname "$0")"
python3 app/api/main.py
