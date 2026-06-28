#!/usr/bin/env python3
"""Deploy automático de Apion Bot a VPS"""
import subprocess
import sys
import getpass
import paramiko

# Configuración
VPS_IP = "38.247.141.48"
VPS_USER = "administrator"
VPS_PATH = "/home/bot/apion"

def run_command(cmd, description):
    """Ejecuta comando local"""
    print(f"\n📌 {description}...")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Error: {result.stderr}")
        return False
    print(f"✅ {description}")
    if result.stdout:
        print(result.stdout)
    return True

def ssh_exec(ssh, command):
    """Ejecuta comando en VPS via SSH"""
    stdin, stdout, stderr = ssh.exec_command(command)
    output = stdout.read().decode()
    error = stderr.read().decode()
    if error:
        print(f"⚠️  {error}")
    return output

def deploy():
    """Deploy automático a VPS"""

    # 1. Pedir contraseña VPS
    print("🔐 Contraseña VPS requerida")
    vps_password = getpass.getpass("Contraseña: ")

    # 2. Git commit
    commit_msg = input("\n📝 Commit message: ").strip()
    if not commit_msg:
        print("❌ Mensaje vacío")
        return

    if not run_command(f'git add .', 'Git add'):
        return

    if not run_command(f'git commit -m "{commit_msg}"', 'Git commit'):
        return

    if not run_command(f'git push origin main', 'Git push'):
        return

    # 3. SSH a VPS
    print(f"\n🚀 Conectando a VPS ({VPS_IP})...")

    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(VPS_IP, username=VPS_USER, password=vps_password, timeout=10)

        print("✅ Conectado a VPS\n")

        # Git pull
        print("📥 Haciendo git pull...")
        output = ssh_exec(ssh, f"cd {VPS_PATH} && git pull origin main")
        print(output)

        # Reiniciar servicios
        print("\n🔄 Reiniciando servicios...")
        output = ssh_exec(ssh, "sudo systemctl restart apion.service apion-paypal.service apion-promerica.service apion-logs-viewer.service")
        print(output)

        # Ver estado
        print("\n📊 Estado de servicios:")
        output = ssh_exec(ssh, "sudo systemctl status apion.service --no-pager")
        print(output)

        ssh.close()
        print("\n✅ DEPLOY COMPLETADO!")
        print("\n🌐 Dashboard de logs: http://38.247.141.48:8080")

    except Exception as e:
        print(f"❌ Error SSH: {e}")

if __name__ == "__main__":
    deploy()
