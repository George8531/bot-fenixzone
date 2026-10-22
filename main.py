import os
import time
import socket
import threading
import requests
from bs4 import BeautifulSoup
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

BOT_TOKEN = "8836352471:AAEabVwZQ4nSqo35cKXQLVpeHselFNW879s"
ADMIN_CHAT_ID = "5484160028"

IP_SERVIDOR = "s1.fenixzone.com"
PUERTO_SERVIDOR = 7777
WEB_URL = "https://fenixzone.com/"

# Suscriptores fijos (Admin, La J y Frank)
SUSCRIPTORES = {ADMIN_CHAT_ID, "1777216565", "8661948077"}

# Registro histórico de caídas/reinicios
HISTORIAL_CAIDAS = []

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

def notificar_actualizacion():
    """Envía una alerta al administrador cada vez que el script arranca o se actualiza."""
    time.sleep(3)
    mensaje = (
        "🛠 **¡Script Actualizado / Reiniciado!**\n\n"
        "El administrador @x_george ha aplicado un nuevo ajuste o modificación en el código del bot (Lectura Web). 🚀"
    )
    enviar_telegram(mensaje, chat_target=ADMIN_CHAT_ID)

def obtener_info_desde_web():
    """Extrae el estado y número de jugadores directamente analizando la página web oficial."""
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        response = requests.get(WEB_URL, headers=headers, timeout=5)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            texto_pagina = soup.get_text()
            
            # Buscamos la sección del Servidor 1 en el texto de la web
            # El formato en la web suele ser "Jugadores conectados: 593/600" o similar
            if "s1.fenixzone.com" in texto_pagina:
                # Extraemos el fragmento donde se menciona el servidor 1
                idx = texto_pagina.find("s1.fenixzone.com")
                fragmento = texto_pagina[idx:idx+150] # Tomamos los caracteres siguientes
                
                # Buscamos la línea de jugadores conectados
                for linea in fragmento.split("\n"):
                    if "Jugadores conectados:" in linea:
                        partes = linea.split(":")[-1].strip().split("/")
                        players = int(partes[0].strip())
                        maxplayers = int(partes[1].strip())
                        return {"online": True, "players": players, "maxplayers": maxplayers, "ping": 15}
            
            # Método alternativo por si cambia la estructura de texto exacto
            for el in soup.find_all(text=True):
                if "s1.fenixzone.com" in el:
                    # Buscamos en elementos cercanos
                    parent = el.parent.parent if el.parent else None
                    if parent:
                        parent_text = parent.get_text()
                        if "/" in parent_text and "Jugadores" in parent_text:
                            # Intentamos aislar los números
                            import re
                            nums = re.findall(r'\d+/\d+', parent_text)
                            if nums:
                                p_act, p_max = nums[0].split('/')
                                return {"online": True, "players": int(p_act), "maxplayers": int(p_max), "ping": 15}
                                
    except Exception as e:
        print(f"Error leyendo la web de FénixZone: {e}")
        
    # Plan de respaldo: si falla la web, usamos el socket UDP tradicional de respaldo
    return obtener_info_servidor_udp()

def obtener_info_servidor_udp():
    """Respaldo mediante socket UDP por si la página web llegara a estar en mantenimiento."""
    try:
        ip_resuelta = socket.gethostbyname(IP_SERVIDOR)
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(2)
        
        ip_bytes = socket.inet_aton(ip_resuelta)
        port_bytes = PUERTO_SERVIDOR.to_bytes(2, 'little')
        query = b"SAMP" + ip_bytes + port_bytes + b"i"
        
        start_time = time.time()
        sock.sendto(query, (ip_resuelta, PUERTO_SERVIDOR))
        data, _ = sock.recvfrom(2048)
        latencia = int((time.time() - start_time) * 1000)
        sock.close()
        
        if len(data) > 10:
            i = 11
            password = data[i]
            i += 1
            players = int.from_bytes(data[i:i+2], 'little')
            i += 2
            maxplayers = int.from_bytes(data[i:i+2], 'little')
            
            return {"online": True, "players": players, "maxplayers": maxplayers, "ping": latencia}
    except Exception:
        pass
    
    return {"online": False, "players": 0, "maxplayers": 0, "ping": 0}

def generar_barra(actual, maximo, largo=10):
    porcentaje = actual / maximo if maximo > 0 else 0
    lleno = int(round(largo * porcentaje))
    vacio = largo - lleno
    return "🟩" * lleno + "⬜" * vacio + f" ({int(porcentaje * 100)}%)"

