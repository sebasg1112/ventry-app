import streamlit as st
from datetime import datetime, timedelta
import qrcode
from io import BytesIO
import cv2
import numpy as np
import gspread
import json
import pandas as pd
import uuid
import base64
import urllib.parse
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- CONFIGURACIÓN DE LA PÁGINA ---
icono_url = "https://i.ibb.co/t7xWXXR/logo.png"
st.set_page_config(page_title="Ventry - Control de Acceso", page_icon=icono_url, layout="centered")

# --- CONVERSIÓN A PWA (APP MÓVIL NATIVA) ---
manifest_json = f"""
{{
  "name": "Ventry System",
  "short_name": "Ventry",
  "theme_color": "#0a0a0a",
  "background_color": "#0a0a0a",
  "display": "standalone",
  "orientation": "portrait",
  "scope": "/",
  "start_url": "/",
  "icons": [
    {{
      "src": "{icono_url}",
      "sizes": "512x512",
      "type": "image/png",
      "purpose": "any maskable"
    }}
  ]
}}
"""
manifest_b64 = base64.b64encode(manifest_json.encode('utf-8')).decode('utf-8')

st.markdown(f"""
    <head>
        <link rel="manifest" href="data:application/json;base64,{manifest_b64}">
        <meta name="theme-color" content="#0a0a0a">
        <link rel="apple-touch-icon" href="{icono_url}">
        <meta name="apple-mobile-web-app-capable" content="yes">
        <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
        <meta name="apple-mobile-web-app-title" content="Ventry">
    </head>
""", unsafe_allow_html=True)

# --- CSS AVANZADO: BLINDAJE NUCLEAR Y DISEÑO PREMIUM ---
st.markdown("""
    <style>
    #MainMenu {display: none;}
    footer {display: none;}
    [data-testid="collapsedControl"] {display: none;} 
    section[data-testid="stSidebar"] {display: none !important;} 
    
    .stApp { background-color: #0d0d0d; color: #f5f5f5; }
    h1, h2, h3, h4, h5, h6, p, span, label, div { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; }
    
    label, label p, label div, div[data-testid="stWidgetLabel"] p, .stTextInput p, .stSelectbox p, .stDateInput p, .stNumberInput p { color: #ffffff !important; font-weight: 600 !important; letter-spacing: 0.5px; }
    
    [data-testid="stForm"] { background-color: #0d0d0d !important; border: 1px solid #333 !important; border-radius: 15px !important; padding: 20px !important; }
    .stTextInput input, .stNumberInput input, .stDateInput input, textarea { background-color: #1a1a1a !important; color: #ffffff !important; -webkit-text-fill-color: #ffffff !important; }
    div[data-baseweb="input"] > div, div[data-baseweb="select"] > div, div[data-baseweb="base-input"] { background-color: #1a1a1a !important; border-radius: 10px !important; border: 1px solid #333 !important; color: #ffffff !important; }
    div[data-baseweb="select"] span { color: #ffffff !important; }
    div[data-baseweb="popover"] > div, div[data-baseweb="menu"] *, ul[role="listbox"] *, li[role="option"] *, div[role="dialog"] *, div[data-baseweb="calendar"] * { background-color: #1a1a1a !important; color: #ffffff !important; }
    div[data-testid="stPopoverBody"] { background-color: #1a1a1a !important; border: 1px solid #333 !important; border-radius: 15px !important; padding: 15px !important; }
    li[role="option"]:hover *, li[role="option"][aria-selected="true"] * { background-color: #FF6600 !important; color: #ffffff !important; }
    div[data-baseweb="input"]:focus-within, div[data-baseweb="select"]:focus-within { border-color: #FF6600 !important; box-shadow: 0 0 8px rgba(255, 102, 0, 0.4) !important; }

    /* BOTONES */
    .stButton>button[kind="primary"], .stFormSubmitButton>button { width: 100%; border-radius: 20px !important; background: #FF6600 !important; color: #ffffff !important; font-weight: 700 !important; letter-spacing: 0.5px; border: none !important; padding: 12px !important; box-shadow: 0 4px 15px rgba(255, 102, 0, 0.3) !important; transition: all 0.2s ease-in-out; justify-content: center !important; }
    .stButton>button[kind="primary"]:active, .stFormSubmitButton>button:active { background: #e65c00 !important; transform: scale(0.98); }
    .btn-secundario>div>button { background: transparent !important; border: 1px solid #555 !important; color: #aaa !important; justify-content: center !important; box-shadow: none !important; }
    .btn-secundario>div>button:hover { border-color: #FF6600 !important; color: #FF6600 !important; }
    .btn-logout>div>button { background: transparent !important; border: none !important; color: #ff4d4d !important; justify-content: center !important; box-shadow: none !important; font-weight: 600 !important; padding: 5px !important; opacity: 0.8; }
    .btn-logout>div>button:hover { opacity: 1; color: #ff1a1a !important; text-decoration: underline; }
    .btn-peligro>div>button { background: rgba(220, 53, 69, 0.1) !important; border: 1px solid rgba(220, 53, 69, 0.5) !important; color: #ff6b6b !important; justify-content: center !important; box-shadow: none !important; }
    
    div[data-testid="stPopover"] > button { background: transparent !important; border: none !important; color: #ffffff !important; font-size: 20px !important; padding: 0 !important; box-shadow: none !important; display: inline-block !important; margin-top: -5px; }
    
    /* NAV BAR */
    .block-container { padding-bottom: 120px !important; }
    div.stRadio { position: fixed !important; bottom: 0 !important; left: 0 !important; width: 100% !important; background-color: rgba(13, 13, 13, 0.95) !important; backdrop-filter: blur(20px) !important; border-top: 1px solid rgba(255, 255, 255, 0.05) !important; padding: 15px 0px 25px 0px !important; z-index: 99999 !important; }
    div.stRadio > div[role="radiogroup"] { display: flex !important; flex-direction: row !important; justify-content: space-evenly !important; align-items: center !important; gap: 0 !important; }
    div.stRadio > div[role="radiogroup"] > label { background: transparent !important; border: none !important; padding: 5px 10px !important; margin: 0 !important; cursor: pointer; }
    div.stRadio > div[role="radiogroup"] > label > div:first-child, div.stRadio > div[role="radiogroup"] > label span[data-baseweb="radio"], div.stRadio > div[role="radiogroup"] > label div[data-baseweb="radio"] { display: none !important; }
    div.stRadio > div[role="radiogroup"] > label div { color: #777777 !important; font-size: 11px !important; font-weight: 600 !important; text-transform: uppercase; letter-spacing: 1px; }
    div.stRadio > div[role="radiogroup"] > label[data-checked="true"] div { color: #FF6600 !important; font-weight: 800 !important; }

    /* CARDS */
    .wallet-card { background: linear-gradient(145deg, #1a1a1a, #0d0d0d); border: 1px solid #333; padding: 20px; border-radius: 15px; text-align: center; margin-bottom: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.4); }
    .wallet-title { color: #888; font-size: 12px; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 5px; font-weight: bold; }
    .wallet-saldo { color: #4ade80 !important; font-size: 32px; font-weight: 800; margin: 0; }
    .wallet-invites { color: #00a8ff !important; font-size: 32px; font-weight: 800; margin: 0; }
    .historial-card { background: #1a1a1a; padding: 15px; border-radius: 12px; margin-bottom: 10px; border-left: 3px solid #FF6600; }
    .monitor-card { background: #111; padding: 12px 20px; border-radius: 8px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center; border: 1px solid #222; border-left: 4px solid #4ade80;}
    .monitor-card-invitado { border-left: 4px solid #00a8ff; }

    /* RECIBO */
    .receipt-card { background: #1a1a1a; border: 1px solid #333; border-top: 5px solid #4ade80; border-radius: 10px; padding: 30px; width: 100%; max-width: 350px; margin: 0 auto; box-shadow: 0 10px 30px rgba(0,0,0,0.5); }
    .receipt-header { text-align: center; border-bottom: 1px dashed #444; padding-bottom: 15px; margin-bottom: 15px; }
    .receipt-amount { font-size: 36px; color: #4ade80; font-weight: 900; margin: 10px 0; }
    .receipt-row { display: flex; justify-content: space-between; margin-bottom: 10px; font-size: 14px; }
    .receipt-label { color: #888; }
    .receipt-value { color: #fff; font-weight: bold; text-align: right; }

    .open-button-container { display: flex; justify-content: center; margin-top: 40px; margin-bottom: 20px;}
    .open-button-glow { border-radius: 50%; padding: 8px; background: radial-gradient(circle, rgba(255,102,0,0.4) 0%, rgba(0,0,0,0) 70%); box-shadow: 0 0 60px rgba(255,102,0,0.3); }
    .open-button { background: linear-gradient(145deg, #222222, #0a0a0a); border: 2px solid #FF6600; border-radius: 50%; width: 200px; height: 200px; display: flex; flex-direction: column; justify-content: center; align-items: center; color: white; cursor: pointer; box-shadow: inset 0 0 25px rgba(0,0,0,0.9); transition: transform 0.1s ease; }
    .open-button:active { background: #FF6600; transform: scale(0.96); }
    
    .dark-wrapper { background-color: transparent; padding: 20px 0px; display: flex; justify-content: center; margin-bottom: 30px; }
    .glass-card { background: rgba(0, 25, 51, 0.4); backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px); border: 1px solid rgba(212, 175, 55, 0.3); border-radius: 20px; padding: 40px 30px; width: 100%; max-width: 360px; box-shadow: 0 15px 35px rgba(0,0,0,0.8); position: relative; overflow: hidden; }
    .magnum-logo { text-align: center; margin-bottom: 35px; }
    .logo-m { font-size: 50px; font-weight: 300; margin: 0; line-height: 1; color: #ffffff !important; }
    .logo-magnum { font-size: 16px; font-weight: 600; letter-spacing: 5px; margin: 5px 0 0 0; color: #ffffff !important; }
    .logo-city { font-size: 9px; letter-spacing: 2px; color: #d4af37 !important; margin: 0; text-transform: uppercase; } 
    .logo-line { width: 30px; height: 1px; background-color: #d4af37; margin: 15px auto 0 auto; }
    .info-group { margin-bottom: 18px; border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 8px; }
    .info-label { font-size: 12px; color: #8892b0 !important; margin-bottom: 4px; text-transform: uppercase; letter-spacing: 1px;}
    .info-value { font-size: 18px; font-weight: 500; color: #ffffff !important; }
    .qr-container { text-align: center; margin-top: 30px; }
    .qr-box { background: rgba(255,255,255,0.95); padding: 10px; border-radius: 12px; display: inline-block; margin-bottom: 15px; }
    .qr-box img { width: 140px; display: block; }
    .status-badge { display: inline-block; padding: 6px 18px; border-radius: 30px; font-size: 12px; font-weight: 700; color: #000 !important; letter-spacing: 1px;}
    .badge-aldia { background: #4ade80 !important; }
    .badge-moroso { background: #ff6b6b !important; color: white !important;}
    .badge-pendiente { background: #ffc107 !important; }
    </style>
""", unsafe_allow_html=True)

