import time
import socket
import threading
import requests
from flask import Flask

# Servidor Flask para mantener activo el servicio en Render
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot de FénixZone S1 activo 24/7"

def run_flask():
    app.run(host='0.0.0.0', port=10000)

# === TUS DATOS DE TELEGRAM ===
BOT_TOKEN = "8836352471:AAHtKE6tPbBsxc2jdBAjpIA1SeQcRJy8gk0"
CHAT_ID = "5484160028"

# Datos FénixZone S1
IP_SERVIDOR = "s1.fenixzone.com"
PUERTO_SERVIDOR = 7777

def enviar_telegram(mensaje):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": mensaje, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print(f"Error Telegram: {e}")

def verificar_servidor():
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(3)
        query = b"SAMP" + socket.inet_aton("127.0.0.1") + b"\x00\x00p"
        sock.sendto(query, (IP_SERVIDOR, PUERTO_SERVIDOR))
        data, _ = sock.recvfrom(1024)
        sock.close()
        return True if data else False
    except Exception:
        return False

def monitorear():
    estado_anterior = True
    print("Iniciando monitoreo de FénixZone S1...")
    
    while True:
        esta_online = verificar_servidor()
        
        if esta_online and not estado_anterior:
            mensaje = "🚨 **¡ALERTA FÉNIXZONE S1!** 🚨\n\nEl Servidor 1 se ha **reiniciado** y ya está en línea de nuevo. ¡Aprovecha para entrar!"
            enviar_telegram(mensaje)
            estado_anterior = True
            
        elif not esta_online and estado_anterior:
            mensaje = "⚠️ **FénixZone S1 se ha caído / apagado.** Monitoreando..."
            enviar_telegram(mensaje)
            estado_anterior = False
            
        time.sleep(15)

if __name__ == "__main__":
    # Arranca el servidor web en el puerto 10000 que Render detectará
    threading.Thread(target=run_flask, daemon=True).start()
    
    # Mensaje de confirmación a Telegram al encender
    enviar_telegram("✅ **Bot de FénixZone S1 iniciado con éxito en Render.** Te avisaré si hay reinicios.")
    
    # Inicia el ciclo de monitoreo
    monitorear()
