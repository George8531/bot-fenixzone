import time
import socket
import requests

# === TUS DATOS DE TELEGRAM ===
BOT_TOKEN = "8836352471:AAHtKE6tPbBsxc2jdBAjpIA1SeQcRJy8gk0"
CHAT_ID = "5484160028"

# Datos de conexión FénixZone S1 (IP y Puerto SA-MP)
IP_SERVIDO = "s1.fenixzone.com"
PUERTO_SERVIDOR = 7777

def enviar_telegram(mensaje):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": mensaje, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print(f"Error al enviar Telegram: {e}")

def verificar_servidor():
    try:
        # Se intenta una conexión socket UDP al puerto de SA-MP
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(3)
        # Enviar paquete de Ping simple de SA-MP
        query = b"SAMP" + socket.inet_aton("127.0.0.1") + b"\x00\x00p"
        sock.sendto(query, (IP_SERVIDO, PUERTO_SERVIDOR))
        data, _ = sock.recvfrom(1024)
        sock.close()
        return True if data else False
    except Exception:
        return False

def monitorear():
    estado_anterior = True  # Asumimos que inicia encendido
    print("Iniciando monitoreo de FénixZone S1...")
    
    while True:
        esta_online = verificar_servidor()
        
        # Si el servidor estaba apagado y acaba de encender (Reinicio)
        if esta_online and not estado_anterior:
            mensaje = "🚨 **¡ALERTA FÉNIXZONE S1!** 🚨\n\nEl Servidor 1 se ha **reiniciado** y ya está en línea de nuevo. ¡Aprovecha para entrar!"
            enviar_telegram(mensaje)
            estado_anterior = True
            
        # Si el servidor se cayó
        elif not esta_online and estado_anterior:
            mensaje = "⚠️ **FénixZone S1 se ha caído / apagado.** Monitoreando hasta que vuelva a encender..."
            enviar_telegram(mensaje)
            estado_anterior = False
            
        # Espera 15 segundos antes de volver a revisar
        time.sleep(15)

if __name__ == "__main__":
    monitorear()