# --- MOTOR DE BASE DE DATOS ---
@st.cache_resource
def conectar_google_sheets():
    if "google_credentials" in st.secrets:
        cred_dict = json.loads(st.secrets["google_credentials"])
        gc = gspread.service_account_from_dict(cred_dict)
    else:
        gc = gspread.service_account(filename="credenciales.json")
    doc = gc.open("Ventry_BD")
    return (doc.worksheet("Socios Magnum City Club"), doc.worksheet("Invitaciones"), doc.worksheet("Pagos"), doc.worksheet("Directorio"), doc.worksheet("Historial"))

try:
    hoja_bd, hoja_invitaciones, hoja_pagos, hoja_directorio, hoja_historial = conectar_google_sheets()
except Exception as e:
    st.error(f"Error conectando a Google Sheets: {e}")
    st.stop()

# --- FUNCIONES ---
def calcular_edad(fecha_nac_str):
    if not fecha_nac_str: return 0
    try:
        fecha_nac = datetime.strptime(fecha_nac_str, "%d/%m/%Y").date()
        hoy = datetime.today().date()
        return hoy.year - fecha_nac.year - ((hoy.month, hoy.day) < (fecha_nac.month, fecha_nac.day))
    except: return 0

# --- NUEVO: FUNCIONES DE TIEMPO Y FACTURACIÓN ---
def mes_actual_str():
    return datetime.now().strftime("%m/%Y")

def proximo_mes_str():
    hoy = datetime.now()
    next_m = hoy.month + 1 if hoy.month < 12 else 1
    next_y = hoy.year if hoy.month < 12 else hoy.year + 1
    return f"{next_m:02d}/{next_y}"

def cargar_bd():
    registros = hoja_bd.get_all_records()
    datos = {}
    for fila in registros:
        ced = str(fila.get("cedula", ""))
        if ced: 
            datos[ced] = {
                "nombre": str(fila.get("nombre", "")), "clave": str(fila.get("clave", "")), 
                "accion": str(fila.get("accion", "")), "rol": str(fila.get("rol", "")), 
                "parentesco": str(fila.get("parentesco", "N/A")), "fecha_nacimiento": str(fila.get("fecha_nacimiento", "")), 
                "solvencia": str(fila.get("solvencia", "Pendiente")), "saldo": float(fila.get("saldo", 0.0)),
                "invitaciones": int(fila.get("invitaciones", 0)), "mes_pagado": str(fila.get("mes_pagado", "08/2026")),
                "cedula": ced
            }
    return datos

def guardar_bd(datos):
    lista_socios = list(datos.values())
    lista_socios.sort(key=lambda x: (x.get("accion", ""), x.get("rol", "")), reverse=True) 
    filas_a_subir = [["cedula", "nombre", "clave", "accion", "rol", "parentesco", "fecha_nacimiento", "solvencia", "saldo", "invitaciones", "mes_pagado"]]
    for socio in lista_socios: filas_a_subir.append([socio["cedula"], socio["nombre"], socio["clave"], socio["accion"], socio["rol"], socio["parentesco"], socio.get("fecha_nacimiento", ""), socio.get("solvencia", "Pendiente"), float(socio.get("saldo", 0.0)), int(socio.get("invitaciones", 0)), socio.get("mes_pagado", "")])
    hoja_bd.clear()
    hoja_bd.update(values=filas_a_subir, range_name="A1")
    st.session_state.db_socios = datos

def cargar_invitaciones():
    try: return {str(f["id_qr"]): f for f in hoja_invitaciones.get_all_records() if str(f.get("id_qr", ""))}
    except: return {}

def guardar_bd_invitaciones(datos):
    filas = [["id_qr", "accion", "fecha_visita", "cedula_invitado", "nombre_invitado", "fecha_nacimiento", "correo", "estatus"]]
    for k, v in datos.items(): filas.append([k, v["accion"], v["fecha_visita"], v["cedula_invitado"], v["nombre_invitado"], v.get("fecha_nacimiento", ""), v.get("correo", ""), v["estatus"]])
    hoja_invitaciones.clear()
    hoja_invitaciones.update(values=filas, range_name="A1")
    st.session_state.db_invitaciones = datos

def cargar_pagos():
    try: 
        registros = hoja_pagos.get_all_records()
        datos = {}
        for f in registros:
            id_p = str(f.get("id_pago", ""))
            if id_p: datos[id_p] = {"accion": str(f.get("accion", "")), "metodo": str(f.get("metodo", "")), "referencia": str(f.get("referencia", "")), "monto": str(f.get("monto", "")), "fecha_reporte": str(f.get("fecha_reporte", "")), "estatus": str(f.get("estatus", "")), "tipo": str(f.get("tipo", "Abono a Billetera"))}
        return datos
    except: return {}

def guardar_bd_pagos(datos):
    filas = [["id_pago", "accion", "metodo", "referencia", "monto", "fecha_reporte", "estatus", "tipo"]]
    for k, v in datos.items(): filas.append([k, v["accion"], v["metodo"], v["referencia"], v["monto"], v["fecha_reporte"], v["estatus"], v.get("tipo", "Abono a Billetera")])
    hoja_pagos.clear()
    hoja_pagos.update(values=filas, range_name="A1")
    st.session_state.db_pagos = datos

def cargar_historial():
    try:
        vals = hoja_historial.get_all_values()
        if len(vals) > 1: return [{"fecha": r[0], "accion": r[1], "nombre": r[2], "via": r[3], "movimiento": r[4]} for r in vals[1:][::-1]]
        return []
    except: return []

def registrar_acceso(nombre, accion, via, movimiento):
    hora_actual = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    hoja_historial.append_row([hora_actual, str(accion), nombre, via, movimiento])
    if "db_historial" not in st.session_state: st.session_state.db_historial = []
    st.session_state.db_historial.insert(0, {"fecha": hora_actual, "accion": str(accion), "nombre": nombre, "via": via, "movimiento": movimiento})

def cargar_directorio():
    try:
        registros = hoja_directorio.get_all_records()
        datos = {}
        for f in registros:
            acc = str(f.get("accion", ""))
            ced = str(f.get("cedula_invitado", ""))
            if acc and ced:
                if acc not in datos: datos[acc] = {}
                datos[acc][ced] = {"nombre": str(f.get("nombre_invitado", "")), "correo": str(f.get("correo", "")), "fecha_nacimiento": str(f.get("fecha_nacimiento", ""))}
        return datos
    except: return {}

def guardar_bd_directorio(datos):
    filas = [["accion", "cedula_invitado", "nombre_invitado", "correo", "fecha_nacimiento"]]
    for acc, invitados in datos.items():
        for ced, info in invitados.items(): filas.append([acc, ced, info["nombre"], info["correo"], info.get("fecha_nacimiento", "")])
    hoja_directorio.clear()
    hoja_directorio.update(values=filas, range_name="A1")
    st.session_state.db_directorio = datos

# --- BLINDAJE DE MEMORIA ---
if "db_socios" not in st.session_state: st.session_state.db_socios = cargar_bd()
if "db_invitaciones" not in st.session_state: st.session_state.db_invitaciones = cargar_invitaciones()
if "db_pagos" not in st.session_state: st.session_state.db_pagos = cargar_pagos()
if "db_directorio" not in st.session_state: st.session_state.db_directorio = cargar_directorio()
if "db_historial" not in st.session_state: st.session_state.db_historial = cargar_historial()

BASE_DATOS_SOCIOS = st.session_state.db_socios
BASE_DATOS_INVITACIONES = st.session_state.db_invitaciones
BASE_DATOS_PAGOS = st.session_state.db_pagos
BASE_DATOS_DIRECTORIO = st.session_state.db_directorio

if "logueado" not in st.session_state: st.session_state.logueado = False
if "usuario_actual" not in st.session_state: st.session_state.usuario_actual = None
if "pantalla_auth" not in st.session_state: st.session_state.pantalla_auth = "login"

