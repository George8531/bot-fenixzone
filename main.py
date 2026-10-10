import os
import time
import socket
import threading
import requests
from datetime import datetime
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot de FénixZone S1 activo 24/7", 200

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

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
        time.sleep(300)

BOT_TOKEN = "8836352471:AAHtKE6tPbBsxc2jdBAjpIA1SeQcRJy8gk0"
ADMIN_CHAT_ID = "5484160028"

IP_SERVIDOR = "s1.fenixzone.com"
PUERTO_SERVIDOR = 7777

SUSCRIPTORES = {ADMIN_CHAT_ID}

def enviar_telegram(mensaje, chat_target=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    
    if chat_target:
        payload = {"chat_id": chat_target, "text": mensaje, "parse_mode": "Markdown"}
        try:
            requests.post(url, json=payload, timeout=5)
        except Exception as e:
            print(f"Error enviando mensaje a {chat_target}: {e}")
    else:
        for user_id in list(SUSCRIPTORES):
            payload = {"chat_id": user_id, "text": mensaje, "parse_mode": "Markdown"}
            try:
                requests.post(url, json=payload, timeout=5)
            except Exception as e:
                print(f"Error enviando broadcast a {user_id}: {e}")

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
                    sender = message.get("from", {})
                    sender_id = str(sender.get("id", ""))
                    first_name = sender.get("first_name", "Desconocido")
                    username = sender.get("username", "Sin username")
                    
                    # Comando /start
                    if texto.strip() == "/start" and sender_id:
                        es_nuevo = sender_id not in SUSCRIPTORES
                        SUSCRIPTORES.add(sender_id)
                        
                        respuesta = (
                            "🤖 **¡Bot de Monitoreo FénixZone S1 Activado!**\n\n"
                            "Estás registrado para recibir alertas automáticamente en privado cuando el Servidor 1 "
                            "se caiga, se reinicie o al momento del pago diario (:02)."
                        )
                        enviar_telegram(respuesta, chat_target=sender_id)
                        
                        if es_nuevo and sender_id != ADMIN_CHAT_ID:
                            notif_admin = (
                                f"👤 **¡Nuevo suscriptor registrado!**\n\n"
                                f"• **Nombre:** {first_name}\n"
                                f"• **Usuario:** @{username}\n"
                                f"• **ID Telegram:** `{sender_id}`\n"
                                f"• **Total Suscriptores:** {len(SUSCRIPTORES)}"
                            )
                            enviar_telegram(notif_admin, chat_target=ADMIN_CHAT_ID)

                    # Comando /broadcast (Exclusivo para el Administrador)
                    elif texto.startswith("/broadcast") and sender_id == ADMIN_CHAT_ID:
                        partes = texto.split(" ", 1)
                        if len(partes) > 1:
                            anuncio = f"📢 **Anuncio Oficial:**\n\n{partes[1]}"
                            enviar_telegram(anuncio, chat_target=None)
                            enviar_telegram("✅ Mensaje enviado con éxito a todos los suscriptores.", chat_target=ADMIN_CHAT_ID)
                        else:
                            enviar_telegram("⚠️ Uso incorrecto. Escribe por ejemplo: `/broadcast Hola a todos`", chat_target=ADMIN_CHAT_ID)
                            
        except Exception as e:
            print(f"Error en polling de Telegram: {e}")
            
        time.sleep(2)

def temporizador_pago_diario():
    ultimo_minuto_enviado = -1
    print("Iniciando temporizador de pago diario (:02 cada hora)...")
    
    while True:
        ahora = datetime.now()
        if ahora.minute == 2 and ahora.minute != ultimo_minuto_enviado:
            mensaje_pago = "💵 **Notificación:** Se ha emitido un pago diario."
            enviar_telegram(mensaje_pago, chat_target=None)
            ultimo_minuto_enviado = ahora.minute
        elif ahora.minute != 2:
            ultimo_minuto_enviado = -1
            
        time.sleep(10)

def verificar_servidor():
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(2)
        query = b"SAMP" + socket.inet_aton("127.0.0.1") + b"\x00\x00p"
        sock.sendto(query, (IP_SERVIDOR, PUERTO_SERVIDOR))
        data, _ = sock.recvfrom(1024)
        sock.close()
        return True if data else False
    except Exception:
        return False

def monitorear():
    estado_anterior = True
    print("Iniciando monitoreo de FénixZone S1 (cada 2 segundos)...")
    
    while True:
        esta_online = verificar_servidor()
        
        if esta_online and not estado_anterior:
            mensaje = "🚨 **El servidor se ha reiniciado y ya esta disponible**"
            enviar_telegram(mensaje, chat_target=None)
            estado_anterior = True
            
        elif not esta_online and estado_anterior:
            mensaje = "⚠️ **FénixZone S1 se ha caído / apagado.** Monitoreando..."
            enviar_telegram(mensaje, chat_target=None)
            estado_anterior = False
            
        time.sleep(2) # Chequeo cada 2 segundos

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    threading.Thread(target=auto_ping, daemon=True).start()
    threading.Thread(target=escuchar_mensajes, daemon=True).start()
    threading.Thread(target=temporizador_pago_diario, daemon=True).start()
    monitorear()
