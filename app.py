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
  "theme_color": "#000000",
  "background_color": "#000000",
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
        <meta name="theme-color" content="#000000">
        <link rel="apple-touch-icon" href="{icono_url}">
        <meta name="apple-mobile-web-app-capable" content="yes">
        <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
        <meta name="apple-mobile-web-app-title" content="Ventry">
    </head>
""", unsafe_allow_html=True)

# --- CSS AVANZADO: CLON FINTECH (RIAL STYLE) ---
st.markdown("""
    <style>
    /* Ocultar elementos base */
    #MainMenu {display: none;}
    footer {display: none;}
    [data-testid="collapsedControl"] {display: none;} 
    section[data-testid="stSidebar"] {display: none !important;} 
    
    @keyframes smoothFadeIn {
        0% { opacity: 0; transform: translateY(10px); }
        100% { opacity: 1; transform: translateY(0); }
    }
    .block-container { 
        padding-bottom: 120px !important; 
        padding-top: 1.5rem !important;
        animation: smoothFadeIn 0.4s cubic-bezier(0.16, 1, 0.3, 1) forwards;
    }
    
    /* PITCH BLACK BACKGROUND */
    .stApp { background-color: #000000; color: #FFFFFF; }
    h1, h2, h3, h4, h5, h6, p, span, label, div { font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; }
    
    .gradient-text { background: linear-gradient(90deg, #FF7B00, #FFC300); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    
    /* Alertas y Toasts */
    [data-testid="stAlert"] { background: #121212 !important; border: 1px solid #1C1C1E !important; border-radius: 16px !important; color: #fff !important; }
    [data-testid="stAlert"] p { color: #fff !important; font-weight: 500 !important; font-size: 14px !important; }
    
    /* Formularios */
    label, label p, label div, div[data-testid="stWidgetLabel"] p, .stTextInput p, .stSelectbox p, .stDateInput p, .stNumberInput p { color: #8E8E93 !important; font-weight: 600 !important; letter-spacing: 0.5px; font-size: 12px !important; text-transform: uppercase; margin-bottom: 4px; }
    [data-testid="stForm"] { background: #0A0A0A !important; border: 1px solid #1C1C1E !important; border-radius: 24px !important; padding: 25px !important; }
    input[type="text"], input[type="password"], input[type="number"], textarea, 
    .stTextInput div[data-baseweb="base-input"], .stDateInput div[data-baseweb="base-input"], 
    .stNumberInput div[data-baseweb="base-input"], .stSelectbox div[data-baseweb="select"] > div,
    div[data-baseweb="input"] { background-color: #121212 !important; color: #FFFFFF !important; -webkit-text-fill-color: #FFFFFF !important; border-radius: 14px !important; font-weight: 500 !important; font-size:15px !important;}
    div[data-baseweb="base-input"], div[data-baseweb="select"] > div { border: 1px solid #1C1C1E !important; }
    div[data-baseweb="input"]:focus-within, div[data-baseweb="select"]:focus-within, div[data-baseweb="base-input"]:focus-within { border-color: #FF6600 !important; background-color: #1C1C1E !important; }

    /* BOTONES */
    .stButton>button[kind="primary"], .stFormSubmitButton>button { width: 100%; border-radius: 18px !important; background: #FF6600 !important; color: #ffffff !important; font-weight: 700 !important; letter-spacing: 0.5px; font-size: 15px !important; border: none !important; padding: 14px !important; box-shadow: 0 4px 15px rgba(255, 102, 0, 0.2) !important; transition: transform 0.15s ease; justify-content: center !important; }
    .stButton>button[kind="primary"]:active, .stFormSubmitButton>button:active { transform: scale(0.96) !important; }
    
    .btn-secundario>div>button { background: #121212 !important; border: 1px solid #2C2C2E !important; color: #E0E0E0 !important; justify-content: center !important; box-shadow: none !important; border-radius: 18px !important; font-weight:600 !important; padding: 14px !important;}
    .btn-secundario>div>button:active { transform: scale(0.96) !important; background: #1C1C1E !important; }
    
    /* 🔴 LA PÍLDORA INFERIOR (BOTTOM NAV) */
    div.stRadio { 
        position: fixed !important; bottom: 25px !important; left: 50% !important; transform: translateX(-50%) !important; 
        width: 90% !important; max-width: 400px !important; 
        background: rgba(28, 28, 30, 0.9) !important; 
        backdrop-filter: saturate(180%) blur(20px) !important; -webkit-backdrop-filter: saturate(180%) blur(20px) !important; 
        border: 1px solid rgba(255, 255, 255, 0.1) !important; border-radius: 40px !important; padding: 8px 10px !important; z-index: 99999 !important; 
        box-shadow: 0 20px 40px rgba(0,0,0,0.8) !important;
    }
    div.stRadio > div[role="radiogroup"] { display: flex !important; flex-direction: row !important; justify-content: space-around !important; align-items: center !important; gap: 0 !important; width:100% !important;}
    div.stRadio > div[role="radiogroup"] > label { background: transparent !important; border: none !important; padding: 8px 4px !important; margin: 0 !important; cursor: pointer; position: relative; flex:1; display:flex; justify-content:center;}
    div.stRadio > div[role="radiogroup"] > label > div:first-child, div.stRadio > div[role="radiogroup"] > label span[data-baseweb="radio"], div.stRadio > div[role="radiogroup"] > label div[data-baseweb="radio"] { display: none !important; }
    div.stRadio > div[role="radiogroup"] > label div { color: #8E8E93 !important; font-size: 11px !important; font-weight: 600 !important; transition: all 0.2s ease; display:flex; flex-direction:column; align-items:center; gap:3px;}
    div.stRadio > div[role="radiogroup"] > label[data-checked="true"] div { color: #FFFFFF !important; font-weight: 700 !important; }

    /* TARJETAS FINANCIERAS (CLON RIAL) */
    .rial-card { background: #121212; border: 1px solid #1C1C1E; padding: 20px; border-radius: 20px; text-align: left; margin-bottom: 15px; }
    .rial-title { color: #8E8E93; font-size: 13px; font-weight: 600; margin-bottom: 8px; display:flex; align-items:center; gap:6px; letter-spacing: 0.5px;}
    .rial-saldo { color: #FFFFFF !important; font-size: 32px; font-weight: 800; margin: 0; letter-spacing: -1px; }
    .rial-monto-verde { color: #32d74b !important; }
    .rial-monto-rojo { color: #ff453a !important; }
    
    .menu-item { background: #121212; border: 1px solid #1C1C1E; padding: 18px 20px; border-radius: 16px; margin-bottom: 10px; display: flex; align-items: center; justify-content: space-between; color: #fff; font-weight: 600; font-size: 15px; cursor: pointer; transition: all 0.2s;}
    .menu-item:active { background: #1C1C1E; transform: scale(0.98); }
    .menu-icon { font-size: 20px; margin-right: 12px; }
    
    /* BOTÓN GARITA GIGANTE */
    .open-button-container { display: flex; justify-content: center; margin-top: 50px; margin-bottom: 30px;}
    .open-button { background: linear-gradient(145deg, #1C1C1E, #0A0A0A); border: 2px solid rgba(255, 102, 0, 0.4); border-radius: 50%; width: 200px; height: 200px; display: flex; flex-direction: column; justify-content: center; align-items: center; color: white; cursor: pointer; box-shadow: 0 10px 30px rgba(255,102,0,0.15); transition: all 0.15s ease; }
    .open-button:active { background: #FF6600; transform: scale(0.94); }

    /* CARNET DIGITAL */
    .dark-wrapper { background-color: transparent; padding: 10px 0px 30px 0px; display: flex; justify-content: center; }
    .glass-card { background: linear-gradient(135deg, #121212 0%, #050505 100%); border: 1px solid #1C1C1E; border-radius: 24px; padding: 40px 30px; width: 100%; max-width: 360px; box-shadow: 0 20px 50px rgba(0,0,0,0.8); position: relative; overflow: hidden; }
    .logo-m { font-size: 50px; font-weight: 200; margin: 0; line-height: 1; color: #ffffff !important; text-align:center;}
    .logo-magnum { font-size: 14px; font-weight: 700; letter-spacing: 5px; margin: 5px 0 0 0; color: #ffffff !important; text-align:center;}
    .logo-city { font-size: 9px; font-weight: 600; letter-spacing: 3px; color: #d4af37 !important; margin: 0; text-transform: uppercase; text-align:center;} 
    .logo-line { width: 40px; height: 2px; background-color: #d4af37; margin: 15px auto 30px auto; border-radius: 2px; }
    .info-group { margin-bottom: 16px; border-bottom: 1px solid #1C1C1E; padding-bottom: 8px; }
    .info-label { font-size: 11px; color: #8E8E93 !important; margin-bottom: 2px; text-transform: uppercase; font-weight: 600;}
    .info-value { font-size: 18px; font-weight: 600; color: #ffffff !important; }
    .qr-container { text-align: center; margin-top: 35px; }
    .qr-box { background: #ffffff; padding: 12px; border-radius: 16px; display: inline-block; margin-bottom: 15px; }
    .qr-box img { width: 150px; display: block; }
    .badge-aldia { background: #32d74b !important; color:#000 !important; padding: 6px 20px; border-radius: 30px; font-size: 11px; font-weight: 800; text-transform: uppercase;}
    .badge-moroso { background: #ff453a !important; color:#fff !important; padding: 6px 20px; border-radius: 30px; font-size: 11px; font-weight: 800; text-transform: uppercase;}
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

# --- FUNCIONES DE LÓGICA ---
def calcular_edad(fecha_nac_str):
    if not fecha_nac_str: return 0
    try:
        fecha_nac = datetime.strptime(fecha_nac_str, "%d/%m/%Y").date()
        hoy = datetime.today().date()
        return hoy.year - fecha_nac.year - ((hoy.month, hoy.day) < (fecha_nac.month, fecha_nac.day))
    except: return 0

def mes_actual_str(): return datetime.now().strftime("%m/%Y")
def sumar_un_mes(mes_str):
    if not mes_str or "/" not in mes_str: return mes_actual_str()
    m, y = map(int, mes_str.split("/"))
    m += 1
    if m > 12:
        m = 1
        y += 1
    return f"{m:02d}/{y}"
def comparar_meses(mes1, mes2):
    if not mes1 or not mes2: return -1
    m1, y1 = map(int, mes1.split("/"))
    m2, y2 = map(int, mes2.split("/"))
    if y1 < y2: return -1
    if y1 > y2: return 1
    if m1 < m2: return -1
    if m1 > m2: return 1
    return 0
def formato_mes_espanol(mes_str):
    meses = {"01":"Enero", "02":"Febrero", "03":"Marzo", "04":"Abril", "05":"Mayo", "06":"Junio", "07":"Julio", "08":"Agosto", "09":"Septiembre", "10":"Octubre", "11":"Noviembre", "12":"Diciembre"}
    try:
        m, y = mes_str.split("/")
        return f"{meses[m]} {y}"
    except: return mes_str

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

def cargar_bd():
    registros = hoja_bd.get_all_records()
    datos = {}
    for fila in registros:
        ced = str(fila.get("cedula", ""))
        if ced: 
            datos[ced] = {"nombre": str(fila.get("nombre", "")), "clave": str(fila.get("clave", "")), "accion": str(fila.get("accion", "")), "rol": str(fila.get("rol", "")), "parentesco": str(fila.get("parentesco", "N/A")), "fecha_nacimiento": str(fila.get("fecha_nacimiento", "")), "solvencia": str(fila.get("solvencia", "Pendiente")), "saldo": float(fila.get("saldo", 0.0)), "invitaciones": int(fila.get("invitaciones", 0)), "mes_pagado": str(fila.get("mes_pagado", "")), "cedula": ced}
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
# PANTALLA INICIAL: LOGIN Y REGISTRO
# ==========================================
if not st.session_state.logueado:
    st.markdown("""
        <div style='text-align: center; margin-top: 50px; margin-bottom: 25px;'>
            <img src="https://i.ibb.co/t7xWXXR/logo.png" width="90" style="margin-bottom: 15px; border-radius:20px; box-shadow: 0 10px 30px rgba(255,102,0,0.3);">
            <h1 style='font-weight: 900; font-size: 38px; margin-bottom: 0px; letter-spacing: 2px;' class='gradient-text'>VENTRY</h1>
            <p style='color: #8E8E93; font-size: 11px; letter-spacing: 4px; text-transform: uppercase; font-weight:600;'>Access Control</p>
        </div>
    """, unsafe_allow_html=True)
    
    if st.session_state.pantalla_auth == "login":
        if "mensaje_exito_registro" in st.session_state:
            st.success(st.session_state.mensaje_exito_registro)
            del st.session_state.mensaje_exito_registro
            
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
                    <span style="border: 1px solid #1C1C1E; background:#121212; padding: 13px 0px; border-radius: 18px; color: #8E8E93; font-size: 13px; font-weight: 600; cursor: pointer; display:block; margin-top: 1px;" onclick="alert('FaceID/TouchID se activará en la Fase 3 de compilación nativa.')">
                        🔒 FaceID
                    </span>
                </div>
            """, unsafe_allow_html=True)

        if boton_entrar:
            if cedula_ingresada in BASE_DATOS_SOCIOS:
                socio = BASE_DATOS_SOCIOS[cedula_ingresada]
                if clave_ingresada == str(socio["clave"]):
                    if socio.get("solvencia", "") == "En revision": st.warning("⏳ Tu cuenta fue creada pero aún se encuentra en revisión administrativa.")
                    else: st.session_state.logueado = True; st.session_state.usuario_actual = socio; st.rerun()
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
                r_accion = st.text_input("Número de Acción / ID Tienda")
                r_rol = st.selectbox("Rol de la Cuenta", ["Titular", "Familiar", "Concesionario", "Vigilante", "Administrador"])
            with col2:
                r_parentesco = st.selectbox("Parentesco / Puesto", ["N/A (Titular)", "Esposo(a)", "Hijo(a)", "Gerente", "Mesero", "Otro"])
            
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
                    st.session_state.mensaje_exito_registro = "✅ ¡Solicitud enviada! Hemos enviado un mensaje de confirmación para verificar tu cuenta. Por favor, espera la aprobación administrativa."
                    st.session_state.pantalla_auth = "login"
                    st.rerun()

# ==========================================
# APP NATIVA INTERNA
# ==========================================
else:
    if st.session_state.usuario_actual["cedula"] in BASE_DATOS_SOCIOS:
        st.session_state.usuario_actual = BASE_DATOS_SOCIOS[st.session_state.usuario_actual["cedula"]]
        
    socio_actual = st.session_state.usuario_actual
    rol_actual = socio_actual["rol"]

    saldo_accion = 0.0
    invitaciones_accion = 0
    mes_pagado_accion = ""
    for m in BASE_DATOS_SOCIOS.values():
        if str(m["accion"]) == str(socio_actual["accion"]) and m["rol"] == "Titular":
            saldo_accion = float(m.get('saldo', 0.0))
            invitaciones_accion = int(m.get('invitaciones', 0))
            mes_pagado_accion = str(m.get('mes_pagado', '')) 
            break

    # 🔴 GESTIÓN DEL MENÚ INTERNO (STACK NAVIGATION)
    if "menu_view" not in st.session_state: st.session_state.menu_view = "main"

    def cb_set_menu(vista):
        st.session_state.menu_view = vista

    def cb_nav_pagos(destino):
        st.session_state.sub_pagos = destino

    def cb_pagar_cuota(saldo, monto, mes, invites, tipo, nombre_mes, accion):
        ya_pagado = False
        for m in st.session_state.db_socios.values():
            if str(m["accion"]) == str(accion) and m["rol"] == "Titular":
                if m.get("mes_pagado", "") == mes: ya_pagado = True
                break
        
        if ya_pagado:
            st.session_state.mensaje_pago_exitoso = "⚠️ Transacción ignorada: El mes ya estaba pagado."
            st.session_state.sub_pagos = "menu"
            return
            
        nuevo_saldo = saldo - monto
        for ced, info in st.session_state.db_socios.items():
            if str(info["accion"]) == str(accion) and info["rol"] == "Titular":
                st.session_state.db_socios[ced]["saldo"] = nuevo_saldo
                st.session_state.db_socios[ced]["mes_pagado"] = mes
                st.session_state.db_socios[ced]["invitaciones"] = invites
                break
        
        for ced_fam, info_fam in st.session_state.db_socios.items():
            if str(info_fam["accion"]) == str(accion):
                st.session_state.db_socios[ced_fam]["solvencia"] = "Al dia"
        
        guardar_bd(st.session_state.db_socios)
        
        id_cargo = f"CRG-{str(uuid.uuid4())[:6].upper()}"
        st.session_state.db_pagos[id_cargo] = {
            "accion": accion, "metodo": "Sistema Ventry", 
            "referencia": f"CUOTA-{mes.replace('/','-')}", 
            "monto": monto, "fecha_reporte": datetime.now().strftime("%d/%m/%Y"), 
            "estatus": "Aprobado", "tipo": tipo
        }
        guardar_bd_pagos(st.session_state.db_pagos)
        
        st.session_state.mensaje_pago_exitoso = f"✅ Mensualidad de {nombre_mes} cancelada con éxito."
        st.session_state.sub_pagos = "menu"


    # --- MENÚ INFERIOR (PÍLDORA FINTECH CON 4 OPCIONES MÁXIMO) ---
    opciones_bottom = ["Inicio", "Carnet", "Finanzas", "Menú"]
    iconos_menu = {
        "Inicio": "🏠 Inicio", 
        "Carnet": "🪪 Carnet", 
        "Finanzas": "💳 Finanzas", 
        "Menú": "☰ Menú"
    }

    modulo_seleccionado_raw = st.radio("Nav", opciones_bottom, horizontal=True, label_visibility="collapsed", format_func=lambda x: iconos_menu.get(x, x))
    modulo_seleccionado = modulo_seleccionado_raw

    # Resetear el submenú si cambiamos de tab principal
    if modulo_seleccionado != "Menú":
        st.session_state.menu_view = "main"

    # --- MÓDULO 1: INICIO ---
    if modulo_seleccionado == "Inicio":
        st.markdown("""
<div style="text-align: center; margin-top: 20px;">
<h2 style="margin-bottom: 5px; font-size:26px; font-weight:900; color:#ffffff; letter-spacing:0.5px;">Magnum City Club</h2>
<p style="color: #8E8E93; font-size:12px; text-transform:uppercase; letter-spacing:3px; font-weight:600;">Puerta Principal</p>
<div class="open-button-container">
<div class="open-button">
<span style="font-size: 50px; margin-bottom:12px; text-shadow: 0 4px 15px rgba(0,0,0,0.5);">🔒</span>
<span style="font-size: 13px; font-weight:800; letter-spacing: 1.5px;">TOCA PARA ABRIR</span>
</div>
</div>
<p style="color: #8E8E93; margin-top: 35px; font-size:11px; font-weight:600; text-transform:uppercase; letter-spacing:1px;">Estatus: <span style="color:#FF6600; font-weight:800; text-shadow: 0 0 10px rgba(255,102,0,0.3);">Cerrado</span></p>
</div>
""", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Simular Apertura (Demo ESP32)", type="primary"): st.success("📡 Señal de apertura enviada a la garita.")

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
<div class="info-group"><p class="info-label">Socio</p><p class="info-value">{socio_actual['nombre']}</p></div>
<div class="info-group"><p class="info-label">Cédula</p><p class="info-value">{socio_actual['cedula']}</p></div>
<div class="info-group"><p class="info-label">Acción</p><p class="info-value">{socio_actual['accion']} <span style="font-size:13px; color:#8E8E93; font-weight:500;">({socio_actual['rol']})</span></p></div>
<div class="qr-container"><div class="qr-box"><img src="data:image/png;base64,{img_str}"></div><br><span class="status-badge {clase_badge}">{texto_badge}</span></div>
</div></div>
""", unsafe_allow_html=True)
        st.info("⏱️ Código dinámico. Se regenera cada 60s para evitar clonaciones.")
        if st.button("🔄 Actualizar Código", type="primary"): st.rerun()

    # --- MÓDULO 3: FINANZAS (CLON RIAL) ---
    elif modulo_seleccionado == "Finanzas":
        
        edad_usuario = calcular_edad(socio_actual.get("fecha_nacimiento", ""))
        if edad_usuario < 18 and edad_usuario > 0:
            st.markdown("<h3 style='font-size:24px; font-weight:800; color:#ffffff;'>Mis Finanzas</h3>", unsafe_allow_html=True)
            st.error("🔒 Acceso Restringido: El módulo financiero es exclusivo para los usuarios mayores de edad.")
            
        else:
            if "sub_pagos" not in st.session_state: st.session_state.sub_pagos = "menu"
            if "recibo_id" not in st.session_state: st.session_state.recibo_id = None

            saldo_favor = saldo_accion if saldo_accion > 0 else 0.0
            deuda = abs(saldo_accion) if saldo_accion < 0 else 0.0
            mes_actual = mes_actual_str()
            dia_actual = datetime.now().day
            nombre_mes_actual = formato_mes_espanol(mes_actual)
            
            if st.session_state.sub_pagos == "menu":
                st.markdown("<h3 style='font-size:24px; font-weight:800; color:#ffffff; margin-bottom: 20px;'>Mis balances</h3>", unsafe_allow_html=True)
                
                if "mensaje_pago_exitoso" in st.session_state:
                    if "⚠️" in st.session_state.mensaje_pago_exitoso: st.warning(st.session_state.mensaje_pago_exitoso)
                    else: st.success(st.session_state.mensaje_pago_exitoso)
                    del st.session_state.mensaje_pago_exitoso
                
                # GRID RIAL CLONE
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"""
                    <div class="rial-card">
                        <div class="rial-title">🇻🇪 Saldo Ventry</div>
                        <h3 class="rial-saldo rial-monto-verde">${saldo_favor:.2f}</h3>
                        <p style="color:#8E8E93; font-size:11px; margin-top:5px;">Fondo a favor</p>
                    </div>
                    """, unsafe_allow_html=True)
                with col2:
                    st.markdown(f"""
                    <div class="rial-card">
                        <div class="rial-title">🧾 Deuda Mensual</div>
                        <h3 class="rial-saldo rial-monto-rojo">${deuda:.2f}</h3>
                        <p style="color:#8E8E93; font-size:11px; margin-top:5px;">Por pagar</p>
                    </div>
                    """, unsafe_allow_html=True)

                st.write("")
                
                if rol_actual == "Titular":
                    if mes_pagado_accion == mes_actual:
                        st.success(f"🎉 **Cuota de {nombre_mes_actual} pagada.** Tu acción está solvente.")
                    else:
                        if dia_actual <= 10: st.info(f"🌟 Beneficio de Pronto Pago vigente. Cuota: $104 + 10 Pases Gratis.")
                        else: st.warning(f"⚠️ Fecha de corte superada. Cuota: $120. No incluye pases.")
                        
                        st.button(f"Pagar Mensualidad", type="primary", on_click=cb_nav_pagos, args=("pagar",))
                    st.write("")
                else:
                    st.info("ℹ️ El pago de la cuota de mantenimiento es gestionado por el Titular.")
                
                st.button("📥 + Agregar fondos (Abono)", type="primary", on_click=cb_nav_pagos, args=("recargar",))
                st.write("")
                st.button("🕒 Ver Movimientos", type="primary", on_click=cb_nav_pagos, args=("historial",))

            elif st.session_state.sub_pagos == "recargar":
                st.markdown("<h3 style='font-size:20px; font-weight:800; color:#FF6600;'>Agregar Fondos</h3>", unsafe_allow_html=True)
                
                with st.form("form_recarga"):
                    metodo_r = st.selectbox("Método de Pago", ["Pago Móvil", "Transferencia", "Zelle", "Efectivo Taquilla"])
                    ref_r = st.text_input("Nº de Referencia (Vacio si es efectivo)")
                    monto_r = st.number_input("Monto depositado ($)", min_value=1.0)
                    st.markdown("<br>", unsafe_allow_html=True)
                    btn_recarga = st.form_submit_button("ENVIAR REPORTE")
                    
                if btn_recarga:
                    if "Efectivo" not in metodo_r and not ref_r:
                        st.error("⚠️ Ingrese el número de referencia.")
                    else:
                        ref_final = ref_r if ref_r else "EFECTIVO"
                        id_pago = f"ABN-{str(uuid.uuid4())[:6].upper()}"
                        BASE_DATOS_PAGOS[id_pago] = {"accion": socio_actual["accion"], "metodo": metodo_r, "referencia": ref_final, "monto": monto_r, "fecha_reporte": datetime.now().strftime("%d/%m/%Y"), "estatus": "En Revisión", "tipo": "Abono a Billetera"}
                        guardar_bd_pagos(BASE_DATOS_PAGOS)
                        st.session_state.mensaje_pago_exitoso = "✅ Reporte enviado. El saldo se actualizará tras revisión."
                        st.session_state.sub_pagos = "menu"
                        st.rerun()
                
                st.write("")
                st.markdown("<div class='btn-secundario'>", unsafe_allow_html=True)
                st.button("← Volver a Balances", type="primary", on_click=cb_nav_pagos, args=("menu",))
                st.markdown("</div>", unsafe_allow_html=True)

            elif st.session_state.sub_pagos == "pagar":
                if mes_pagado_accion == mes_actual:
                    st.session_state.sub_pagos = "menu"
                    st.rerun()
                
                if dia_actual <= 10:
                    monto_cobro = 104.0
                    invites_premio = 10
                    tipo_cobro = f"Mensualidad {nombre_mes_actual} (Pronto Pago)"
                else:
                    monto_cobro = 120.0
                    invites_premio = 0
                    tipo_cobro = f"Mensualidad {nombre_mes_actual} (Tardío)"

                st.markdown(f"<h3 style='font-size:20px; font-weight:800; color:#FF6600;'>Confirmación de Pago</h3>", unsafe_allow_html=True)
                
                if saldo_accion >= monto_cobro:
                    st.info(f"💡 Se debitarán **${monto_cobro:.2f}** de tu Fondo Familiar.")
                    st.button(f"Confirmar Pago (${monto_cobro:.2f})", key="btn_pagar_mes", type="primary", on_click=cb_pagar_cuota, args=(saldo_accion, monto_cobro, mes_actual, invites_premio, tipo_cobro, nombre_mes_actual, socio_actual["accion"]))
                else:
                    st.error(f"❌ Fondo Insuficiente. Necesitas **${monto_cobro:.2f}** para pagar.")
                
                st.write("")
                st.markdown("<div class='btn-secundario'>", unsafe_allow_html=True)
                st.button("← Cancelar", type="primary", on_click=cb_nav_pagos, args=("menu",))
                st.markdown("</div>", unsafe_allow_html=True)

            elif st.session_state.sub_pagos == "historial":
                st.markdown("<h3 style='font-size:20px; font-weight:800; color:#fff;'>Movimientos</h3>", unsafe_allow_html=True)
                mis_pagos = {k: v for k, v in BASE_DATOS_PAGOS.items() if str(v["accion"]) == str(socio_actual["accion"])}
                mis_pagos_lista = list(mis_pagos.items())[::-1]
                
                if mis_pagos_lista:
                    for p_id, p_info in mis_pagos_lista:
                        es_cargo = "Cargo" in p_info.get('tipo', '') or "Mensualidad" in p_info.get('tipo', '') or "Consumo" in p_info.get('tipo', '')
                        
                        if es_cargo: color_status = "#ff453a"
                        elif p_info['estatus'] == "Aprobado": color_status = "#32d74b"
                        elif p_info['estatus'] == "En Revisión": color_status = "#FF6600"
                        else: color_status = "#ff453a"
                        
                        signo = "-" if es_cargo else "+"
                        monto_str = f"{signo}${float(p_info['monto']):.2f}"
                        
                        st.markdown(f"""
                        <div class='historial-card' style='border-left-color: {color_status};'>
                            <div style='display:flex; justify-content:space-between; margin-bottom:5px;'>
                                <b style='color:#ffffff; font-size:14px;'>{p_info.get('tipo', 'Abono a Billetera')}</b>
                                <b style='color:{color_status}; font-size:16px;'>{monto_str}</b>
                            </div>
                            <span style='color:#8E8E93; font-size:12px;'>{p_info['fecha_reporte']} | {p_info['metodo']}</span><br>
                        </div>
                        """, unsafe_allow_html=True)
                else: st.info("No hay movimientos registrados.")
                    
                st.write("")
                st.markdown("<div class='btn-secundario'>", unsafe_allow_html=True)
                st.button("← Volver a Balances", type="primary", on_click=cb_nav_pagos, args=("menu",))
                st.markdown("</div>", unsafe_allow_html=True)

    # --- MÓDULO 4: EL HUB (MENÚ APILADO) ---
    elif modulo_seleccionado == "Menú":
        
        # VISTA PRINCIPAL DEL HUB
        if st.session_state.menu_view == "main":
            st.markdown(f"""
            <div style="background:#121212; padding:20px; border-radius:20px; border:1px solid #1C1C1E; margin-bottom:25px; display:flex; align-items:center; gap:15px;">
                <div style="width:60px; height:60px; background:#FF6600; border-radius:50%; display:flex; justify-content:center; align-items:center; color:#fff; font-size:24px; font-weight:800;">
                    {socio_actual['nombre'][:2].upper()}
                </div>
                <div>
                    <h3 style="margin:0; font-size:18px; color:#fff;">{socio_actual['nombre']}</h3>
                    <p style="margin:0; color:#8E8E93; font-size:13px;">Acción {socio_actual['accion']} • {socio_actual['rol']}</p>
                </div>
            </div>
            <h4 style="color:#A0A0A0; font-size:13px; margin-bottom:15px; text-transform:uppercase; letter-spacing:1px;">Gestión del Club</h4>
            """, unsafe_allow_html=True)

            if rol_actual in ["Titular", "Familiar"]:
                st.markdown("<div class='menu-item' onclick='document.getElementById(\"btn_invitados\").click()'><div style='display:flex; align-items:center;'><span class='menu-icon'>🎟️</span> Pases e Invitados</div> <span style='color:#8E8E93;'>›</span></div>", unsafe_allow_html=True)
                st.button("btn_invitados", key="btn_invitados", on_click=cb_set_menu, args=("invitados",), help="Oculto", type="secondary", use_container_width=True)
                st.markdown("""<style>button[key="btn_invitados"] {display:none !important;}</style>""", unsafe_allow_html=True)

            if rol_actual == "Concesionario":
                st.markdown("<div class='menu-item' onclick='document.getElementById(\"btn_pos\").click()'><div style='display:flex; align-items:center;'><span class='menu-icon'>🛒</span> Ventry Pay (POS)</div> <span style='color:#8E8E93;'>›</span></div>", unsafe_allow_html=True)
                st.button("btn_pos", key="btn_pos", on_click=cb_set_menu, args=("pos",), help="Oculto")
                st.markdown("""<style>button[key="btn_pos"] {display:none !important;}</style>""", unsafe_allow_html=True)

            if rol_actual == "Vigilante":
                st.markdown("<div class='menu-item' onclick='document.getElementById(\"btn_garita\").click()'><div style='display:flex; align-items:center;'><span class='menu-icon'>🛡️</span> Control de Garita</div> <span style='color:#8E8E93;'>›</span></div>", unsafe_allow_html=True)
                st.button("btn_garita", key="btn_garita", on_click=cb_set_menu, args=("garita",), help="Oculto")
                st.markdown("""<style>button[key="btn_garita"] {display:none !important;}</style>""", unsafe_allow_html=True)

            if rol_actual == "Administrador":
                st.markdown("<div class='menu-item' onclick='document.getElementById(\"btn_admin\").click()'><div style='display:flex; align-items:center;'><span class='menu-icon'>📊</span> Consola Administrativa</div> <span style='color:#8E8E93;'>›</span></div>", unsafe_allow_html=True)
                st.button("btn_admin", key="btn_admin", on_click=cb_set_menu, args=("admin",), help="Oculto")
                st.markdown("""<style>button[key="btn_admin"] {display:none !important;}</style>""", unsafe_allow_html=True)

            st.markdown("<h4 style='color:#A0A0A0; font-size:13px; margin-top:25px; margin-bottom:15px; text-transform:uppercase; letter-spacing:1px;'>Cuenta</h4>", unsafe_allow_html=True)
            
            st.markdown("<div class='menu-item' onclick='document.getElementById(\"btn_ajustes\").click()'><div style='display:flex; align-items:center;'><span class='menu-icon'>⚙️</span> Ajustes de Perfil</div> <span style='color:#8E8E93;'>›</span></div>", unsafe_allow_html=True)
            st.button("btn_ajustes", key="btn_ajustes", on_click=cb_set_menu, args=("ajustes",), help="Oculto")
            st.markdown("""<style>button[key="btn_ajustes"] {display:none !important;}</style>""", unsafe_allow_html=True)

            st.write("---")
            st.markdown("<div class='btn-logout'>", unsafe_allow_html=True)
            if st.button("Cerrar Sesión"):
                st.session_state.logueado = False
                st.session_state.usuario_actual = None
                st.session_state.pantalla_auth = "login"
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        # SUB-VISTA: INVITADOS
        elif st.session_state.menu_view == "invitados":
            st.markdown("<h3 style='font-size:22px; font-weight:800; color:#fff; margin-bottom: 20px;'>Pases y Accesos</h3>", unsafe_allow_html=True)
            
            if "ultimo_pase_generado" not in st.session_state: st.session_state.ultimo_pase_generado = None

            if st.session_state.ultimo_pase_generado:
                pase_temp = st.session_state.ultimo_pase_generado
                url_base = "https://ventry.streamlit.app" 
                link_pase_digital = f"{url_base}/?pase={pase_temp['id']}"
                
                st.success(f"✅ Pase de {pase_temp['nombre']} emitido.")
                mensaje_ws = f"¡Hola {pase_temp['nombre']}! Aquí tienes tu pase para el *Magnum City Club*.\nFecha: {pase_temp['fecha']}\n👉 Abre tu código QR aquí:\n{link_pase_digital}"
                link_ws = f"https://wa.me/?text={urllib.parse.quote(mensaje_ws)}"
                st.markdown(f'<a href="{link_ws}" target="_blank" style="display:flex; justify-content:center; align-items:center; background:linear-gradient(135deg, #32d74b, #28a745); color:white; padding:16px; border-radius:16px; text-decoration:none; font-weight:800; letter-spacing:1px; margin-top:20px; margin-bottom:20px; box-shadow: 0 8px 25px rgba(50, 215, 75, 0.3); font-size:15px; text-transform:uppercase;">ENVIAR POR WHATSAPP</a>', unsafe_allow_html=True)
                
                st.markdown("<div class='btn-secundario'>", unsafe_allow_html=True)
                if st.button("← Volver a crear otra invitación", type="primary"):
                    st.session_state.ultimo_pase_generado = None
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
                    
            else:
                if mes_pagado_accion != mes_actual_str():
                    st.error("❌ Operación Denegada. Debes estar al día con el pago del mes actual para invitar.")
                else:
                    col1, col2 = st.columns(2)
                    with col1: st.markdown(f'<div class="rial-card" style="padding:15px;"><p class="rial-title" style="font-size:10px;">Pases Libres</p><h3 class="rial-invites">{invitaciones_accion}</h3></div>', unsafe_allow_html=True)
                    with col2: st.markdown(f'<div class="rial-card" style="padding:15px;"><p class="rial-title" style="font-size:10px;">Fondo Familiar</p><h3 class="rial-saldo" style="font-size:22px;">${saldo_accion:.2f}</h3></div>', unsafe_allow_html=True)
                    
                    if invitaciones_accion > 0: st.info(f"✨ Tienes {invitaciones_accion} pases de cortesía.")
                    else: st.warning("⚠️ Has agotado tus pases gratuitos. Se debitarán **$10.00** por este pase.")
                    
                    invitados_previos = BASE_DATOS_DIRECTORIO.get(socio_actual["accion"], {})
                    modo_ingreso = st.selectbox("Método de registro:", ["📝 Ingresar Nuevo Invitado", "⭐ Seleccionar de Favoritos"])
                    n_cedula_def, n_nombre_def, n_correo_def, n_nacimiento_def = "", "", "", datetime.today()
                    
                    if modo_ingreso == "⭐ Seleccionar de Favoritos":
                        if invitados_previos:
                            inv_sel = st.selectbox("Tu directorio:", list(invitados_previos.keys()), format_func=lambda x: f"{invitados_previos[x]['nombre']} (C.I: {x})")
                            n_cedula_def, n_nombre_def, n_correo_def = inv_sel, invitados_previos[inv_sel]['nombre'], invitados_previos[inv_sel]['correo']
                        else: st.info("Aún no tienes invitados en tu directorio.")

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
                        puede_invitar = True
                        if invitaciones_accion > 0:
                            for ced_fam, info_fam in BASE_DATOS_SOCIOS.items():
                                if str(info_fam["accion"]) == str(socio_actual["accion"]) and info_fam["rol"] == "Titular":
                                    BASE_DATOS_SOCIOS[ced_fam]["invitaciones"] = invitaciones_accion - 1
                                    break
                        else:
                            if saldo_accion >= 10.0:
                                for ced_fam, info_fam in BASE_DATOS_SOCIOS.items():
                                    if str(info_fam["accion"]) == str(socio_actual["accion"]) and info_fam["rol"] == "Titular":
                                        BASE_DATOS_SOCIOS[ced_fam]["saldo"] = saldo_accion - 10.0
                                        break
                                id_cargo = f"P-INV-{str(uuid.uuid4())[:6].upper()}"
                                BASE_DATOS_PAGOS[id_cargo] = {"accion": socio_actual["accion"], "metodo": "Saldo Ventry", "referencia": "PASE-EXTRA", "monto": 10.0, "fecha_reporte": datetime.now().strftime("%d/%m/%Y"), "estatus": "Aprobado", "tipo": "Cargo Pase Extra"}
                                guardar_bd_pagos(BASE_DATOS_PAGOS)
                            else:
                                puede_invitar = False
                                st.error("❌ Fondo insuficiente. Necesitas al menos $10.00.")
                        
                        if puede_invitar:
                            guardar_bd(BASE_DATOS_SOCIOS)
                            if guardar_contacto:
                                if socio_actual["accion"] not in BASE_DATOS_DIRECTORIO: BASE_DATOS_DIRECTORIO[socio_actual["accion"]] = {}
                                BASE_DATOS_DIRECTORIO[socio_actual["accion"]][n_cedula_inv] = {"nombre": n_nombre_inv, "correo": "", "fecha_nacimiento": ""}
                                guardar_bd_directorio(BASE_DATOS_DIRECTORIO)
                                
                            str_fecha = fecha_visita.strftime("%d/%m/%Y")
                            id_unico = f"INV-{socio_actual['accion']}-{str(uuid.uuid4())[:6].upper()}"
                            BASE_DATOS_INVITACIONES[id_unico] = {"accion": socio_actual["accion"], "fecha_visita": str_fecha, "cedula_invitado": n_cedula_inv, "nombre_invitado": n_nombre_inv, "fecha_nacimiento": "", "correo": "", "estatus": "Activo"}
                            guardar_bd_invitaciones(BASE_DATOS_INVITACIONES)
                            st.session_state.ultimo_pase_generado = {"id": id_unico, "nombre": n_nombre_inv, "fecha": str_fecha}
                            st.rerun()

            st.write("")
            st.markdown("<div class='btn-secundario'>", unsafe_allow_html=True)
            st.button("← Volver al Menú", type="primary", on_click=cb_set_menu, args=("main",))
            st.markdown("</div>", unsafe_allow_html=True)

        # SUB-VISTA: AJUSTES
        elif st.session_state.menu_view == "ajustes":
            st.markdown("<h3 style='font-size:22px; font-weight:800; color:#fff; margin-bottom: 20px;'>Ajustes</h3>", unsafe_allow_html=True)
            st.write("Módulo de ajustes en construcción para diseño fintech.")
            
            st.write("")
            st.markdown("<div class='btn-secundario'>", unsafe_allow_html=True)
            st.button("← Volver al Menú", type="primary", on_click=cb_set_menu, args=("main",))
            st.markdown("</div>", unsafe_allow_html=True)

        # SUB-VISTA: VENTRY PAY (POS)
        elif st.session_state.menu_view == "pos":
            st.markdown("<h3 style='font-size:24px; font-weight:800; color:#fff;'>Ventry Pay <span style='font-size:14px; color:#A0A0A0;'>(Punto de Venta)</span></h3>", unsafe_allow_html=True)
            st.write("Módulo POS en construcción para diseño fintech.")
            
            st.write("")
            st.markdown("<div class='btn-secundario'>", unsafe_allow_html=True)
            st.button("← Volver al Menú", type="primary", on_click=cb_set_menu, args=("main",))
            st.markdown("</div>", unsafe_allow_html=True)

        # SUB-VISTA: GARITA
        elif st.session_state.menu_view == "garita":
            st.markdown("<h3 style='font-size:24px; font-weight:800; color:#fff;'>Modo Operativo: Garita</h3>", unsafe_allow_html=True)
            st.write("Escáner en construcción para diseño fintech.")
            
            st.write("")
            st.markdown("<div class='btn-secundario'>", unsafe_allow_html=True)
            st.button("← Volver al Menú", type="primary", on_click=cb_set_menu, args=("main",))
            st.markdown("</div>", unsafe_allow_html=True)

        # SUB-VISTA: ADMIN
        elif st.session_state.menu_view == "admin":
            st.markdown("<h3 style='font-size:24px; font-weight:800; color:#FF6600;'>Consola Administrativa VIP</h3>", unsafe_allow_html=True)
            st.write("Panel Admin en construcción para diseño fintech.")
            
            st.write("")
            st.markdown("<div class='btn-secundario'>", unsafe_allow_html=True)
            st.button("← Volver al Menú", type="primary", on_click=cb_set_menu, args=("main",))
            st.markdown("</div>", unsafe_allow_html=True)