# ==========================================
# 🛑 INTERCEPTOR DE PASES DIGITALES
# ==========================================
params = st.query_params
if "pase" in params:
    id_pase_url = params["pase"]
    if id_pase_url in BASE_DATOS_INVITACIONES:
        pase = BASE_DATOS_INVITACIONES[id_pase_url]
        datos_qr = f"INVITADO|{id_pase_url}"
        img = qrcode.make(datos_qr)
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        if pase["estatus"] == "Activo": clase_badge = "badge-aldia"; texto_badge = "PASE VÁLIDO"
        elif pase["estatus"] == "Adentro": clase_badge = "badge-aldia"; texto_badge = "EN INSTALACIONES"
        else: clase_badge = "badge-moroso"; texto_badge = pase["estatus"].upper()
            
        if pase["fecha_visita"] != datetime.now().strftime("%d/%m/%Y") and pase["estatus"] == "Activo":
            clase_badge = "badge-pendiente"; texto_badge = "FECHA INVÁLIDA"

        st.markdown(f"""
<div class="dark-wrapper" style="margin-top: 50px;">
<div class="glass-card">
<div class="magnum-logo">
<p class="logo-m">M</p>
<p class="logo-magnum">MAGNUM</p>
<p class="logo-city">CITY CLUB</p>
<div class="logo-line"></div>
</div>
<div style="text-align:center; color:#d4af37; font-size:12px; font-weight:bold; letter-spacing:2px; margin-bottom:20px;">PASE DE INVITADO</div>
<div class="info-group"><p class="info-label">Invitado</p><p class="info-value">{pase['nombre_invitado']}</p></div>
<div class="info-group"><p class="info-label">Válido para el día</p><p class="info-value">{pase['fecha_visita']}</p></div>
<div class="info-group"><p class="info-label">Autorizado por (Acción)</p><p class="info-value">{pase['accion']}</p></div>
<div class="qr-container"><div class="qr-box"><img src="data:image/png;base64,{img_str}"></div><br><span class="status-badge {clase_badge}">{texto_badge}</span></div>
</div></div>
""", unsafe_allow_html=True)
        st.info("💡 Muestra esta pantalla en garita al llegar al club.")
    else: st.error("❌ Enlace de pase inválido o vencido.")
    st.stop()

# ==========================================
# PANTALLA INICIAL: LOGIN Y REGISTRO
# ==========================================
if not st.session_state.logueado:
    st.markdown("""
        <div style='text-align: center; margin-top: 40px; margin-bottom: 20px;'>
            <img src="https://i.ibb.co/t7xWXXR/logo.png" width="90" style="margin-bottom: 15px;">
            <h1 style='font-weight: 800; font-size: 34px; margin-bottom: 0px; letter-spacing: 1px;'>VENTRY</h1>
            <p style='color: #666; font-size: 12px; letter-spacing: 3px; text-transform: uppercase;'>Access Control</p>
        </div>
    """, unsafe_allow_html=True)
    
    if st.session_state.pantalla_auth == "login":
        with st.form("login_form"):
            cedula_ingresada = st.text_input("Email o ID (Cédula)")
            clave_ingresada = st.text_input("Contraseña", type="password")
            st.markdown("<br>", unsafe_allow_html=True)
            boton_entrar = st.form_submit_button("INICIAR SESIÓN")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("<div class='btn-secundario'>", unsafe_allow_html=True)
            if st.button("Crear cuenta", type="primary"):
                st.session_state.pantalla_auth = "registro"
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
        with col2:
            st.markdown("""
                <div style="text-align: center;">
                    <span style="border: 1px solid #333; padding: 11px 0px; border-radius: 20px; color: #aaa; font-size: 13px; cursor: pointer; display:block; margin-top: 1px;" onclick="alert('FaceID/TouchID se activará en la Fase 3 de compilación nativa.')">
                        🔒 FaceID
                    </span>
                </div>
            """, unsafe_allow_html=True)

        if boton_entrar:
            if cedula_ingresada in BASE_DATOS_SOCIOS:
                socio = BASE_DATOS_SOCIOS[cedula_ingresada]
                if clave_ingresada == str(socio["clave"]):
                    if socio.get("solvencia", "") == "En revision":
                        st.warning("⏳ Su cuenta fue creada y está en revisión. Debe esperar aprobación administrativa.")
                    else:
                        st.session_state.logueado = True; st.session_state.usuario_actual = socio; st.rerun()
                else: st.error("❌ Contraseña incorrecta.")
            else: st.error("⚠️ Usuario no registrado.")

    elif st.session_state.pantalla_auth == "registro":
        with st.form("registro_form"):
            st.markdown("<h3 style='text-align:center; font-size:18px; margin-bottom:20px; color:#fff;'>Solicitud de Ingreso</h3>", unsafe_allow_html=True)
            r_cedula = st.text_input("Cédula de Identidad")
            r_nombre = st.text_input("Nombre y Apellido")
            r_nacimiento = st.date_input("Fecha de Nacimiento", min_value=datetime(1920, 1, 1), max_value=datetime.today(), format="DD/MM/YYYY")
            
            col1, col2 = st.columns(2)
            with col1:
                r_accion = st.text_input("Número de Acción")
                r_rol = st.selectbox("Rol en la Acción", ["Titular", "Familiar"])
            with col2:
                r_parentesco = st.selectbox("Parentesco", ["N/A (Titular)", "Esposo(a)", "Hijo(a)", "Madre/Padre", "Hermano(a)", "Otro"])
            
            r_clave = st.text_input("Crea una Contraseña", type="password")
            r_clave_conf = st.text_input("Confirma tu Contraseña", type="password")
            
            st.markdown("<br>", unsafe_allow_html=True)
            btn_registrar = st.form_submit_button("ENVIAR SOLICITUD")
            
        st.markdown("<div class='btn-secundario'>", unsafe_allow_html=True)
        if st.button("← Volver a Iniciar Sesión", type="primary"):
            st.session_state.pantalla_auth = "login"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
            
        if btn_registrar:
            if not r_cedula or not r_nombre or not r_accion or not r_clave: st.error("⚠️ Todos los campos son obligatorios.")
            elif r_clave != r_clave_conf: st.error("❌ Las contraseñas no coinciden.")
            elif r_cedula in BASE_DATOS_SOCIOS: st.error("⚠️ Esta cédula ya se encuentra registrada.")
            else:
                r_acc_norm = r_accion.strip().lstrip('0') or "0"
                titular_existente = any(info["accion"] == r_acc_norm and info["rol"] == "Titular" for info in BASE_DATOS_SOCIOS.values()) if r_rol == "Titular" else False
                
                if titular_existente: st.error(f"⚠️ Operación Denegada: La Acción {r_acc_norm} ya tiene un Titular registrado.")
                else:
                    BASE_DATOS_SOCIOS[r_cedula] = {
                        "nombre": r_nombre, "clave": r_clave, "accion": r_acc_norm, "rol": r_rol, 
                        "parentesco": r_parentesco, "fecha_nacimiento": r_nacimiento.strftime("%d/%m/%Y"), 
                        "solvencia": "En revision", "saldo": 0.0, "invitaciones": 0, "mes_pagado": "", "cedula": r_cedula
                    }
                    guardar_bd(BASE_DATOS_SOCIOS)
                    st.success("✅ Su cuenta fue creada, esta en revision, debe esperar aprobacion.")

