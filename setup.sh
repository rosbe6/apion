#!/bin/bash
# Setup script para migración de Apion a VPS Linux
# Ejecutar como: bash setup.sh

set -e

echo "======================================"
echo "🚀 Apion Bot - Setup Linux VPS"
echo "======================================"

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 1. Actualizar sistema
echo -e "\n${YELLOW}[1/10] Actualizando sistema...${NC}"
sudo apt update && sudo apt upgrade -y

# 2. Instalar dependencias de sistema
echo -e "\n${YELLOW}[2/10] Instalando dependencias del sistema...${NC}"
sudo apt install -y \
    python3.11 \
    python3.11-venv \
    python3.11-dev \
    python3-pip \
    chromium-browser \
    git \
    curl \
    wget \
    nano \
    libssl-dev \
    libffi-dev \
    build-essential

# 3. Crear usuario 'bot' si no existe
echo -e "\n${YELLOW}[3/10] Creando usuario 'bot'...${NC}"
if ! id "bot" &>/dev/null; then
    sudo adduser --disabled-password --gecos "" bot
    echo "Usuario 'bot' creado"
else
    echo "Usuario 'bot' ya existe"
fi

# 4. Crear estructura de directorios
echo -e "\n${YELLOW}[4/10] Creando estructura de directorios...${NC}"
sudo mkdir -p /home/bot/apion/{data,logs,temp_profiles}
sudo chown -R bot:bot /home/bot/apion

# 5. Clonar o copiar el código
echo -e "\n${YELLOW}[5/10] Preparando código...${NC}"
if [ -d ".git" ]; then
    echo "Repositorio Git detectado"
    sudo -u bot git clone "$(git config --get remote.origin.url)" /home/bot/apion
else
    echo "Copiando archivos locales..."
    sudo cp -r . /home/bot/apion/
fi

# 6. Crear venv e instalar dependencias Python
echo -e "\n${YELLOW}[6/10] Creando entorno virtual Python...${NC}"
sudo -u bot python3.11 -m venv /home/bot/apion/venv
sudo -u bot /home/bot/apion/venv/bin/pip install --upgrade pip setuptools wheel
sudo -u bot /home/bot/apion/venv/bin/pip install -r /home/bot/apion/requirements.txt

# 7. Configurar .env
echo -e "\n${YELLOW}[7/10] Configurando .env...${NC}"
if [ ! -f /home/bot/apion/.env ]; then
    sudo cp /home/bot/apion/.env.template /home/bot/apion/.env
    sudo chown bot:bot /home/bot/apion/.env
    echo -e "${RED}⚠️  IMPORTANTE: Edita /home/bot/apion/.env con tus credenciales${NC}"
    echo "   sudo nano /home/bot/apion/.env"
else
    echo ".env ya existe"
fi

# 8. Copiar servicios systemd
echo -e "\n${YELLOW}[8/10] Instalando servicios systemd...${NC}"
sudo cp /home/bot/apion/systemd/apion.service /etc/systemd/system/
sudo cp /home/bot/apion/systemd/apion-paypal.service /etc/systemd/system/
sudo cp /home/bot/apion/systemd/apion-promerica.service /etc/systemd/system/
sudo systemctl daemon-reload

# 9. Configurar permisos
echo -e "\n${YELLOW}[9/10] Configurando permisos...${NC}"
sudo chown -R bot:bot /home/bot/apion
sudo chmod +x /home/bot/apion/setup.sh

# 10. Verificar instalación
echo -e "\n${YELLOW}[10/10] Verificando instalación...${NC}"
which chromium || echo -e "${RED}⚠️  Chromium no se encontró. Instalando...${NC}" && sudo apt install chromium-browser -y
/home/bot/apion/venv/bin/python --version

echo -e "\n${GREEN}======================================"
echo "✅ Setup completado exitosamente"
echo "=====================================${NC}"

echo -e "\n${YELLOW}PRÓXIMOS PASOS:${NC}"
echo "1. Edita las credenciales en .env:"
echo "   sudo nano /home/bot/apion/.env"
echo ""
echo "2. Inicia los servicios:"
echo "   sudo systemctl start apion.service"
echo "   sudo systemctl start apion-paypal.service"
echo "   sudo systemctl start apion-promerica.service"
echo ""
echo "3. Habilita los servicios para que se inicien automáticamente:"
echo "   sudo systemctl enable apion.service"
echo "   sudo systemctl enable apion-paypal.service"
echo "   sudo systemctl enable apion-promerica.service"
echo ""
echo "4. Verifica el estado:"
echo "   sudo systemctl status apion.service"
echo "   tail -f /home/bot/apion/logs/bot.log"
echo ""
