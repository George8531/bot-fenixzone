import os
import time
import socket
import threading
import requests
from datetime import datetime
from flask import Flask

# Servidor Flask para mantener activo Render
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot de FénixZone S1 activo 24/7", 200

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# Mantiene vivo el servicio de Render haciendo una autofila web cada 10 min
def auto_ping():
    time.sleep(10)
    render_url = os.environ.get("RENDER_EXTERNAL_URL")
    while True:
        if render_url:
            try:
                requests.get(render_url, timeout=5)
                print("Auto-ping realizado con éxito para mantener vivo Render.")
            except Exception as e:
                print(f"Error en auto-ping: {e}")
        time.sleep(600) # 10 minutos

# === DATOS DE CONFIGURACIÓN ===
BOT_TOKEN = "8836352471:AAHtKE6tPbBsxc2jdBAjpIA1SeQcRJy8gk0"
CHAT_ID = "5484160028"

# Servidor FénixZone S1
IP_SERVIDOR = "s1.fenixzone.com"
PUERTO_SERVIDOR = 7777

def enviar_telegram(mensaje, chat_target=CHAT_ID):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_target, "text": mensaje, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print(f"Error al enviar a Telegram: {e}")

# === ATENDER COMANDOS DE TELEGRAM (/start) ===
def escuchar_mensajes():
    last_update_id = 0
    print("Escuchando comandos de Telegram...")
    
    while True:
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
            params = {"offset": last_update_id + 1, "timeout": 10}
            resp = requests.get(url, params=params, timeout=15).json()
            
            if resp.get("ok"):
                for result in resp.get("result", []):
                    last_update_id = result["update_id"]
                    message = result.get("message", {})
                    texto = message.get("text", "")
                    sender_id = message.get("chat", {}).get("id")
                    
                    if texto.strip() == "/start" and sender_id:
                        respuesta = (
                            "🤖 **¡Bot de Monitoreo FénixZone S1 Activado!**\n\n"
                            "Te avisaré automáticamente por este medio cada vez que el Servidor 1 "
                            "se caiga o se reinicie."
                        )
                        enviar_telegram(respuesta, chat_target=sender_id)
        except Exception as e:
            print(f"Error en polling de Telegram: {e}")
            
        time.sleep(2)

# === PROGRAMADOR CADA HORA AL MINUTO 02 ===
def temporizador_pago_diario():
    ultimo_minuto_enviado = -1
    print("Iniciando temporizador de pago diario (:02 cada hora)...")
    
    while True:
        ahora = datetime.now()
        if ahora.minute == 2 and ahora.minute != ultimo_minuto_enviado:
            mensaje_pago = "💵 **Notificación:** Se ha emitido un pago diario."
            enviar_telegram(mensaje_pago)
            ultimo_minuto_enviado = ahora.minute
        elif ahora.minute != 2:
            ultimo_minuto_enviado = -1
            
        time.sleep(10)

# === VERIFICACIÓN DE FÉNIXZONE S1 ===
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
    # 1. Servidor Web Flask
    threading.Thread(target=run_flask, daemon=True).start()
    
    # 2. Auto-ping para evitar suspend en Render
    threading.Thread(target=auto_ping, daemon=True).start()
    
    # 3. Escucha de comandos /start
    threading.Thread(target=escuchar_mensajes, daemon=True).start()
    
    # 4. Temporizador de pago diario (:02 cada hora)
    threading.Thread(target=temporizador_pago_diario, daemon=True).start()
    
    # 5. Monitoreo del juego
    monitorear()
