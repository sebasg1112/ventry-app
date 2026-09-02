import streamlit as st
from datetime import datetime
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

# --- CSS AVANZADO: DISEÑO PREMIUM Y CORRECCIONES ABSOLUTAS ---
st.markdown("""
    <style>
    /* Ocultamos rastros de Streamlit web */
    #MainMenu {display: none;}
    footer {display: none;}
    [data-testid="collapsedControl"] {display: none;} 
    section[data-testid="stSidebar"] {display: none !important;} 
    
    /* 1. FONDO GLOBAL VENTRY (GRIS OSCURO/NEGRO) */
    .stApp { 
        background-color: #0d0d0d; 
        color: #f5f5f5;
    }
    
    /* 2. TIPOGRAFÍA GLOBAL MINIMALISTA */
    h1, h2, h3, h4, h5, h6, p, span, label, div { color: #f5f5f5 !important; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; }
    
    /* 3. CORRECCIÓN DEFINITIVA DE FORMULARIOS Y CAJAS DE TEXTO */
    .stTextInput input, .stNumberInput input, .stDateInput input, .stSelectbox select, textarea {
        background-color: #1a1a1a !important;
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
    }
    div[data-baseweb="input"] > div, 
    div[data-baseweb="select"] > div, 
    div[data-baseweb="base-input"] {
        background-color: #1a1a1a !important;
        border-radius: 10px !important;
        border: 1px solid #333 !important;
    }
    div[data-baseweb="input"]:focus-within, div[data-baseweb="select"]:focus-within {
        border-color: #FF6600 !important;
        box-shadow: 0 0 8px rgba(255, 102, 0, 0.4) !important;
    }

    /* 4. BOTÓN PRINCIPAL NARANJA ELÉCTRICO VENTRY */
    .stButton>button, .stFormSubmitButton>button { 
        width: 100%; 
        border-radius: 20px !important; 
        background: #FF6600 !important; 
        color: #ffffff !important; 
        font-weight: 700 !important; 
        letter-spacing: 0.5px;
        border: none !important; 
        padding: 12px !important;
        box-shadow: 0 4px 15px rgba(255, 102, 0, 0.3) !important;
        transition: all 0.2s ease-in-out;
    }
    .stButton>button:active, .stFormSubmitButton>button:active {
        background: #e65c00 !important;
        transform: scale(0.98);
    }
    
    /* 5. BOTÓN SECUNDARIO (VOLVER / CANCELAR) */
    .btn-secundario>button {
        background: transparent !important;
        border: 1px solid #555 !important;
        color: #aaa !important;
        box-shadow: none !important;
    }
    
    /* 6. BOTTOM NAVIGATION BAR (MENÚ INFERIOR ELEGANTE SIN EMOJIS) */
    .block-container {
        padding-bottom: 120px !important; 
    }
    div.stRadio {
        position: fixed !important;
        bottom: 0 !important;
        left: 0 !important;
        width: 100% !important;
        background-color: rgba(13, 13, 13, 0.95) !important;
        backdrop-filter: blur(20px) !important;
        border-top: 1px solid rgba(255, 255, 255, 0.05) !important;
        padding: 15px 0px 25px 0px !important;
        z-index: 99999 !important;
    }
    div.stRadio > div[role="radiogroup"] {
        display: flex !important;
        flex-direction: row !important;
        justify-content: space-evenly !important;
        align-items: center !important;
        gap: 0 !important;
    }
    div.stRadio > div[role="radiogroup"] > label {
        background: transparent !important;
        border: none !important;
        padding: 5px 10px !important;
        margin: 0 !important;
        cursor: pointer;
    }
    div.stRadio > div[role="radiogroup"] > label span[data-baseweb="radio"] {
        display: none !important;
    }
    div.stRadio > div[role="radiogroup"] > label div {
        color: #777777 !important;
        font-size: 13px !important;
        font-weight: 500 !important;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    div.stRadio > div[role="radiogroup"] > label[data-checked="true"] div {
        color: #FF6600 !important;
        font-weight: 800 !important;
    }

    /* 7. BOTÓN GIGANTE DE ABRIR PUERTA */
    .open-button-container { display: flex; justify-content: center; margin-top: 40px; margin-bottom: 20px;}
    .open-button-glow {
        border-radius: 50%;
        padding: 8px;
        background: radial-gradient(circle, rgba(255,102,0,0.4) 0%, rgba(0,0,0,0) 70%);
        box-shadow: 0 0 60px rgba(255,102,0,0.3);
    }
    .open-button {
        background: linear-gradient(145deg, #222222, #0a0a0a);
        border: 2px solid #FF6600;
        border-radius: 50%;
        width: 200px;
        height: 200px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        color: white;
        cursor: pointer;
        box-shadow: inset 0 0 25px rgba(0,0,0,0.9);
        transition: transform 0.1s ease;
    }
    .open-button:active {
        background: #FF6600;
        transform: scale(0.96);
    }
    
    /* 8. CARNET MAGNUM CLUB (WHITE LABEL) */
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
    
    /* 9. TARJETAS KPI ADMIN */
    .kpi-card {
        background: #1a1a1a;
        padding: 20px;
        border-radius: 15px;
        border-left: 4px solid #FF6600;
        box-shadow: 0 4px 10px rgba(0,0,0,0.5);
        margin-bottom: 15px;
    }
    .kpi-title { color: #888; font-size: 12px; font-weight: bold; letter-spacing: 1px; text-transform: uppercase; margin-bottom: 5px; }
    .kpi-value { color: #fff; font-size: 28px; font-weight: 800; margin: 0; }
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
    if not fecha_nac_str: return "N/A"
    try:
        fecha_nac = datetime.strptime(fecha_nac_str, "%d/%m/%Y").date()
        hoy = datetime.today().date()
        return str(hoy.year - fecha_nac.year - ((hoy.month, hoy.day) < (fecha_nac.month, fecha_nac.day)))
    except:
        return "N/A"

def registrar_acceso(nombre, accion, via, movimiento):
    hora_actual = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    hoja_historial.append_row([hora_actual, str(accion), nombre, via, movimiento])
    st.session_state.historial.insert(0, {"nombre": nombre, "accion": accion, "hora": hora_actual, "via": via, "movimiento": movimiento})

def cargar_bd():
    registros = hoja_bd.get_all_records()
    datos = {}
    for fila in registros:
        ced = str(fila.get("cedula", ""))
        if ced: datos[ced] = {"nombre": str(fila.get("nombre", "")), "clave": str(fila.get("clave", "")), "accion": str(fila.get("accion", "")), "rol": str(fila.get("rol", "")), "parentesco": str(fila.get("parentesco", "N/A")), "fecha_nacimiento": str(fila.get("fecha_nacimiento", "")), "solvency": str(fila.get("solvencia", "")), "cedula": ced}
    return datos

def guardar_bd(datos):
    lista_socios = list(datos.values())
    lista_socios.sort(key=lambda x: (x.get("accion", ""), x.get("rol", "")), reverse=True) 
    filas_a_subir = [["cedula", "nombre", "clave", "accion", "rol", "parentesco", "fecha_nacimiento", "solvencia"]]
    for socio in lista_socios: filas_a_subir.append([socio["cedula"], socio["nombre"], socio["clave"], socio["accion"], socio["rol"], socio["parentesco"], socio.get("fecha_nacimiento", ""), socio.get("solvencia", socio.get("solvency"))])
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
            if id_p: datos[id_p] = {"accion": str(f.get("accion", "")), "metodo": str(f.get("metodo", "")), "referencia": str(f.get("referencia", "")), "monto": str(f.get("monto", "")), "fecha_reporte": str(f.get("fecha_reporte", "")), "estatus": str(f.get("estatus", ""))}
        return datos
    except: return {}

def guardar_bd_pagos(datos):
    filas = [["id_pago", "accion", "metodo", "referencia", "monto", "fecha_reporte", "estatus"]]
    for k, v in datos.items(): filas.append([k, v["accion"], v["metodo"], v["referencia"], v["monto"], v["fecha_reporte"], v["estatus"]])
    hoja_pagos.clear()
    hoja_pagos.update(values=filas, range_name="A1")
    st.session_state.db_pagos = datos

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

# --- MEMORIA LOCAL ---
if "datos_cargados" not in st.session_state:
    st.session_state.db_socios = cargar_bd()
    st.session_state.db_invitaciones = cargar_invitaciones()
    st.session_state.db_pagos = cargar_pagos()
    st.session_state.db_directorio = cargar_directorio()
    st.session_state.datos_cargados = True

BASE_DATOS_SOCIOS = st.session_state.db_socios
BASE_DATOS_INVITACIONES = st.session_state.db_invitaciones
BASE_DATOS_PAGOS = st.session_state.db_pagos
BASE_DATOS_DIRECTORIO = st.session_state.db_directorio

if "logueado" not in st.session_state: st.session_state.logueado = False
if "usuario_actual" not in st.session_state: st.session_state.usuario_actual = None
if "historial" not in st.session_state: st.session_state.historial = []
if "ubicacion_socios" not in st.session_state: st.session_state.ubicacion_socios = {} 


# ==========================================
# 🛑 INTERCEPTOR DE PASES DIGITALES (VISTA INVITADO)
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
# PANTALLA INICIAL: LOGIN PREMIUM
# ==========================================
if not st.session_state.logueado:
    st.markdown("""
        <div style='text-align: center; margin-top: 40px; margin-bottom: 30px;'>
            <img src="https://i.ibb.co/t7xWXXR/logo.png" width="90" style="margin-bottom: 15px;">
            <h1 style='font-weight: 800; font-size: 34px; margin-bottom: 0px; letter-spacing: 1px;'>VENTRY</h1>
            <p style='color: #666; font-size: 12px; letter-spacing: 3px; text-transform: uppercase;'>Access Control</p>
        </div>
    """, unsafe_allow_html=True)
    
    with st.form("login_form"):
        cedula_ingresada = st.text_input("Email o ID (Cédula)")
        clave_ingresada = st.text_input("Contraseña", type="password")
        
        st.markdown("<br>", unsafe_allow_html=True)
        boton_entrar = st.form_submit_button("INICIAR SESIÓN")
        
        st.markdown("""
            <div style="text-align: center; margin-top: 20px;">
                <span style="border: 1px solid #333; padding: 8px 15px; border-radius: 20px; color: #aaa; font-size: 12px; cursor: pointer; transition: all 0.3s;" onclick="alert('FaceID/TouchID se activará en la Fase 3 de compilación nativa.')">
                    🔒 Ingresar con Biometría
                </span>
            </div>
            <p style='text-align:center; color:#FF6600; font-size:12px; margin-top:25px; cursor:pointer;'>¿Olvidaste tu contraseña?</p>
        """, unsafe_allow_html=True)

    if boton_entrar:
        if cedula_ingresada in BASE_DATOS_SOCIOS:
            socio = BASE_DATOS_SOCIOS[cedula_ingresada]
            if clave_ingresada == str(socio["clave"]):
                st.session_state.logueado = True; st.session_state.usuario_actual = socio; st.rerun()
            else: st.error("❌ Contraseña incorrecta.")
        else: st.error("⚠️ Usuario no registrado.")

# ==========================================
# APP NATIVA INTERNA
# ==========================================
else:
    socio_actual = st.session_state.usuario_actual
    rol_actual = socio_actual["rol"]

    # Header Superior Elegante
    st.markdown(f"""
    <div style="display:flex; align-items:center; gap:10px; margin-bottom: 20px;">
        <img src="https://i.ibb.co/t7xWXXR/logo.png" width="25">
        <span style="font-size:16px; font-weight:700; letter-spacing: 1px;">VENTRY</span>
    </div>
    """, unsafe_allow_html=True)

    # --- BOTTOM NAVIGATION BAR DEFINITION ---
    # ¡AQUÍ ESTÁ LA CORRECCIÓN! Todos los roles ahora tienen "Ajustes"
    if rol_actual in ["Titular", "Familiar"]: 
        opciones_menu = ["Inicio", "Invitados", "Carnet", "Pagos", "Ajustes"]
    elif rol_actual == "Vigilante": 
        opciones_menu = ["Garita", "Ajustes"]
    elif rol_actual == "Administrador": 
        opciones_menu = ["Inicio", "Invitados", "Garita", "Admin", "Ajustes"]

    modulo_seleccionado = st.radio("Nav", opciones_menu, horizontal=True, label_visibility="collapsed")

    # ==========================================
    # LOGICA DE EXPANSIÓN RESPONSIVA (HACK PARA ADMIN)
    # ==========================================
    if modulo_seleccionado == "Admin":
        st.markdown("<style>.block-container { max-width: 95% !important; padding-top: 2rem !important; }</style>", unsafe_allow_html=True)
    else:
        st.markdown("<style>.block-container { max-width: 46rem !important; }</style>", unsafe_allow_html=True)


    # --- MÓDULO 1: INICIO ---
    if modulo_seleccionado == "Inicio":
        st.markdown("""
<div style="text-align: center; margin-top: 20px;">
<h2 style="margin-bottom: 5px; font-size:22px; font-weight:800;">Magnum City Club</h2>
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
        if st.button("Simular Apertura (Demo ESP32)"):
            st.success("📡 Señal enviada a garita.")


    # --- MÓDULO 2: CARNET DIGITAL ---
    elif modulo_seleccionado == "Carnet":
        solvencia = socio_actual.get('solvencia', socio_actual.get('solvency', 'Desconocido'))
        if solvencia == "Moroso": st.error("⚠️ Tu grupo familiar presenta un saldo pendiente.")
        
        if solvencia == "Al dia": clase_badge = "badge-aldia"; texto_badge = "AL DÍA"
        elif solvencia == "Pendiente": clase_badge = "badge-pendiente"; texto_badge = "PENDIENTE"
        else: clase_badge = "badge-moroso"; texto_badge = "MOROSO"

        datos_qr = f"CEDULA:{socio_actual['cedula']}|VENTRY|{socio_actual['nombre']}|{socio_actual['accion']}"
        img = qrcode.make(datos_qr)
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        img_str = base64.b64encode(buffer.getvalue()).decode()

        carnet_html = f"""
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
"""
        st.markdown(carnet_html, unsafe_allow_html=True)

    # --- MÓDULO 3: INVITADOS ---
    elif modulo_seleccionado == "Invitados":
        
        if "ultimo_pase_generado" not in st.session_state: 
            st.session_state.ultimo_pase_generado = None

        if st.session_state.ultimo_pase_generado:
            pase_temp = st.session_state.ultimo_pase_generado
            url_base = "https://ventry.streamlit.app" 
            link_pase_digital = f"{url_base}/?pase={pase_temp['id']}"
            
            st.success(f"✅ Pase de {pase_temp['nombre']} emitido correctamente.")
            
            mensaje_ws = f"¡Hola {pase_temp['nombre']}! Aquí tienes tu pase para el *Magnum City Club*.\nFecha: {pase_temp['fecha']}\n👉 Abre tu código QR aquí:\n{link_pase_digital}"
            link_ws = f"https://wa.me/?text={urllib.parse.quote(mensaje_ws)}"
            
            st.markdown(f'<a href="{link_ws}" target="_blank" style="display:block; text-align:center; background:#25D366; color:white; padding:15px; border-radius:20px; text-decoration:none; font-weight:800; letter-spacing:1px; margin-top:20px; margin-bottom:20px; box-shadow: 0 5px 15px rgba(37, 211, 102, 0.3);">ENVIAR POR WHATSAPP</a>', unsafe_allow_html=True)
            
            st.markdown("<div class='btn-secundario'>", unsafe_allow_html=True)
            if st.button("← Volver a crear otra invitación"):
                st.session_state.ultimo_pase_generado = None
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
                
        else:
            st.markdown("<h3 style='font-size:18px; font-weight:700;'>Pases y Accesos</h3>", unsafe_allow_html=True)
            
            solvencia = socio_actual.get('solvencia', socio_actual.get('solvency', 'Desconocido'))
            if solvencia != "Al dia":
                st.error("❌ Operación Denegada. Debes estar al día con la administración para invitar.")
            else:
                invitados_previos = BASE_DATOS_DIRECTORIO.get(socio_actual["accion"], {})
                
                modo_ingreso = st.selectbox("Método de registro:", ["📝 Ingresar Nuevo Invitado", "⭐ Seleccionar de Favoritos"])
                
                n_cedula_def, n_nombre_def, n_correo_def = "", "", ""
                n_nacimiento_def = datetime.today()
                
                if modo_ingreso == "⭐ Seleccionar de Favoritos":
                    if invitados_previos:
                        inv_sel = st.selectbox("Tu directorio:", list(invitados_previos.keys()), format_func=lambda x: f"{invitados_previos[x]['nombre']} (C.I: {x})")
                        n_cedula_def = inv_sel
                        n_nombre_def = invitados_previos[inv_sel]['nombre']
                        n_correo_def = invitados_previos[inv_sel]['correo']
                    else: 
                        st.info("Aún no tienes invitados en tu directorio frecuente.")

                with st.form("form_invitacion"):
                    n_cedula_inv = st.text_input("Cédula", value=n_cedula_def)
                    n_nombre_inv = st.text_input("Nombre y Apellido", value=n_nombre_def)
                    fecha_visita = st.date_input("Fecha de acceso", min_value=datetime.today(), format="DD/MM/YYYY")
                    
                    guardar_contacto = False
                    if modo_ingreso == "📝 Ingresar Nuevo Invitado":
                        st.write("")
                        guardar_contacto = st.checkbox("Guardar en mi directorio frecuente", value=True)
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    btn_generar = st.form_submit_button("GENERAR PASE DIGITAL")
                    
                if btn_generar and n_cedula_inv and n_nombre_inv:
                    if guardar_contacto:
                        if socio_actual["accion"] not in BASE_DATOS_DIRECTORIO: BASE_DATOS_DIRECTORIO[socio_actual["accion"]] = {}
                        BASE_DATOS_DIRECTORIO[socio_actual["accion"]][n_cedula_inv] = {"nombre": n_nombre_inv, "correo": n_correo_def, "fecha_nacimiento": n_nacimiento_def.strftime("%d/%m/%Y")}
                        guardar_bd_directorio(BASE_DATOS_DIRECTORIO)
                        
                    str_fecha = fecha_visita.strftime("%d/%m/%Y")
                    id_unico = f"INV-{socio_actual['accion']}-{str(uuid.uuid4())[:6].upper()}"
                    BASE_DATOS_INVITACIONES[id_unico] = {
                        "accion": socio_actual["accion"], "fecha_visita": str_fecha, 
                        "cedula_invitado": n_cedula_inv, "nombre_invitado": n_nombre_inv, 
                        "fecha_nacimiento": "", "correo": "", "estatus": "Activo"
                    }
                    guardar_bd_invitaciones(BASE_DATOS_INVITACIONES)
                    
                    st.session_state.ultimo_pase_generado = {"id": id_unico, "nombre": n_nombre_inv, "fecha": str_fecha}
                    st.rerun()

    # --- MÓDULO 4: PAGOS ---
    elif modulo_seleccionado == "Pagos":
        st.markdown("<h3 style='font-size:18px; font-weight:700;'>Gestión de Pagos</h3>", unsafe_allow_html=True)
        solvencia = socio_actual.get('solvencia', socio_actual.get('solvency', 'Desconocido'))
        deuda = 104.00 if solvencia == "Moroso" else 0.00
        
        st.markdown(f"""
        <div style="background: rgba(255,255,255,0.05); padding: 20px; border-radius: 15px; border: 1px solid #333; margin-bottom: 20px;">
            <p style="margin:0; color:#aaa; font-size:12px; text-transform:uppercase; letter-spacing:1px;">Saldo Pendiente Estimado</p>
            <h2 style="margin:0; color:{'#FF6600' if deuda > 0 else '#4ade80'}; font-size:28px;">${deuda:.2f}</h2>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("form_pago"):
            metodo = st.selectbox("Vía de pago", ["Zelle", "Pago Móvil", "Transferencia"])
            n_referencia = st.text_input("Nº de Referencia (Últimos 6 dígitos)")
            n_monto = st.number_input("Monto reportado", min_value=1.0)
            st.markdown("<br>", unsafe_allow_html=True)
            btn_reportar = st.form_submit_button("REPORTAR PAGO")
            
        if btn_reportar and n_referencia:
            st.success("✅ Recibo enviado a administración.")

    # --- MÓDULO GARITA ---
    elif modulo_seleccionado == "Garita":
        st.markdown("<h3 style='font-size:18px; font-weight:700;'>Escáner de Seguridad</h3>", unsafe_allow_html=True)
        foto_qr = st.camera_input("")

    # --- MÓDULO 5: ADMIN (DASHBOARD RESPONSIVO) ---
    elif modulo_seleccionado == "Admin":
        st.markdown("<h3 style='font-size:24px; font-weight:800; color:#FF6600;'>Consola Administrativa VIP</h3>", unsafe_allow_html=True)
        
        acciones_al_dia, acciones_morosas, acciones_pendientes = set(), set(), set()
        for socio in BASE_DATOS_SOCIOS.values():
            solvencia_s = socio.get("solvencia", socio.get("solvency", ""))
            if solvencia_s == "Moroso": acciones_morosas.add(socio["accion"])
            elif solvencia_s == "Pendiente": acciones_pendientes.add(socio["accion"])
            else: acciones_al_dia.add(socio["accion"])
        
        for acc in acciones_morosas: acciones_pendientes.discard(acc); acciones_al_dia.discard(acc)
        for acc in acciones_pendientes: acciones_al_dia.discard(acc)
            
        morosos_count = len(acciones_morosas)
        total_acciones = len(acciones_al_dia) + morosos_count + len(acciones_pendientes)
        tasa_morosidad = (morosos_count / total_acciones * 100) if total_acciones > 0 else 0
        capital_riesgo = morosos_count * 104

        col_k1, col_k2, col_k3 = st.columns(3)
        
        with col_k1:
            st.markdown(f"""
            <div class="kpi-card">
                <p class="kpi-title">Familias Registradas</p>
                <h3 class="kpi-value">{total_acciones}</h3>
            </div>
            """, unsafe_allow_html=True)
            
        with col_k2:
            st.markdown(f"""
            <div class="kpi-card" style="border-left-color: {'#ff6b6b' if tasa_morosidad > 15 else '#FF6600'};">
                <p class="kpi-title">Tasa de Morosidad</p>
                <h3 class="kpi-value">{tasa_morosidad:.1f}%</h3>
            </div>
            """, unsafe_allow_html=True)
            
        with col_k3:
            st.markdown(f"""
            <div class="kpi-card" style="border-left-color: #4ade80;">
                <p class="kpi-title">Capital por Cobrar</p>
                <h3 class="kpi-value">${capital_riesgo:,.2f}</h3>
            </div>
            """, unsafe_allow_html=True)

        st.write("---")
        
        col_admin1, col_admin2 = st.columns([1, 1])
        
        with col_admin1:
            st.markdown("<h4 style='font-size:16px; color:#aaa;'>💳 Conciliación Pendiente</h4>", unsafe_allow_html=True)
            pagos_pendientes = {k: v for k, v in BASE_DATOS_PAGOS.items() if v["estatus"] == "En Revisión"}
            if pagos_pendientes:
                for p_id, p_info in pagos_pendientes.items():
                    with st.expander(f"Acción: {p_info['accion']} | ${p_info['monto']} ({p_info['metodo']})"):
                        st.write(f"**Ref:** {p_info['referencia']} | **Fecha:** {p_info['fecha_reporte']}")
                        btn_col1, btn_col2 = st.columns(2)
                        with btn_col1:
                            if st.button("✅ Aprobar", key=f"apr_{p_id}"):
                                BASE_DATOS_PAGOS[p_id]["estatus"] = "Aprobado"; guardar_bd_pagos(BASE_DATOS_PAGOS)
                                for ced, info in BASE_DATOS_SOCIOS.items():
                                    if str(info["accion"]) == str(p_info["accion"]): BASE_DATOS_SOCIOS[ced]["solvencia"] = "Al dia"
                                guardar_bd(BASE_DATOS_SOCIOS); st.rerun()
                        with btn_col2:
                            if st.button("❌ Rechazar", key=f"rec_{p_id}"): BASE_DATOS_PAGOS[p_id]["estatus"] = "Rechazado"; guardar_bd_pagos(BASE_DATOS_PAGOS); st.rerun()
            else: 
                st.success("No hay pagos pendientes.")

            st.write("")
            st.markdown("<h4 style='font-size:16px; color:#aaa;'>📥 Descargar Data (CSV)</h4>", unsafe_allow_html=True)
            if total_acciones > 0:
                df_socios = pd.DataFrame(list(BASE_DATOS_SOCIOS.values()))
                st.download_button("Exportar Matriz de Socios", data=df_socios.to_csv(index=False).encode('utf-8'), file_name="Socios_Ventry.csv", mime="text/csv")
            
        with col_admin2:
            st.markdown("<h4 style='font-size:16px; color:#aaa;'>📝 Gestión Rápida Familiar</h4>", unsafe_allow_html=True)
            acciones_disponibles = sorted(list(set(d["accion"] for d in BASE_DATOS_SOCIOS.values())))
            if acciones_disponibles:
                accion_sel = st.selectbox("Seleccione Acción:", acciones_disponibles)
                miembros_accion = sorted([info for info in BASE_DATOS_SOCIOS.values() if info["accion"] == accion_sel], key=lambda x: x.get("rol", ""), reverse=True)
                
                for m in miembros_accion: 
                    icono = '👑' if m['rol'] == 'Titular' else '👤'
                    solvencia_m = m.get('solvencia', m.get('solvency', 'Desconocido'))
                    st.markdown(f"<div style='background:#1a1a1a; padding:10px; border-radius:8px; margin-bottom:5px; font-size:13px;'>{icono} <b>{m['nombre']}</b> - {solvencia_m}</div>", unsafe_allow_html=True)
                
                with st.form("form_estatus_rapido"):
                    n_estatus = st.radio("Actualizar Estatus de Grupo:", ["Al dia", "Moroso", "Pendiente"], horizontal=True)
                    if st.form_submit_button("Actualizar Todo"):
                        for ced, info in BASE_DATOS_SOCIOS.items():
                            if info["accion"] == accion_sel: BASE_DATOS_SOCIOS[ced]["solvencia"] = n_estatus
                        guardar_bd(BASE_DATOS_SOCIOS); st.success("Actualizado.")

        st.write("---")
        if st.button("🔄 Sincronizar Base de Datos en la Nube (Google Sheets)"):
            st.session_state.db_socios = cargar_bd(); st.session_state.db_invitaciones = cargar_invitaciones(); st.session_state.db_pagos = cargar_pagos(); st.session_state.db_directorio = cargar_directorio()
            st.success("Base de datos sincronizada.")

    # --- MÓDULO AJUSTES ---
    elif modulo_seleccionado == "Ajustes":
        st.markdown("<h3 style='font-size:18px; font-weight:700;'>Ajustes de Perfil</h3>", unsafe_allow_html=True)
        
        st.info("🔧 Módulo en construcción: Aquí podrás editar tu foto, notificaciones y grupo familiar.")
        
        st.write("---")
        st.markdown("<div class='btn-peligro'>", unsafe_allow_html=True)
        if st.button("Cerrar Sesión"):
            st.session_state.logueado = False
            st.session_state.usuario_actual = None
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)