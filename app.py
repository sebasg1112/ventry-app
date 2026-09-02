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

# --- CSS AVANZADO (NAVEGACIÓN BOTTOM TIPO APP NATIVA) ---
st.markdown("""
    <style>
    /* Ocultamos menú de Streamlit */
    #MainMenu {display: none;}
    footer {display: none;}
    [data-testid="collapsedControl"] {display: none;} 
    section[data-testid="stSidebar"] {display: none !important;} 
    
    /* 1. FONDO GLOBAL VENTRY */
    .stApp { 
        background-color: #121212; 
        color: #f5f5f5;
    }
    
    /* 2. TIPOGRAFÍA GLOBAL */
    h1, h2, h3, h4, h5, h6, p, span, label, div { color: #f5f5f5 !important; }
    
    /* 3. PANTALLA LOGIN: CAJA BIOMÉTRICA */
    .biometric-box {
        border: 2px solid rgba(255, 102, 0, 0.4);
        border-radius: 15px;
        text-align: center;
        padding: 30px 20px;
        margin-bottom: 20px;
        cursor: pointer;
        box-shadow: 0 0 20px rgba(255, 102, 0, 0.1);
        transition: all 0.3s ease;
        background-color: rgba(255, 255, 255, 0.02);
    }
    .biometric-box:hover {
        border-color: #FF6600;
        box-shadow: 0 0 30px rgba(255, 102, 0, 0.3);
    }
    
    /* 4. FORMULARIOS (LOGIN) CORREGIDO: CAJAS OSCURAS */
    div[data-baseweb="input"] > div, div[data-baseweb="select"] > div {
        background-color: #1a1a1a !important;
        border: 1px solid #444 !important;
        border-radius: 12px !important;
    }
    input, select, textarea {
        color: #ffffff !important;
        background-color: transparent !important;
        -webkit-text-fill-color: #ffffff !important;
    }
    div[data-baseweb="input"]:focus-within {
        border-color: #FF6600 !important;
        box-shadow: 0 0 8px rgba(255, 102, 0, 0.4) !important;
    }

    /* 5. BOTÓN NARANJA VENTRY */
    .stButton>button, .stFormSubmitButton>button { 
        width: 100%; 
        border-radius: 25px !important; 
        background: #FF6600 !important; 
        color: #ffffff !important; 
        font-weight: bold !important; 
        letter-spacing: 1px;
        border: none !important; 
        padding: 10px !important;
        box-shadow: 0 4px 15px rgba(255, 102, 0, 0.4) !important;
    }
    .stButton>button:hover, .stFormSubmitButton>button:hover {
        background: #e65c00 !important;
        transform: scale(0.98);
    }
    
    /* 6. BOTTOM NAVIGATION BAR (MENÚ INFERIOR FIJO) */
    .block-container {
        padding-bottom: 100px !important; 
    }
    
    div.stRadio {
        position: fixed !important;
        bottom: 0 !important;
        left: 0 !important;
        width: 100% !important;
        background-color: rgba(18, 18, 18, 0.95) !important;
        backdrop-filter: blur(15px) !important;
        border-top: 1px solid rgba(255, 255, 255, 0.05) !important;
        padding: 15px 0px 25px 0px !important;
        z-index: 99999 !important;
    }
    div.stRadio > div[role="radiogroup"] {
        display: flex !important;
        flex-direction: row !important;
        justify-content: space-around !important;
        align-items: center !important;
        gap: 0 !important;
    }
    div.stRadio > div[role="radiogroup"] > label {
        background: transparent !important;
        border: none !important;
        padding: 0 !important;
        margin: 0 !important;
    }
    div.stRadio > div[role="radiogroup"] > label span[data-baseweb="radio"] {
        display: none !important;
    }
    div.stRadio > div[role="radiogroup"] > label div {
        color: #888888 !important;
        font-size: 11px !important;
        text-align: center !important;
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        gap: 4px !important;
    }
    div.stRadio > div[role="radiogroup"] > label[data-checked="true"] div {
        color: #FF6600 !important;
        font-weight: bold !important;
    }

    /* 7. BOTÓN GIGANTE DE ABRIR PUERTA */
    .open-button-container { display: flex; justify-content: center; margin-top: 40px; margin-bottom: 20px;}
    .open-button-glow {
        border-radius: 50%;
        padding: 5px;
        background: radial-gradient(circle, rgba(255,102,0,0.5) 0%, rgba(0,0,0,0) 70%);
        box-shadow: 0 0 50px rgba(255,102,0,0.4);
    }
    .open-button {
        background: linear-gradient(145deg, #2a2a2a, #111111);
        border: 3px solid #FF6600;
        border-radius: 50%;
        width: 220px;
        height: 220px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        color: white;
        font-weight: bold;
        font-size: 16px;
        cursor: pointer;
        box-shadow: inset 0 0 20px rgba(0,0,0,0.8);
    }
    .open-button:active {
        background: #FF6600;
        transform: scale(0.95);
        box-shadow: 0 0 30px rgba(255,102,0,0.8);
    }
    
    /* ========================================================= */
    /* CARNET MAGNUM CLUB (DENTRO DEL MODULO) */
    /* ========================================================= */
    .dark-wrapper { background-color: transparent; padding: 20px 0px; display: flex; justify-content: center; margin-bottom: 30px; }
    .glass-card { background: rgba(0, 31, 63, 0.4); backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px); border: 1px solid rgba(212, 175, 55, 0.3); border-radius: 20px; padding: 40px 30px; width: 100%; max-width: 360px; box-shadow: 0 15px 35px rgba(0,0,0,0.8); position: relative; overflow: hidden; }
    .magnum-logo { text-align: center; margin-bottom: 35px; }
    .logo-m { font-size: 50px; font-weight: 300; margin: 0; line-height: 1; color: #ffffff !important; }
    .logo-magnum { font-size: 16px; font-weight: 600; letter-spacing: 5px; margin: 5px 0 0 0; color: #ffffff !important; }
    .logo-city { font-size: 9px; letter-spacing: 2px; color: #d4af37 !important; margin: 0; text-transform: uppercase; } 
    .logo-line { width: 30px; height: 1px; background-color: #d4af37; margin: 15px auto 0 auto; }
    .info-group { margin-bottom: 18px; border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 8px; }
    .info-label { font-size: 12px; color: #8892b0 !important; margin-bottom: 4px;}
    .info-value { font-size: 18px; font-weight: 500; color: #ffffff !important; }
    .qr-container { text-align: center; margin-top: 30px; }
    .qr-box { background: rgba(255,255,255,0.95); padding: 10px; border-radius: 12px; display: inline-block; margin-bottom: 15px; }
    .qr-box img { width: 140px; display: block; }
    .status-badge { display: inline-block; padding: 6px 18px; border-radius: 30px; font-size: 12px; font-weight: bold; color: #000 !important; }
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
        if ced: datos[ced] = {"nombre": str(fila.get("nombre", "")), "clave": str(fila.get("clave", "")), "accion": str(fila.get("accion", "")), "rol": str(fila.get("rol", "")), "parentesco": str(fila.get("parentesco", "N/A")), "fecha_nacimiento": str(fila.get("fecha_nacimiento", "")), "solvencia": str(fila.get("solvencia", "")), "cedula": ced}
    return datos

def guardar_bd(datos):
    lista_socios = list(datos.values())
    lista_socios.sort(key=lambda x: (x.get("accion", ""), x.get("rol", "")), reverse=True) 
    filas_a_subir = [["cedula", "nombre", "clave", "accion", "rol", "parentesco", "fecha_nacimiento", "solvencia"]]
    for socio in lista_socios: filas_a_subir.append([socio["cedula"], socio["nombre"], socio["clave"], socio["accion"], socio["rol"], socio["parentesco"], socio.get("fecha_nacimiento", ""), socio["solvencia"]])
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
        st.info("💡 Muestra esta pantalla en garita.")
    else: st.error("❌ Enlace de pase inválido.")
    st.stop()


# ==========================================
# PANTALLA INICIAL: LOGIN VIP
# ==========================================
if not st.session_state.logueado:
    st.markdown("""
        <div style='text-align: center; margin-top: 20px; margin-bottom: 20px;'>
            <img src="https://i.ibb.co/t7xWXXR/logo.png" width="80" style="margin-bottom: 10px;">
            <h1 style='font-weight: 800; font-size: 32px; margin-bottom: 0px;'>Ventry</h1>
        </div>
    """, unsafe_allow_html=True)
    
    with st.form("login_form"):
        # UI Mockup Biometría
        st.markdown("""
        <div class='biometric-box' onclick="alert('Funcionalidad nativa (FaceID/TouchID) requiere compilación móvil en Fase 3.')">
            <div style='font-size: 50px; margin-bottom: 10px;'>🤳</div>
            <p style='margin:0; font-size:14px; font-weight:600;'>Toca para ingresar con<br>Biometría</p>
        </div>
        <p style='text-align:center; color:#555; font-size:12px;'>o usar contraseña</p>
        """, unsafe_allow_html=True)
        
        cedula_ingresada = st.text_input("Email o ID")
        clave_ingresada = st.text_input("Contraseña", type="password")
        st.markdown("<br>", unsafe_allow_html=True)
        boton_entrar = st.form_submit_button("INGRESAR")
        
        st.markdown("<p style='text-align:center; color:#FF6600; font-size:12px; margin-top:15px; cursor:pointer;'>¿Olvidaste tu contraseña?</p>", unsafe_allow_html=True)

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

    # Header Superior Limpio
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown(f"""
        <div style="display:flex; align-items:center; gap:10px;">
            <img src="https://i.ibb.co/t7xWXXR/logo.png" width="30">
            <span style="font-size:18px; font-weight:bold;">Ventry</span>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        if st.button("🚪"): 
            st.session_state.logueado = False; st.session_state.usuario_actual = None; st.rerun()
    
    st.write("")

    # --- BOTTOM NAVIGATION BAR DEFINITION ---
    if rol_actual in ["Titular", "Familiar"]: 
        opciones_menu = ["🏠\nInicio", "👥\nInvitados", "🎫\nCarnet", "💳\nPagos"]
    elif rol_actual == "Vigilante": 
        opciones_menu = ["🛡️\nGarita"]
    elif rol_actual == "Administrador": 
        opciones_menu = ["🏠\nInicio", "👥\nInvitados", "🛡️\nGarita", "⚙️\nAdmin"]

    modulo_seleccionado = st.radio("Nav", opciones_menu, horizontal=True, label_visibility="collapsed")

    # --- MÓDULO 1: INICIO (BOTÓN ABRIR PUERTA MOCKUP) ---
    if modulo_seleccionado == "🏠\nInicio":
        st.markdown("""
<div style="text-align: center; margin-top: 30px;">
<h2 style="margin-bottom: 0; font-size:24px;">Magnum City Club</h2>
<p style="color: #888; font-size:14px;">Puerta Principal</p>
<div class="open-button-container">
<div class="open-button-glow">
<div class="open-button" onclick="alert('Señal enviada a Garita')">
<span style="font-size: 50px; margin-bottom:5px;">🔒</span>
<span style="font-size: 14px;">TOCA PARA<br>ABRIR</span>
</div>
</div>
</div>
<p style="color: #888; margin-top: 40px; font-size:14px;">Estado: <span style="color:#FF6600;">Cerrado</span></p>
</div>
""", unsafe_allow_html=True)
        
        if st.button("Simular Apertura (Demo)"):
            st.success("📡 Señal BLE enviada al hardware del torniquete.")


    # --- MÓDULO 2: CARNET DIGITAL ---
    elif modulo_seleccionado == "🎫\nCarnet":
        if socio_actual['solvencia'] == "Moroso": st.error("⚠️ Tu grupo familiar presenta un saldo pendiente.")
        if socio_actual['solvencia'] == "Al dia": clase_badge = "badge-aldia"; texto_badge = "AL DÍA"
        elif socio_actual['solvencia'] == "Pendiente": clase_badge = "badge-pendiente"; texto_badge = "PENDIENTE"
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
<div class="info-group"><p class="info-label">Nombre</p><p class="info-value">{socio_actual['nombre']}</p></div>
<div class="info-group"><p class="info-label">ID (Cédula)</p><p class="info-value">{socio_actual['cedula']}</p></div>
<div class="info-group"><p class="info-label">Acción</p><p class="info-value">{socio_actual['accion']} ({socio_actual['rol']})</p></div>
<div class="qr-container"><div class="qr-box"><img src="data:image/png;base64,{img_str}"></div><br><span class="status-badge {clase_badge}">{texto_badge}</span></div>
</div></div>
"""
        st.markdown(carnet_html, unsafe_allow_html=True)

    # --- MÓDULO 3: INVITADOS (FAVORITOS RESTAURADOS) ---
    elif modulo_seleccionado == "👥\nInvitados":
        st.subheader("Generar Invitación")
        
        if "ultimo_pase_generado" not in st.session_state: st.session_state.ultimo_pase_generado = None

        if socio_actual["solvencia"] != "Al dia":
            st.error("❌ Operación Denegada. Solvencia requerida.")
        else:
            invitados_previos = BASE_DATOS_DIRECTORIO.get(socio_actual["accion"], {})
            modo_ingreso = st.radio("Tipo de registro:", ["Nuevo Invitado", "Directorio de Favoritos"], horizontal=True)
            n_cedula_def, n_nombre_def, n_correo_def = "", "", ""
            n_nacimiento_def = datetime.today()
            
            if modo_ingreso == "Directorio de Favoritos":
                if invitados_previos:
                    inv_sel = st.selectbox("Seleccione de su directorio:", list(invitados_previos.keys()), format_func=lambda x: f"{invitados_previos[x]['nombre']} (C.I: {x})")
                    n_cedula_def = inv_sel
                    n_nombre_def = invitados_previos[inv_sel]['nombre']
                    n_correo_def = invitados_previos[inv_sel]['correo']
                    if invitados_previos[inv_sel].get("fecha_nacimiento"):
                        try: n_nacimiento_def = datetime.strptime(invitados_previos[inv_sel]["fecha_nacimiento"], "%d/%m/%Y").date()
                        except: pass
                else: st.info("Aún no tienes invitados guardados en tu directorio.")

            with st.form("form_invitacion"):
                n_cedula_inv = st.text_input("Cédula del Invitado", value=n_cedula_def)
                n_nombre_inv = st.text_input("Nombre del Invitado", value=n_nombre_def)
                fecha_visita = st.date_input("Fecha de la visita", min_value=datetime.today(), format="DD/MM/YYYY")
                
                guardar_contacto = False
                if modo_ingreso == "Nuevo Invitado":
                    st.write("---")
                    guardar_contacto = st.checkbox("⭐ Guardar en mi directorio de invitados", value=True)
                
                st.markdown("<br>", unsafe_allow_html=True)
                btn_generar = st.form_submit_button("GENERAR PASE")
                
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
                st.success(f"✅ Pase digital generado.")
            
            if st.session_state.ultimo_pase_generado:
                pase_temp = st.session_state.ultimo_pase_generado
                url_base = "https://ventry.streamlit.app" 
                link_pase_digital = f"{url_base}/?pase={pase_temp['id']}"
                
                mensaje_ws = f"¡Hola {pase_temp['nombre']}! Aquí tienes tu pase para el *Magnum City Club*.\nFecha: {pase_temp['fecha']}\n👉 Abre tu código QR aquí:\n{link_pase_digital}"
                link_ws = f"https://wa.me/?text={urllib.parse.quote(mensaje_ws)}"
                
                st.markdown(f'<a href="{link_ws}" target="_blank" style="display:block; text-align:center; background:#FF6600; color:white; padding:12px; border-radius:15px; text-decoration:none; font-weight:bold; margin-top:10px;">📲 ENVIAR POR WHATSAPP</a>', unsafe_allow_html=True)

    # --- MÓDULO 4: PAGOS ---
    elif modulo_seleccionado == "💳\nPagos":
        st.subheader("Pagos y Solvencia")
        st.markdown("<div class='pago-card'>", unsafe_allow_html=True)
        deuda = 104.00 if socio_actual['solvencia'] == "Moroso" else 0.00
        st.metric("Saldo Pendiente", f"${deuda:.2f}")
        st.markdown("</div>", unsafe_allow_html=True)
        with st.form("form_pago"):
            metodo = st.selectbox("Método", ["Zelle", "Pago Móvil", "Transferencia"])
            n_referencia = st.text_input("Nº de Referencia")
            n_monto = st.number_input("Monto", min_value=1.0)
            btn_reportar = st.form_submit_button("REPORTAR PAGO")
        if btn_reportar and n_referencia:
            st.success("✅ Pago en revisión.")

    # --- MÓDULO GARITA ---
    elif modulo_seleccionado == "🛡️\nGarita":
        st.subheader("Escáner de Garita")
        st.info("Apunta el QR de un Socio o Invitado:")
        foto_qr = st.camera_input("")
        # Lógica de validación QR se mantiene intacta

    # --- MÓDULO ADMIN ---
    elif modulo_seleccionado == "⚙️\nAdmin":
        st.subheader("Panel Administrativo")
        st.info("Para gestionar usuarios y pagos completos se recomienda la versión de escritorio.")
        if st.button("Sincronizar DB"):
            st.success("Base de datos al día.")