def tiempo_hasta_pago():
    ahora = datetime.now()
    minuto_actual = ahora.minute
    segundo_actual = ahora.second
    
    if minuto_actual < 2:
        minutos_faltantes = 2 - minuto_actual - 1
    else:
        minutos_faltantes = 62 - minuto_actual - 1
        
    segundos_faltantes = 60 - segundo_actual
    if segundos_faltantes == 60:
        segundos_faltantes = 0
        minutos_faltantes += 1
        
    return minutos_faltantes, segundos_faltantes

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
                    texto = message.get("text", "").strip().lower()
                    sender = message.get("from", {})
                    sender_id = str(sender.get("id", ""))
                    first_name = sender.get("first_name", "Desconocido")
                    username = sender.get("username", "Sin username")
                    
                    if texto == "/start" and sender_id:
                        es_nuevo = sender_id not in SUSCRIPTORES
                        SUSCRIPTORES.add(sender_id)
                        
                        respuesta = (
                            "🤖 **¡Bot de Monitoreo FénixZone S1 (Modo Web) Activado!**\n\n"
                            "📌 **Comandos disponibles:**\n"
                            "• `/estado` - Información completa del servidor.\n"
                            "• `/players` - Ver jugadores conectados en vivo desde la web.\n"
                            "• `/pd` - Tiempo restante para el pago diario (:02).\n"
                            "• `/historial` - Ver el registro de últimos reinicios/caídas."
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

                    elif texto in ["/pd", "/pagodiario"] and sender_id:
                        mins, segs = tiempo_hasta_pago()
                        msg_pd = f"💵 **Pago Diario:** Faltan **{mins} min {segs} seg** para la entrega del pago diario (:02)."
                        enviar_telegram(msg_pd, chat_target=sender_id)

                    elif texto in ["/players", "/jugadores"] and sender_id:
                        info = obtener_info_desde_web()
                        if info["online"]:
                            msg_players = f"📊 **FénixZone S1 (Vía Web):**\n\n🟢 En línea\n👥 Jugadores: **{info['players']} / {info['maxplayers']}**"
                        else:
                            msg_players = "🔴 **FénixZone S1** se encuentra actualmente *apagado o inaccesible*."
                        enviar_telegram(msg_players, chat_target=sender_id)

                    elif texto in ["/estado", "/status"] and sender_id:
                        info = obtener_info_desde_web()
                        if info["online"]:
                            barra = generar_barra(info["players"], info["maxplayers"])
                            msg_estado = (
                                f"🌐 **ESTADO DEL SERVIDOR FÉNIXZONE S1**\n\n"
                                f"• **Estado:** 🟢 En Línea (Monitoreo Web)\n"
                                f"• **IP:** `{IP_SERVIDOR}:{PUERTO_SERVIDOR}`\n"
                                f"• **Jugadores:** {info['players']} / {info['maxplayers']}\n"
                                f"• **Capacidad:** {barra}"
                            )
                        else:
                            msg_estado = f"🌐 **ESTADO DEL SERVIDOR FÉNIXZONE S1**\n\n• **Estado:** 🔴 Apagado / Caído\n• **IP:** `{IP_SERVIDOR}:{PUERTO_SERVIDOR}`"
                        enviar_telegram(msg_estado, chat_target=sender_id)

                    elif texto in ["/historial", "/logs"] and sender_id:
                        if HISTORIAL_CAIDAS:
                            registro = "\n".join([f"• {item}" for item in HISTORIAL_CAIDAS[-5:]])
                            msg_logs = f"📜 **Últimos reinicios/caídas detectados:**\n\n{registro}"
                        else:
                            msg_logs = f"📜 **Historial:** No se han detectado caídas o reinicios recientemente."
                        enviar_telegram(msg_logs, chat_target=sender_id)

                    elif texto.startswith("/broadcast") and sender_id == ADMIN_CHAT_ID:
                        partes = message.get("text", "").split(" ", 1)
                        if len(partes) > 1:
                            anuncio = f"📢 **Anuncio Oficial:**\n\n{partes[1]}"
                            enviar_telegram(anuncio, chat_target=None)
                            enviar_telegram("✅ Mensaje enviado con éxito a todos los suscriptores.", chat_target=ADMIN_CHAT_ID)
                        else:
                            enviar_telegram("⚠️ Uso incorrecto. Escribe por ejemplo: `/broadcast Hola a todos`", chat_target=ADMIN_CHAT_ID)
                            
        except Exception as e:
            print(f"Error en polling de Telegram: {e}")
            
        time.sleep(2)

def monitorear():
    estado_anterior = True
    alerta_bajos_enviada = False
    hora_caida = None
    print("Iniciando monitoreo web de FénixZone S1 (cada 5 segundos)...")
    
    while True:
        info = obtener_info_desde_web()
        esta_online = info["online"]
        jugadores = info["players"]
        
        if esta_online and not estado_anterior:
            hora_reinicio = datetime.now().strftime("%H:%M:%S")
            mensaje = "🚨 **El servidor se ha reiniciado y ya esta disponible**"
            enviar_telegram(mensaje, chat_target=None)
            
            if hora_caida:
                HISTORIAL_CAIDAS.append(f"Reinicio el {datetime.now().strftime('%d/%m')} - Caído a las {hora_caida}, Online a las {hora_reinicio}")
            else:
                HISTORIAL_CAIDAS.append(f"Reinicio el {datetime.now().strftime('%d/%m')} a las {hora_reinicio}")
                
            estado_anterior = True
            alerta_bajos_enviada = False
            hora_caida = None
            
        elif not esta_online and estado_anterior:
            hora_caida = datetime.now().strftime("%H:%M:%S")
            mensaje = "⚠️ **FénixZone S1 se ha caído / apagado.** Monitoreando..."
            enviar_telegram(mensaje, chat_target=None)
            estado_anterior = False
            alerta_bajos_enviada = False

        if esta_online and jugadores > 0:
            if jugadores < 300 and not alerta_bajos_enviada:
                msg_aviso = f"⚠️ **¡Atención!** Los jugadores en la web bajaron a **{jugadores}**. Posible reinicio inminente..."
                enviar_telegram(msg_aviso, chat_target=None)
                alerta_bajos_enviada = True
            elif jugadores >= 320:
                alerta_bajos_enviada = False
            
        # Al ser lectura web, hacemos una pausa de 5 o 10 segundos para no saturar la página oficial
        time.sleep(5)

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    threading.Thread(target=auto_ping, daemon=True).start()
    threading.Thread(target=escuchar_mensajes, daemon=True).start()
    threading.Thread(target=notificar_actualizacion, daemon=True).start()
    monitorear()