# ==========================================
# APP NATIVA INTERNA
# ==========================================
else:
    # 🔴 SOLUCIÓN DE SESIÓN: SIEMPRE LEEMOS LA DB ACTUALIZADA
    if st.session_state.usuario_actual["cedula"] in BASE_DATOS_SOCIOS:
        st.session_state.usuario_actual = BASE_DATOS_SOCIOS[st.session_state.usuario_actual["cedula"]]
        
    socio_actual = st.session_state.usuario_actual
    rol_actual = socio_actual["rol"]

    # 🔴 EXTRACCIÓN DE DATOS FAMILIARES GLOBALES
    saldo_accion = 0.0
    invitaciones_accion = 0
    mes_pagado_accion = ""
    for m in BASE_DATOS_SOCIOS.values():
        if str(m["accion"]) == str(socio_actual["accion"]) and m["rol"] == "Titular":
            saldo_accion = float(m.get('saldo', 0.0))
            invitaciones_accion = int(m.get('invitaciones', 0))
            mes_pagado_accion = str(m.get('mes_pagado', '08/2026')) # Asumimos mes anterior si es nuevo
            break

    # --- HEADER CON CENTRO DE NOTIFICACIONES ---
    col_logo, col_campana = st.columns([5, 1])
    with col_logo:
        st.markdown(f"""
        <div style="display:flex; align-items:center; gap:10px; margin-bottom: 20px;">
            <img src="https://i.ibb.co/t7xWXXR/logo.png" width="25">
            <span style="font-size:16px; font-weight:700; letter-spacing: 1px;">VENTRY</span>
        </div>
        """, unsafe_allow_html=True)
    with col_campana:
        notificaciones = []
        mis_pagos = [p for p in BASE_DATOS_PAGOS.values() if str(p["accion"]) == str(socio_actual["accion"])]
        for p in mis_pagos[-3:]:
            if p["estatus"] == "Aprobado" and p["tipo"] == "Abono a Billetera": notificaciones.append(f"💰 Tu Abono de **${float(p['monto']):.2f}** fue Aprobado.")
            elif p["estatus"] == "Aprobado" and p["tipo"] == "Cargo Mensual": notificaciones.append(f"🧾 Cargo mensual de **${float(p['monto']):.2f}** procesado.")
            elif p["estatus"] == "Rechazado": notificaciones.append(f"❌ Tu Abono de **${float(p['monto']):.2f}** fue Rechazado.")
                
        mis_accesos = [h for h in st.session_state.db_historial if h["accion"] == str(socio_actual["accion"]) and h["movimiento"] == "Entrada"]
        for h in mis_accesos[:3]:
            if "Invitado" in h["via"]: notificaciones.append(f"🎟️ Tu invitado **{h['nombre']}** ingresó al club.")

        with st.popover("🔔"):
            st.markdown("<h4 style='color:#FF6600; font-size:14px; margin-bottom:10px;'>Centro de Notificaciones</h4>", unsafe_allow_html=True)
            if notificaciones:
                for n in notificaciones[:5]: st.markdown(f"<div style='background:#0d0d0d; padding:10px; border-radius:8px; margin-bottom:5px; font-size:12px; border-left:2px solid #FF6600;'>{n}</div>", unsafe_allow_html=True)
            else: st.write("No tienes notificaciones nuevas.")

    # --- DEFINICIÓN DE MENÚ INFERIOR ---
    if rol_actual in ["Titular", "Familiar"]: opciones_menu = ["Inicio", "Invitados", "Carnet", "Pagos", "Ajustes"]
    elif rol_actual == "Vigilante": opciones_menu = ["Garita", "Ajustes"]
    elif rol_actual == "Administrador": opciones_menu = ["Inicio", "Invitados", "Garita", "Admin", "Ajustes"]

    modulo_seleccionado = st.radio("Nav", opciones_menu, horizontal=True, label_visibility="collapsed")

    if modulo_seleccionado == "Admin": st.markdown("<style>.block-container { max-width: 95% !important; padding-top: 2rem !important; }</style>", unsafe_allow_html=True)
    else: st.markdown("<style>.block-container { max-width: 46rem !important; }</style>", unsafe_allow_html=True)

    # --- MÓDULO 1: INICIO ---
    if modulo_seleccionado == "Inicio":
        st.markdown("""
<div style="text-align: center; margin-top: 0px;">
<h2 style="margin-bottom: 5px; font-size:22px; font-weight:800; color:#fff;">Magnum City Club</h2>
<p style="color: #666; font-size:12px; text-transform:uppercase; letter-spacing:2px;">Puerta Principal</p>
<div class="open-button-container">
<div class="open-button-glow">
<div class="open-button">
<span style="font-size: 40px; margin-bottom:10px;">🔒</span>
<span style="font-size: 14px; letter-spacing: 1px;">TOCA PARA ABRIR</span>
</div>
</div>
</div>
<p style="color: #666; margin-top: 30px; font-size:12px; text-transform:uppercase;">Estatus: <span style="color:#FF6600; font-weight:bold;">Cerrado</span></p>
</div>
""", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Simular Apertura (Demo ESP32)", type="primary"): st.success("📡 Señal enviada a garita.")

    # --- MÓDULO 2: CARNET DIGITAL ---
    elif modulo_seleccionado == "Carnet":
        solvencia = socio_actual.get('solvencia', 'Desconocido')
        if solvencia == "Moroso": st.error("⚠️ Tu grupo familiar presenta un saldo pendiente.")
        if solvencia == "Al dia": clase_badge = "badge-aldia"; texto_badge = "AL DÍA"
        elif solvencia == "Pendiente": clase_badge = "badge-pendiente"; texto_badge = "PENDIENTE"
        else: clase_badge = "badge-moroso"; texto_badge = "MOROSO"

        timestamp_actual = int(datetime.now().timestamp())
        datos_qr = f"VENTRY_DYN|{socio_actual['cedula']}|{timestamp_actual}"
        
        img = qrcode.make(datos_qr)
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        img_str = base64.b64encode(buffer.getvalue()).decode()

        st.markdown(f"""
<div class="dark-wrapper">
<div class="glass-card">
<div class="magnum-logo">
<p class="logo-m">M</p>
<p class="logo-magnum">MAGNUM</p>
<p class="logo-city">CITY CLUB</p>
<div class="logo-line"></div>
</div>
<div class="info-group"><p class="info-label">Nombre del Socio</p><p class="info-value">{socio_actual['nombre']}</p></div>
<div class="info-group"><p class="info-label">ID (Cédula)</p><p class="info-value">{socio_actual['cedula']}</p></div>
<div class="info-group"><p class="info-label">Acción</p><p class="info-value">{socio_actual['accion']} <span style="font-size:12px; color:#8892b0; font-weight:normal;">({socio_actual['rol']})</span></p></div>
<div class="qr-container"><div class="qr-box"><img src="data:image/png;base64,{img_str}"></div><br><span class="status-badge {clase_badge}">{texto_badge}</span></div>
</div></div>
""", unsafe_allow_html=True)
        st.info("⏱️ Este código de seguridad es dinámico. Válido por 60 segundos para evitar clonaciones.")
        if st.button("🔄 Actualizar Código QR", type="primary"): st.rerun()

    # --- MÓDULO 3: INVITADOS (CON LÓGICA DE NEGOCIOS: 10 PASES) ---
    elif modulo_seleccionado == "Invitados":
        if "ultimo_pase_generado" not in st.session_state: st.session_state.ultimo_pase_generado = None

        if st.session_state.ultimo_pase_generado:
            pase_temp = st.session_state.ultimo_pase_generado
            url_base = "https://ventry.streamlit.app" 
            link_pase_digital = f"{url_base}/?pase={pase_temp['id']}"
            
            st.success(f"✅ Pase de {pase_temp['nombre']} emitido correctamente.")
            mensaje_ws = f"¡Hola {pase_temp['nombre']}! Aquí tienes tu pase para el *Magnum City Club*.\nFecha: {pase_temp['fecha']}\n👉 Abre tu código QR aquí:\n{link_pase_digital}"
            link_ws = f"https://wa.me/?text={urllib.parse.quote(mensaje_ws)}"
            st.markdown(f'<a href="{link_ws}" target="_blank" style="display:block; text-align:center; background:#25D366; color:white; padding:15px; border-radius:20px; text-decoration:none; font-weight:800; letter-spacing:1px; margin-top:20px; margin-bottom:20px; box-shadow: 0 5px 15px rgba(37, 211, 102, 0.3);">ENVIAR POR WHATSAPP</a>', unsafe_allow_html=True)
            
            st.markdown("<div class='btn-secundario'>", unsafe_allow_html=True)
            if st.button("← Volver a crear otra invitación", type="primary"):
                st.session_state.ultimo_pase_generado = None
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
                
        else:
            st.markdown("<h3 style='font-size:18px; font-weight:700; color:#fff;'>Pases y Accesos</h3>", unsafe_allow_html=True)
            solvencia = socio_actual.get('solvencia', 'Desconocido')
            
            # Verificamos si la familia está solvente el mes actual
            if mes_pagado_accion != mes_actual_str():
                st.error("❌ Operación Denegada. Debes estar al día con el pago del mes actual para invitar.")
            else:
                col1, col2 = st.columns(2)
                with col1: st.markdown(f'<div class="wallet-card" style="padding:10px;"><p class="wallet-title" style="font-size:10px;">Pases Libres</p><h3 class="wallet-invites">{invitaciones_accion}</h3></div>', unsafe_allow_html=True)
                with col2: st.markdown(f'<div class="wallet-card" style="padding:10px;"><p class="wallet-title" style="font-size:10px;">Saldo Ventry</p><h3 class="wallet-saldo" style="font-size:20px;">${saldo_accion:.2f}</h3></div>', unsafe_allow_html=True)
                
                if invitaciones_accion > 0: st.info(f"✨ Tienes {invitaciones_accion} invitaciones de cortesía disponibles. El pase será gratuito.")
                else: st.warning("⚠️ Has agotado tus invitaciones gratuitas del mes. Se debitarán **$10.00** de tu Saldo Ventry por este pase.")
                
                invitados_previos = BASE_DATOS_DIRECTORIO.get(socio_actual["accion"], {})
                modo_ingreso = st.selectbox("Método de registro:", ["📝 Ingresar Nuevo Invitado", "⭐ Seleccionar de Favoritos"])
                n_cedula_def, n_nombre_def, n_correo_def, n_nacimiento_def = "", "", "", datetime.today()
                
                if modo_ingreso == "⭐ Seleccionar de Favoritos":
                    if invitados_previos:
                        inv_sel = st.selectbox("Tu directorio:", list(invitados_previos.keys()), format_func=lambda x: f"{invitados_previos[x]['nombre']} (C.I: {x})")
                        n_cedula_def, n_nombre_def, n_correo_def = inv_sel, invitados_previos[inv_sel]['nombre'], invitados_previos[inv_sel]['correo']
                    else: st.info("Aún no tienes invitados en tu directorio frecuente.")

                with st.form("form_invitacion"):
                    n_cedula_inv = st.text_input("Cédula", value=n_cedula_def)
                    n_nombre_inv = st.text_input("Nombre y Apellido", value=n_nombre_def)
                    n_correo_inv = st.text_input("Correo Electrónico (Opcional)", value=n_correo_def, placeholder="ejemplo@correo.com")
                    fecha_visita = st.date_input("Fecha de acceso", min_value=datetime.today(), format="DD/MM/YYYY")
                    guardar_contacto = False
                    if modo_ingreso == "📝 Ingresar Nuevo Invitado":
                        st.write("")
                        guardar_contacto = st.checkbox("Guardar en mi directorio frecuente", value=True)
                    st.markdown("<br>", unsafe_allow_html=True)
                    btn_generar = st.form_submit_button("GENERAR PASE DIGITAL")
                    
                if btn_generar and n_cedula_inv and n_nombre_inv:
                    # LÓGICA DE COBRO DE INVITACIONES
                    puede_invitar = True
                    
                    if invitaciones_accion > 0:
                        # Descontamos 1 invitación gratis
                        for ced_fam, info_fam in BASE_DATOS_SOCIOS.items():
                            if str(info_fam["accion"]) == str(socio_actual["accion"]) and info_fam["rol"] == "Titular":
                                BASE_DATOS_SOCIOS[ced_fam]["invitaciones"] = invitaciones_accion - 1
                                break
                    else:
                        # Si no hay libres, cobramos $10
                        if saldo_accion >= 10.0:
                            for ced_fam, info_fam in BASE_DATOS_SOCIOS.items():
                                if str(info_fam["accion"]) == str(socio_actual["accion"]) and info_fam["rol"] == "Titular":
                                    BASE_DATOS_SOCIOS[ced_fam]["saldo"] = saldo_accion - 10.0
                                    break
                            # Generar recibo de cobro
                            id_cargo = f"P-INV-{str(uuid.uuid4())[:6].upper()}"
                            BASE_DATOS_PAGOS[id_cargo] = {"accion": socio_actual["accion"], "metodo": "Saldo Ventry", "referencia": "PASE-EXTRA", "monto": 10.0, "fecha_reporte": datetime.now().strftime("%d/%m/%Y"), "estatus": "Aprobado", "tipo": "Cargo Pase Extra"}
                            guardar_bd_pagos(BASE_DATOS_PAGOS)
                        else:
                            puede_invitar = False
                            st.error("❌ Saldo insuficiente. Necesitas al menos $10.00 en tu Billetera Ventry para generar pases adicionales.")
                    
                    if puede_invitar:
                        guardar_bd(BASE_DATOS_SOCIOS)
                        if guardar_contacto:
                            if socio_actual["accion"] not in BASE_DATOS_DIRECTORIO: BASE_DATOS_DIRECTORIO[socio_actual["accion"]] = {}
                            BASE_DATOS_DIRECTORIO[socio_actual["accion"]][n_cedula_inv] = {"nombre": n_nombre_inv, "correo": n_correo_inv, "fecha_nacimiento": n_nacimiento_def.strftime("%d/%m/%Y")}
                            guardar_bd_directorio(BASE_DATOS_DIRECTORIO)
                            
                        str_fecha = fecha_visita.strftime("%d/%m/%Y")
                        id_unico = f"INV-{socio_actual['accion']}-{str(uuid.uuid4())[:6].upper()}"
                        BASE_DATOS_INVITACIONES[id_unico] = {"accion": socio_actual["accion"], "fecha_visita": str_fecha, "cedula_invitado": n_cedula_inv, "nombre_invitado": n_nombre_inv, "fecha_nacimiento": "", "correo": n_correo_inv, "estatus": "Activo"}
                        guardar_bd_invitaciones(BASE_DATOS_INVITACIONES)
                        st.session_state.ultimo_pase_generado = {"id": id_unico, "nombre": n_nombre_inv, "fecha": str_fecha, "correo": n_correo_inv}
                        st.rerun()

    # --- MÓDULO 4: PAGOS (BILLETERA FAMILIAR & LÓGICA DE NEGOCIOS) ---
    elif modulo_seleccionado == "Pagos":
        
        edad_usuario = calcular_edad(socio_actual.get("fecha_nacimiento", ""))
        if edad_usuario < 18 and edad_usuario > 0:
            st.markdown("<h3 style='font-size:22px; font-weight:800; color:#fff; margin-bottom: 20px;'>Billetera Ventry</h3>", unsafe_allow_html=True)
            st.error("🔒 Acceso Restringido: El módulo financiero es exclusivo para los usuarios mayores de edad.")
            
        else:
            if "sub_pagos" not in st.session_state: st.session_state.sub_pagos = "menu"
            if "recibo_id" not in st.session_state: st.session_state.recibo_id = None

            saldo_favor = saldo_accion if saldo_accion > 0 else 0.0
            
            if st.session_state.sub_pagos == "menu":
                st.markdown("<h3 style='font-size:22px; font-weight:800; color:#fff; margin-bottom: 20px;'>Billetera Ventry</h3>", unsafe_allow_html=True)
                st.markdown(f'<div class="wallet-card"><p class="wallet-title">Fondo Familiar Disponible</p><h3 class="wallet-saldo" style="font-size:40px;">${saldo_favor:.2f}</h3></div>', unsafe_allow_html=True)

                st.write("")
                
                # 🔴 LÓGICA DE NEGOCIO DEL CLUB: EL PAGO DEL MES
                if rol_actual == "Titular":
                    mes_actual = mes_actual_str()
                    dia_actual = datetime.now().day
                    
                    if mes_pagado_accion == mes_actual:
                        st.success("🎉 Tu Acción está solvente este mes.")
                        if st.button(f"Adelantar Cuota de {proximo_mes_str()}", type="primary"): st.session_state.sub_pagos = "pagar"; st.rerun()
                    else:
                        if dia_actual <= 10:
                            st.info(f"🌟 Beneficio de Pronto Pago (Días 1-10). Cuota: **$104**. Incluye **10 Pases Gratis**.")
                        else:
                            st.warning(f"⚠️ Fecha de corte superada. Cuota: **$120**. No incluye pases gratis.")
                        
                        if st.button("Pagar Cuota de Mantenimiento", type="primary"): st.session_state.sub_pagos = "pagar"; st.rerun()
                    st.write("")
                else:
                    st.info("ℹ️ El pago de la cuota de mantenimiento es gestionado por el Titular de la acción.")
                
                if st.button("📥 Reportar Abono / Depósito", type="primary"): st.session_state.sub_pagos = "recargar"; st.rerun()
                st.write("")
                if st.button("🕒 Libro de Transacciones", type="primary"): st.session_state.sub_pagos = "historial"; st.rerun()

            elif st.session_state.sub_pagos == "recargar":
                st.markdown("<h3 style='font-size:20px; font-weight:800; color:#FF6600;'>Reportar Abono</h3>", unsafe_allow_html=True)
                st.write("Recarga saldo a favor en la billetera de tu familia.")
                
                with st.form("form_recarga"):
                    metodo_r = st.selectbox("Método de Pago", ["Pago Móvil (Ej. Mercantil, Banesco, etc.)", "Transferencia Nacional", "Zelle", "Efectivo en Taquilla"])
                    ref_r = st.text_input("Nº de Referencia (Deje en blanco si es efectivo)")
                    monto_r = st.number_input("Monto depositado ($)", min_value=1.0)
                    st.markdown("<br>", unsafe_allow_html=True)
                    btn_recarga = st.form_submit_button("ENVIAR REPORTE")
                    
                if btn_recarga:
                    if "Efectivo" not in metodo_r and not ref_r:
                        st.error("⚠️ Ingrese el número de referencia de su transferencia o Zelle.")
                    else:
                        ref_final = ref_r if ref_r else "EFECTIVO-TAQ"
                        id_pago = f"ABN-{str(uuid.uuid4())[:6].upper()}"
                        BASE_DATOS_PAGOS[id_pago] = {"accion": socio_actual["accion"], "metodo": metodo_r, "referencia": ref_final, "monto": monto_r, "fecha_reporte": datetime.now().strftime("%d/%m/%Y"), "estatus": "En Revisión", "tipo": "Abono a Billetera"}
                        guardar_bd_pagos(BASE_DATOS_PAGOS)
                        st.success("✅ Reporte enviado. El saldo se actualizará tras la aprobación administrativa.")
                
                st.write("")
                st.markdown("<div class='btn-secundario'>", unsafe_allow_html=True)
                if st.button("← Volver a Billetera", type="primary"): st.session_state.sub_pagos = "menu"; st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

            elif st.session_state.sub_pagos == "pagar":
                mes_actual = mes_actual_str()
                dia_actual = datetime.now().day
                
                es_adelanto = (mes_pagado_accion == mes_actual)
                mes_a_cobrar = proximo_mes_str() if es_adelanto else mes_actual
                
                if dia_actual <= 10 or es_adelanto:
                    monto_cobro = 104.0
                    invites_premio = 10
                    tipo_cobro = "Cargo Mensual (Pronto Pago)"
                else:
                    monto_cobro = 120.0
                    invites_premio = 0
                    tipo_cobro = "Cargo Mensual (Tardío)"
                
                st.markdown(f"<h3 style='font-size:20px; font-weight:800; color:#FF6600;'>Pago de Mantenimiento ({mes_a_cobrar})</h3>", unsafe_allow_html=True)
                
                if saldo_accion >= monto_cobro:
                    st.info(f"💡 Tienes suficiente Saldo Ventry. Se debitarán **${monto_cobro:.2f}** de tu Billetera Familiar.")
                    if st.button("Pagar Cuota Automáticamente", type="primary"):
                        # Descontamos el dinero, actualizamos el mes y damos el premio de invitaciones
                        nuevo_saldo = saldo_accion - monto_cobro
                        for ced, info in BASE_DATOS_SOCIOS.items():
                            if str(info["accion"]) == str(socio_actual["accion"]) and info["rol"] == "Titular":
                                BASE_DATOS_SOCIOS[ced]["saldo"] = nuevo_saldo
                                BASE_DATOS_SOCIOS[ced]["mes_pagado"] = mes_a_cobrar
                                # Solo sumamos las nuevas si pagó a tiempo
                                BASE_DATOS_SOCIOS[ced]["invitaciones"] = int(info.get('invitaciones',0)) + invites_premio
                                break
                        
                        # Actualizar solvencia de toda la familia
                        for ced_fam, info_fam in BASE_DATOS_SOCIOS.items():
                            if str(info_fam["accion"]) == str(socio_actual["accion"]):
                                BASE_DATOS_SOCIOS[ced_fam]["solvencia"] = "Al dia"
                        
                        guardar_bd(BASE_DATOS_SOCIOS)
                        
                        # Generamos el recibo de Cargo
                        id_cargo = f"CRG-{str(uuid.uuid4())[:6].upper()}"
                        BASE_DATOS_PAGOS[id_cargo] = {"accion": socio_actual["accion"], "metodo": "Sistema Ventry", "referencia": f"CUOTA-{mes_a_cobrar.replace('/','-')}", "monto": monto_cobro, "fecha_reporte": datetime.now().strftime("%d/%m/%Y"), "estatus": "Aprobado", "tipo": tipo_cobro}
                        guardar_bd_pagos(BASE_DATOS_PAGOS)
                        
                        st.success(f"✅ Cuota pagada exitosamente. Se te han habilitado {invites_premio} invitaciones de cortesía.")
                        st.rerun()
                else:
                    st.error(f"❌ Saldo Insuficiente. Necesitas **${monto_cobro:.2f}** para pagar este mes. Regresa y reporta un Abono a tu billetera primero.")
                
                st.write("")
                st.markdown("<div class='btn-secundario'>", unsafe_allow_html=True)
                if st.button("← Volver a Billetera", type="primary"): st.session_state.sub_pagos = "menu"; st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

            elif st.session_state.sub_pagos == "historial":
                st.markdown("<h3 style='font-size:20px; font-weight:800; color:#FF6600;'>Libro de Transacciones</h3>", unsafe_allow_html=True)
                mis_pagos = {k: v for k, v in BASE_DATOS_PAGOS.items() if str(v["accion"]) == str(socio_actual["accion"])}
                mis_pagos_lista = list(mis_pagos.items())[::-1]
                
                if mis_pagos_lista:
                    for p_id, p_info in mis_pagos_lista:
                        es_cargo = "Cargo" in p_info.get('tipo', '')
                        
                        if es_cargo: color_status = "#ff6b6b"
                        elif p_info['estatus'] == "Aprobado": color_status = "#4ade80"
                        elif p_info['estatus'] == "En Revisión": color_status = "#FF6600"
                        else: color_status = "#ff6b6b"
                        
                        signo = "-" if es_cargo else "+"
                        monto_str = f"{signo}${float(p_info['monto']):.2f}"
                        
                        st.markdown(f"""
                        <div style='background:#1a1a1a; padding:15px; border-radius:12px; margin-bottom:10px; border-left: 3px solid {color_status};'>
                            <div style='display:flex; justify-content:space-between; margin-bottom:5px;'>
                                <b style='color:#fff;'>{p_info.get('tipo', 'Abono a Billetera')}</b>
                                <b style='color:{color_status};'>{monto_str}</b>
                            </div>
                            <span style='color:#aaa; font-size:12px;'>Fecha: {p_info['fecha_reporte']} | Vía: {p_info['metodo']}</span><br>
                            <span style='color:{color_status}; font-size:11px; font-weight:bold; text-transform:uppercase;'>Estatus: {p_info['estatus']}</span>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        if not es_cargo and p_info['estatus'] == "Aprobado":
                            st.markdown("<div class='btn-secundario' style='margin-bottom: 15px;'>", unsafe_allow_html=True)
                            if st.button(f"🧾 Ver Recibo {p_id}", key=f"btn_{p_id}"):
                                st.session_state.recibo_id = p_id
                                st.session_state.sub_pagos = "recibo"
                                st.rerun()
                            st.markdown("</div>", unsafe_allow_html=True)
                else: st.info("No hay movimientos financieros registrados.")
                    
                st.write("")
                st.markdown("<div class='btn-secundario'>", unsafe_allow_html=True)
                if st.button("← Volver a Billetera", type="primary"): st.session_state.sub_pagos = "menu"; st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

            elif st.session_state.sub_pagos == "recibo":
                r_id = st.session_state.recibo_id
                if r_id in BASE_DATOS_PAGOS:
                    r_info = BASE_DATOS_PAGOS[r_id]
                    st.markdown(f"""
                    <div class="receipt-card">
                        <div class="receipt-header">
                            <img src="https://i.ibb.co/t7xWXXR/logo.png" width="40">
                            <h4 style="color: #fff; margin: 10px 0 0 0; letter-spacing: 2px;">VENTRY</h4>
                            <p style="color: #888; font-size: 10px; text-transform: uppercase; margin:0;">Recibo de Operación</p>
                        </div>
                        <div style="text-align: center;">
                            <p class="receipt-amount">${float(r_info['monto']):.2f}</p>
                            <span style="background: #4ade80; color: #000; padding: 4px 12px; border-radius: 20px; font-size: 11px; font-weight: bold;">TRANSACCIÓN APROBADA</span>
                        </div>
                        <div style="margin-top: 30px;">
                            <div class="receipt-row"><span class="receipt-label">Recibo ID</span><span class="receipt-value">{r_id}</span></div>
                            <div class="receipt-row"><span class="receipt-label">Fecha</span><span class="receipt-value">{r_info['fecha_reporte']}</span></div>
                            <div class="receipt-row"><span class="receipt-label">Tipo</span><span class="receipt-value">{r_info.get('tipo', 'Abono a Billetera')}</span></div>
                            <div class="receipt-row"><span class="receipt-label">Método</span><span class="receipt-value">{r_info['metodo']}</span></div>
                            <div class="receipt-row"><span class="receipt-label">Referencia</span><span class="receipt-value">{r_info['referencia']}</span></div>
                            <div class="receipt-row"><span class="receipt-label">Acción Titular</span><span class="receipt-value">{r_info['accion']}</span></div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.write("")
                st.markdown("<div class='btn-secundario'>", unsafe_allow_html=True)
                if st.button("← Volver al Historial", type="primary"): st.session_state.sub_pagos = "historial"; st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

    # --- MÓDULO GARITA ---
    elif modulo_seleccionado == "Garita":
        st.markdown("<h3 style='font-size:18px; font-weight:700; color:#fff;'>Control de Acceso (Escáner)</h3>", unsafe_allow_html=True)
        data_usb = st.text_input("🔫 Lector de Código Físico (Pistola USB):", placeholder="Haga clic aquí y dispare el escáner...")
        st.write("📸 O utilizar cámara del dispositivo:")
        foto_qr = st.camera_input("Tomar foto del código QR")

        data_qr = data_usb if data_usb else None
        if foto_qr is not None and not data_qr:
            bytes_data = foto_qr.getvalue()
            cv2_img = cv2.imdecode(np.frombuffer(bytes_data, np.uint8), cv2.IMREAD_COLOR)
            detector = cv2.QRCodeDetector()
            data, bbox, _ = detector.detectAndDecode(cv2_img)
            if data: data_qr = data
            else: st.error("⚠️ No se detectó un código QR claro. Intenta acercar la imagen o mejorar la luz.")

        if data_qr:
            st.write("---")
            if data_qr.startswith("INVITADO|"):
                id_pase = data_qr.split("|")[1]
                if id_pase in BASE_DATOS_INVITACIONES:
                    pase = BASE_DATOS_INVITACIONES[id_pase]
                    fecha_hoy = datetime.now().strftime("%d/%m/%Y")
                    if pase["fecha_visita"] != fecha_hoy:
                        st.error(f"❌ ACCESO DENEGADO\\n\\nEste pase está programado para el **{pase['fecha_visita']}** y hoy es **{fecha_hoy}**.")
                    elif pase["estatus"] == "Activo":
                        st.success(f"✅ ACCESO PERMITIDO\\n\\n**Invitado:** {pase['nombre_invitado']}\\n**Acción:** {pase['accion']}")
                        BASE_DATOS_INVITACIONES[id_pase]["estatus"] = "Adentro"
                        guardar_bd_invitaciones(BASE_DATOS_INVITACIONES)
                        registrar_acceso(pase["nombre_invitado"], pase["accion"], "QR Invitado", "Entrada")
                    elif pase["estatus"] == "Adentro": st.warning("⚠️ ALERTA: El invitado ya registró entrada previamente.")
                    else: st.error(f"❌ ACCESO DENEGADO: Pase {pase['estatus']}")
                else: st.error("❌ Pase no encontrado o falsificado.")
            elif data_qr.startswith("VENTRY_DYN|"):
                try:
                    partes = data_qr.split("|")
                    cedula_qr = partes[1]
                    timestamp_qr = int(partes[2])
                    timestamp_ahora = int(datetime.now().timestamp())
                    if (timestamp_ahora - timestamp_qr) > 60:
                        st.error("❌ ACCESO DENEGADO\\n\\nEl código QR ha **expirado** (Tiene más de 60 segundos). Por favor, actualiza el código en tu aplicación.\\n*(Posible intento de ingreso con captura de pantalla).*")
                    elif cedula_qr in BASE_DATOS_SOCIOS:
                        socio_qr = BASE_DATOS_SOCIOS[cedula_qr]
                        solvencia_qr = socio_qr.get("solvencia", "")
                        if solvencia_qr == "Al dia":
                            st.success(f"✅ ACCESO PERMITIDO\\n\\n**Socio:** {socio_qr['nombre']}\\n**Acción:** {socio_qr['accion']}")
                            registrar_acceso(socio_qr["nombre"], socio_qr["accion"], "QR Dinámico Socio", "Entrada")
                        else: st.error(f"❌ ACCESO DENEGADO\\n\\n**Socio:** {socio_qr['nombre']}\\n**Estatus:** {solvencia_qr.upper()}")
                    else: st.error("❌ Cédula de socio no registrada.")
                except: st.error("❌ Código de carnet ilegible o corrupto.")
            elif "VENTRY" in data_qr:
                st.error("❌ ACCESO DENEGADO\\n\\nEstás intentando usar un carnet estático obsoleto. Por favor, actualiza o refresca tu aplicación Ventry para generar tu nuevo Código Dinámico.")
            else: st.error("❌ Código QR no pertenece al sistema Ventry.")

    # --- MÓDULO 5: ADMIN (DASHBOARD RESPONSIVO) ---
    elif modulo_seleccionado == "Admin":
        st.markdown("<h3 style='font-size:24px; font-weight:800; color:#FF6600;'>Consola Administrativa VIP</h3>", unsafe_allow_html=True)
        
        tab_dashboard, tab_facturacion = st.tabs(["📊 Dashboard & Conciliación", "⚙️ Motor de Facturación"])
        
        with tab_dashboard:
            acciones_al_dia, acciones_morosas, acciones_pendientes = set(), set(), set()
            for socio in BASE_DATOS_SOCIOS.values():
                solvencia_s = socio.get("solvencia", "")
                if solvencia_s == "Moroso": acciones_morosas.add(socio["accion"])
                elif solvencia_s == "Pendiente": acciones_pendientes.add(socio["accion"])
                elif solvencia_s == "En revision": pass 
                else: acciones_al_dia.add(socio["accion"])
            
            for acc in acciones_morosas: acciones_pendientes.discard(acc); acciones_al_dia.discard(acc)
            for acc in acciones_pendientes: acciones_al_dia.discard(acc)
                
            morosos_count = len(acciones_morosas)
            total_acciones = len(acciones_al_dia) + morosos_count + len(acciones_pendientes)
            tasa_morosidad = (morosos_count / total_acciones * 100) if total_acciones > 0 else 0
            capital_riesgo = sum([abs(float(info.get("saldo", 0))) for info in BASE_DATOS_SOCIOS.values() if info["rol"] == "Titular" and float(info.get("saldo", 0)) < 0])

            col_k1, col_k2, col_k3 = st.columns(3)
            with col_k1: st.markdown(f'<div class="kpi-card"><p class="kpi-title">Familias Activas</p><h3 class="kpi-value">{total_acciones}</h3></div>', unsafe_allow_html=True)
            with col_k2: st.markdown(f'<div class="kpi-card" style="border-left-color: {"#ff6b6b" if tasa_morosidad > 15 else "#FF6600"};"><p class="kpi-title">Tasa de Morosidad</p><h3 class="kpi-value">{tasa_morosidad:.1f}%</h3></div>', unsafe_allow_html=True)
            with col_k3: st.markdown(f'<div class="kpi-card" style="border-left-color: #4ade80;"><p class="kpi-title">Capital por Cobrar</p><h3 class="kpi-value">${capital_riesgo:,.2f}</h3></div>', unsafe_allow_html=True)
            st.write("---")
            
            col_admin1, col_admin2 = st.columns([1, 1])
            with col_admin1:
                st.markdown("<h4 style='font-size:16px; color:#aaa;'>💳 Conciliación Pendiente</h4>", unsafe_allow_html=True)
                pagos_pendientes = {k: v for k, v in BASE_DATOS_PAGOS.items() if v["estatus"] == "En Revisión"}
                if pagos_pendientes:
                    for p_id, p_info in pagos_pendientes.items():
                        tipo_trans = p_info.get("tipo", "Abono a Billetera")
                        with st.expander(f"Acción: {p_info['accion']} | ${p_info['monto']} ({p_info['metodo']}) - {tipo_trans}"):
                            st.write(f"**Ref:** {p_info['referencia']} | **Fecha:** {p_info['fecha_reporte']}")
                            btn_col1, btn_col2 = st.columns(2)
                            with btn_col1:
                                if st.button("✅ Aprobar", key=f"apr_{p_id}"):
                                    BASE_DATOS_PAGOS[p_id]["estatus"] = "Aprobado"
                                    guardar_bd_pagos(BASE_DATOS_PAGOS)
                                    
                                    nuevo_saldo = 0.0
                                    for ced, info in BASE_DATOS_SOCIOS.items():
                                        if str(info["accion"]) == str(p_info["accion"]) and info["rol"] == "Titular":
                                            nuevo_saldo = float(info.get("saldo", 0)) + float(p_info['monto'])
                                            BASE_DATOS_SOCIOS[ced]["saldo"] = nuevo_saldo
                                            break
                                            
                                    nueva_solvencia = "Al dia" if nuevo_saldo >= 0 else "Moroso"
                                    for ced_fam, info_fam in BASE_DATOS_SOCIOS.items():
                                        if str(info_fam["accion"]) == str(p_info["accion"]):
                                            BASE_DATOS_SOCIOS[ced_fam]["solvencia"] = nueva_solvencia
                                    
                                    guardar_bd(BASE_DATOS_SOCIOS)
                                    st.rerun()
                            with btn_col2:
                                if st.button("❌ Rechazar", key=f"rec_{p_id}"): BASE_DATOS_PAGOS[p_id]["estatus"] = "Rechazado"; guardar_bd_pagos(BASE_DATOS_PAGOS); st.rerun()
                else: st.success("No hay pagos ni recargas pendientes de revisión.")

                st.write("")
                st.markdown("<h4 style='font-size:16px; color:#aaa;'>📥 Descargar Data (CSV)</h4>", unsafe_allow_html=True)
                if len(BASE_DATOS_SOCIOS) > 0:
                    df_socios = pd.DataFrame(list(BASE_DATOS_SOCIOS.values()))
                    st.download_button("Exportar Matriz de Socios", data=df_socios.to_csv(index=False).encode('utf-8'), file_name="Socios_Ventry.csv", mime="text/csv")
                
            with col_admin2:
                st.markdown("<h4 style='font-size:16px; color:#aaa;'>🔍 Buscador CRM Familiar</h4>", unsafe_allow_html=True)
                busqueda_admin = st.text_input("Buscar por Acción, Cédula o Nombre:")
                acciones_encontradas = set()
                
                if busqueda_admin:
                    for ced, info in BASE_DATOS_SOCIOS.items():
                        if busqueda_admin.lower() in str(info['accion']).lower() or \
                           busqueda_admin.lower() in str(ced).lower() or \
                           busqueda_admin.lower() in str(info['nombre']).lower():
                            acciones_encontradas.add(info['accion'])
                else:
                    acciones_encontradas = set(d["accion"] for d in BASE_DATOS_SOCIOS.values())
                
                if acciones_encontradas:
                    accion_sel = st.selectbox("Familias encontradas (Seleccione Acción):", sorted(list(acciones_encontradas)))
                    miembros_accion = sorted([info for info in BASE_DATOS_SOCIOS.values() if info["accion"] == accion_sel], key=lambda x: x.get("rol", ""), reverse=True)
                    
                    for m in miembros_accion: 
                        icono = '👑' if m['rol'] == 'Titular' else '👤'
                        solvencia_m = m.get('solvencia', 'Desconocido')
                        saldo_m = float(m.get('saldo', 0.0)) if m['rol'] == 'Titular' else "N/A"
                        color_fondo = "#FF6600" if solvencia_m == "En revision" else "#1a1a1a"
                        saldo_txt = f" | Saldo: ${saldo_m:.2f}" if m['rol'] == 'Titular' else ""
                        st.markdown(f"<div style='background:{color_fondo}; color:#ffffff; padding:10px; border-radius:8px; margin-bottom:5px; font-size:13px;'>{icono} <b>{m['nombre']}</b> - {solvencia_m}{saldo_txt}</div>", unsafe_allow_html=True)
                    
                    with st.form("form_estatus_rapido"):
                        n_estatus = st.selectbox("Actualizar Estatus de Grupo:", ["Al dia", "Moroso", "Pendiente", "En revision"])
                        if st.form_submit_button("Actualizar Todo"):
                            for ced, info in BASE_DATOS_SOCIOS.items():
                                if info["accion"] == accion_sel: BASE_DATOS_SOCIOS[ced]["solvencia"] = n_estatus
                            guardar_bd(BASE_DATOS_SOCIOS); st.success("Actualizado.")
                else:
                    st.warning("No se encontraron familias con esa búsqueda.")

            st.write("---")
            st.markdown("<h4 style='font-size:18px; color:#fff;'>📟 Monitor de Acceso en Tiempo Real</h4>", unsafe_allow_html=True)
            if st.session_state.db_historial:
                for h in st.session_state.db_historial[:15]:
                    clase_monitor = "monitor-card-invitado" if "Invitado" in h['via'] else ""
                    icono_persona = "🎟️" if "Invitado" in h['via'] else "👤"
                    st.markdown(f"""
                    <div class="monitor-card {clase_monitor}">
                        <div>
                            <span style="color:#aaa; font-size:11px;">{h['fecha']}</span><br>
                            <b style="color:#fff; font-size:14px;">{icono_persona} {h['nombre']}</b>
                        </div>
                        <div style="text-align: right;">
                            <span style="color:#FF6600; font-size:12px; font-weight:bold;">Acción {h['accion']}</span><br>
                            <span style="color:#666; font-size:11px; text-transform:uppercase;">{h['via']}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else: st.info("No hay registros de acceso en la base de datos.")

        with tab_facturacion:
            st.markdown("<h4 style='color:#FF6600;'>Auditoría y Cobro de Morosos (Post-Día 10)</h4>", unsafe_allow_html=True)
            st.write("Este botón debe ser accionado por el Administrador **después del día 10** de cada mes. Cobrará la cuota de **$120** (Sin premio de pases gratis) a todas las familias que no hayan pagado su cuota.")
            
            if st.button("🚨 EJECUTAR COBRO DE MOROSOS", type="primary"):
                fecha_cobro = datetime.now().strftime("%d/%m/%Y")
                mes_actual = mes_actual_str()
                familias_cobradas = 0
                
                for ced, info in BASE_DATOS_SOCIOS.items():
                    if info["rol"] == "Titular":
                        # Solo cobra a los que NO están solventes este mes
                        if info.get("mes_pagado", "") != mes_actual:
                            monto_tardio = 120.0
                            nuevo_saldo = float(info.get("saldo", 0)) - monto_tardio
                            BASE_DATOS_SOCIOS[ced]["saldo"] = nuevo_saldo
                            BASE_DATOS_SOCIOS[ced]["mes_pagado"] = mes_actual
                            BASE_DATOS_SOCIOS[ced]["invitaciones"] = 0 # Castigo por pagar tarde
                            familias_cobradas += 1
                            
                            id_cargo = f"CRG-{str(uuid.uuid4())[:6].upper()}"
                            BASE_DATOS_PAGOS[id_cargo] = {
                                "accion": info["accion"], "metodo": "Sistema Ventry", "referencia": "MORA", 
                                "monto": monto_tardio, "fecha_reporte": fecha_cobro, "estatus": "Aprobado", "tipo": "Cargo Mensual (Tardío)"
                            }
                            
                            nueva_solvencia = "Al dia" if nuevo_saldo >= 0 else "Moroso"
                            for ced_fam, info_fam in BASE_DATOS_SOCIOS.items():
                                if str(info_fam["accion"]) == str(info["accion"]):
                                    BASE_DATOS_SOCIOS[ced_fam]["solvencia"] = nueva_solvencia
                                    
                guardar_bd(BASE_DATOS_SOCIOS)
                guardar_bd_pagos(BASE_DATOS_PAGOS)
                st.success(f"✅ ¡FACTURACIÓN DE MOROSOS EXITOSA! Se han cargado $120 a {familias_cobradas} acciones rezagadas.")
                st.rerun()

        st.write("---")
        if st.button("🔄 Sincronizar DB en la Nube (Google Sheets)"):
            st.session_state.db_socios = cargar_bd(); st.session_state.db_invitaciones = cargar_invitaciones(); st.session_state.db_pagos = cargar_pagos(); st.session_state.db_directorio = cargar_directorio(); st.session_state.db_historial = cargar_historial()
            st.success("Base de datos sincronizada.")

    # --- MÓDULO 6: AJUSTES ---
    elif modulo_seleccionado == "Ajustes":
        
        if "sub_ajustes" not in st.session_state: st.session_state.sub_ajustes = "menu"

        if st.session_state.sub_ajustes == "menu":
            st.markdown("<h3 style='font-size:22px; font-weight:800; color:#fff; margin-bottom: 20px;'>Ajustes</h3>", unsafe_allow_html=True)
            
            if st.button("Perfil y Seguridad", type="primary"): st.session_state.sub_ajustes = "perfil"; st.rerun()
            st.write("")
            if st.button("Mis Contactos (Directorio)", type="primary"): st.session_state.sub_ajustes = "directorio"; st.rerun()
            st.write("")
            if st.button("Grupo Familiar", type="primary"): st.session_state.sub_ajustes = "familia"; st.rerun()
            st.write("")
            if st.button("Historial de Accesos", type="primary"): st.session_state.sub_ajustes = "historial"; st.rerun()

        elif st.session_state.sub_ajustes == "perfil":
            st.markdown("<h3 style='font-size:20px; font-weight:800; color:#FF6600;'>Perfil y Seguridad</h3>", unsafe_allow_html=True)
            with st.form("form_cambio_clave"):
                clave_actual = st.text_input("Contraseña Actual", type="password")
                clave_nueva = st.text_input("Nueva Contraseña", type="password")
                clave_confirma = st.text_input("Confirmar Nueva Contraseña", type="password")
                st.markdown("<br>", unsafe_allow_html=True)
                btn_cambiar_clave = st.form_submit_button("ACTUALIZAR CONTRASEÑA")
                
            if btn_cambiar_clave:
                if clave_actual != str(socio_actual["clave"]): st.error("❌ La contraseña actual es incorrecta.")
                elif clave_nueva != clave_confirma: st.error("❌ Las contraseñas nuevas no coinciden.")
                elif len(clave_nueva) < 4: st.error("⚠️ La contraseña debe tener al menos 4 caracteres.")
                else:
                    BASE_DATOS_SOCIOS[socio_actual["cedula"]]["clave"] = clave_nueva
                    guardar_bd(BASE_DATOS_SOCIOS)
                    st.session_state.usuario_actual["clave"] = clave_nueva
                    st.success("✅ Contraseña actualizada exitosamente.")
            
            st.write("")
            st.markdown("<div class='btn-secundario'>", unsafe_allow_html=True)
            if st.button("← Volver a Ajustes", type="primary"): st.session_state.sub_ajustes = "menu"; st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
            
            st.write("---")
            st.markdown("<div class='btn-logout'>", unsafe_allow_html=True)
            if st.button("Cerrar Sesión de Ventry"):
                st.session_state.logueado = False
                st.session_state.usuario_actual = None
                st.session_state.pantalla_auth = "login"
                st.session_state.sub_ajustes = "menu"
                st.session_state.sub_pagos = "menu"
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        elif st.session_state.sub_ajustes == "directorio":
            st.markdown("<h3 style='font-size:20px; font-weight:800; color:#FF6600;'>Mis Contactos</h3>", unsafe_allow_html=True)
            mis_contactos = BASE_DATOS_DIRECTORIO.get(socio_actual["accion"], {})
            
            if mis_contactos:
                for ced_contacto, info_contacto in mis_contactos.items():
                    st.markdown(f"""
                    <div class="historial-card">
                        <b style="font-size: 16px; color:#fff;">{info_contacto['nombre']}</b><br>
                        <span style="color:#aaa; font-size:12px;">C.I: {ced_contacto} | Correo: {info_contacto.get('correo', 'N/A')}</span>
                    </div>
                    """, unsafe_allow_html=True)
                    st.markdown("<div class='btn-peligro' style='margin-bottom:15px;'>", unsafe_allow_html=True)
                    if st.button(f"Eliminar {info_contacto['nombre']}", key=f"del_{ced_contacto}"):
                        del BASE_DATOS_DIRECTORIO[socio_actual["accion"]][ced_contacto]
                        guardar_bd_directorio(BASE_DATOS_DIRECTORIO)
                        st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.info("No tienes invitados guardados en tu directorio frecuente.")
                
            st.write("")
            st.markdown("<div class='btn-secundario'>", unsafe_allow_html=True)
            if st.button("← Volver a Ajustes", type="primary"): st.session_state.sub_ajustes = "menu"; st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        elif st.session_state.sub_ajustes == "familia":
            st.markdown(f"<h3 style='font-size:20px; font-weight:800; color:#FF6600;'>Acción {socio_actual['accion']}</h3>", unsafe_allow_html=True)
            if rol_actual == "Titular":
                miembros = [m for m in BASE_DATOS_SOCIOS.values() if m["accion"] == socio_actual["accion"] and m["cedula"] != socio_actual["cedula"]]
                if miembros:
                    for m in miembros:
                        st.markdown(f"""
                        <div class="historial-card">
                            <b style="font-size: 16px; color:#fff;">{m['nombre']}</b><br>
                            <span style="color:#aaa; font-size:12px;">C.I: {m['cedula']} | Parentesco: {m['parentesco']}</span><br>
                            <span style="color:#FF6600; font-size:12px; font-weight:bold;">Estatus: {m.get('solvencia', 'Desconocido')}</span>
                        </div>
                        """, unsafe_allow_html=True)
                else: st.info("No hay familiares registrados bajo tu acción en este momento.")
            else: st.warning("🔒 Esta sección es exclusiva para la cuenta Titular de la Acción.")
                
            st.write("")
            st.markdown("<div class='btn-secundario'>", unsafe_allow_html=True)
            if st.button("← Volver a Ajustes", type="primary"): st.session_state.sub_ajustes = "menu"; st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        elif st.session_state.sub_ajustes == "historial":
            st.markdown("<h3 style='font-size:20px; font-weight:800; color:#FF6600;'>Actividad Reciente</h3>", unsafe_allow_html=True)
            historial_accion = [h for h in st.session_state.db_historial if h["accion"] == str(socio_actual["accion"])]
            if historial_accion:
                for h in historial_accion[:10]:
                    st.markdown(f"""
                    <div style='background:#1a1a1a; padding:12px; border-radius:8px; margin-bottom:8px; border-left: 2px solid #FF6600;'>
                        <span style='color:#FF6600; font-weight:bold; font-size:11px;'>{h['fecha']}</span><br>
                        <b style='font-size:14px; color:#fff;'>{h['nombre']}</b><br>
                        <span style='color:#aaa; font-size:12px;'>Método: {h['via']} - Tipo: {h['movimiento']}</span>
                    </div>
                    """, unsafe_allow_html=True)
            else: st.info("No hay registros de acceso recientes para tu acción.")
                
            st.write("")
            st.markdown("<div class='btn-secundario'>", unsafe_allow_html=True)
            if st.button("← Volver a Ajustes", type="primary"): st.session_state.sub_ajustes = "menu"; st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)