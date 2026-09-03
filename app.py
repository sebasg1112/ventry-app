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

# --- CSS AVANZADO: BLINDAJE NUCLEAR Y DISEÑO PREMIUM ---
st.markdown("""
    <style>
    #MainMenu {display: none;}
    footer {display: none;}
    [data-testid="collapsedControl"] {display: none;} 
    section[data-testid="stSidebar"] {display: none !important;} 
    
    .stApp { background-color: #0d0d0d; color: #f5f5f5; }
    h1, h2, h3, h4, h5, h6, p, span, label, div { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; }
    
    /* ETIQUETAS (LABELS VISIBLES) */
    label, label p, label div, div[data-testid="stWidgetLabel"] p, .stTextInput p, .stSelectbox p, .stDateInput p, .stNumberInput p { color: #ffffff !important; font-weight: 600 !important; letter-spacing: 0.5px; }
    
    /* BLINDAJE NUCLEAR DE FORMULARIOS Y ELEMENTOS FLOTANTES */
    [data-testid="stForm"] { background-color: #0d0d0d !important; border: 1px solid #333 !important; border-radius: 15px !important; padding: 20px !important; }
    .stTextInput input, .stNumberInput input, .stDateInput input, textarea { background-color: #1a1a1a !important; color: #ffffff !important; -webkit-text-fill-color: #ffffff !important; }
    div[data-baseweb="input"] > div, div[data-baseweb="select"] > div, div[data-baseweb="base-input"] { background-color: #1a1a1a !important; border-radius: 10px !important; border: 1px solid #333 !important; color: #ffffff !important; }
    div[data-baseweb="select"] span { color: #ffffff !important; }
    div[data-baseweb="popover"] *, div[data-baseweb="menu"] *, ul[role="listbox"] *, li[role="option"] *, div[role="dialog"] *, div[data-baseweb="calendar"] * { background-color: #1a1a1a !important; color: #ffffff !important; }
    li[role="option"]:hover *, li[role="option"][aria-selected="true"] * { background-color: #FF6600 !important; color: #ffffff !important; }
    div[data-baseweb="input"]:focus-within, div[data-baseweb="select"]:focus-within { border-color: #FF6600 !important; box-shadow: 0 0 8px rgba(255, 102, 0, 0.4) !important; }

    /* ========================================================= */
    /* BOTONES (NATIVOS Y ACCIÓN) */
    /* ========================================================= */
    
    /* BOTONES DE ACCIÓN PRINCIPAL (Naranjas Ventry) */
    .stButton>button[kind="primary"], .stFormSubmitButton>button { 
        width: 100%; border-radius: 20px !important; background: #FF6600 !important; color: #ffffff !important; 
        font-weight: 700 !important; letter-spacing: 0.5px; border: none !important; padding: 12px !important; 
        box-shadow: 0 4px 15px rgba(255, 102, 0, 0.3) !important; transition: all 0.2s ease-in-out; justify-content: center !important;
    }
    .stButton>button[kind="primary"]:active, .stFormSubmitButton>button:active { background: #e65c00 !important; transform: scale(0.98); }
    
    /* BOTONES SECUNDARIOS ESPECIALES (Volver / Peligro) */
    .btn-secundario>div>button { background: transparent !important; border: 1px solid #555 !important; color: #aaa !important; justify-content: center !important; box-shadow: none !important; }
    .btn-secundario>div>button:hover { border-color: #FF6600 !important; color: #FF6600 !important; }
    .btn-peligro>div>button { background: rgba(220, 53, 69, 0.1) !important; border: 1px solid rgba(220, 53, 69, 0.5) !important; color: #ff6b6b !important; justify-content: center !important; box-shadow: none !important; }
    
    /* BOTTOM NAVIGATION BAR */
    .block-container { padding-bottom: 120px !important; }
    div.stRadio { position: fixed !important; bottom: 0 !important; left: 0 !important; width: 100% !important; background-color: rgba(13, 13, 13, 0.95) !important; backdrop-filter: blur(20px) !important; border-top: 1px solid rgba(255, 255, 255, 0.05) !important; padding: 15px 0px 25px 0px !important; z-index: 99999 !important; }
    div.stRadio > div[role="radiogroup"] { display: flex !important; flex-direction: row !important; justify-content: space-evenly !important; align-items: center !important; gap: 0 !important; }
    div.stRadio > div[role="radiogroup"] > label { background: transparent !important; border: none !important; padding: 5px 10px !important; margin: 0 !important; cursor: pointer; }
    div.stRadio > div[role="radiogroup"] > label > div:first-child, div.stRadio > div[role="radiogroup"] > label span[data-baseweb="radio"], div.stRadio > div[role="radiogroup"] > label div[data-baseweb="radio"] { display: none !important; }
    div.stRadio > div[role="radiogroup"] > label div { color: #777777 !important; font-size: 11px !important; font-weight: 600 !important; text-transform: uppercase; letter-spacing: 1px; }
    div.stRadio > div[role="radiogroup"] > label[data-checked="true"] div { color: #FF6600 !important; font-weight: 800 !important; }

    /* BILLETERA CARDS */
    .wallet-card { background: linear-gradient(145deg, #1a1a1a, #0d0d0d); border: 1px solid #333; padding: 20px; border-radius: 15px; text-align: center; margin-bottom: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.4); }
    .wallet-title { color: #888; font-size: 12px; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 5px; font-weight: bold; }
    .wallet-saldo { color: #4ade80 !important; font-size: 32px; font-weight: 800; margin: 0; }
    .wallet-deuda { color: #ff6b6b !important; font-size: 24px; font-weight: 700; margin: 0; }
    .historial-card { background: #1a1a1a; padding: 15px; border-radius: 12px; margin-bottom: 10px; border-left: 3px solid #FF6600; }

    /* BOTÓN ABRIR PUERTA */
    .open-button-container { display: flex; justify-content: center; margin-top: 40px; margin-bottom: 20px;}
    .open-button-glow { border-radius: 50%; padding: 8px; background: radial-gradient(circle, rgba(255,102,0,0.4) 0%, rgba(0,0,0,0) 70%); box-shadow: 0 0 60px rgba(255,102,0,0.3); }
    .open-button { background: linear-gradient(145deg, #222222, #0a0a0a); border: 2px solid #FF6600; border-radius: 50%; width: 200px; height: 200px; display: flex; flex-direction: column; justify-content: center; align-items: center; color: white; cursor: pointer; box-shadow: inset 0 0 25px rgba(0,0,0,0.9); transition: transform 0.1s ease; }
    .open-button:active { background: #FF6600; transform: scale(0.96); }
    
    /* CARNET */
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
def cargar_historial():
    try:
        vals = hoja_historial.get_all_values()
        if len(vals) > 1:
            return [{"fecha": r[0], "accion": r[1], "nombre": r[2], "via": r[3], "movimiento": r[4]} for r in vals[1:][::-1]]
        return []
    except:
        return []

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
            datos[ced] = {
                "nombre": str(fila.get("nombre", "")), "clave": str(fila.get("clave", "")), 
                "accion": str(fila.get("accion", "")), "rol": str(fila.get("rol", "")), 
                "parentesco": str(fila.get("parentesco", "N/A")), "fecha_nacimiento": str(fila.get("fecha_nacimiento", "")), 
                "solvencia": str(fila.get("solvencia", "")), "saldo": float(fila.get("saldo", 0.0)), "cedula": ced
            }
    return datos

def guardar_bd(datos):
    lista_socios = list(datos.values())
    lista_socios.sort(key=lambda x: (x.get("accion", ""), x.get("rol", "")), reverse=True) 
    filas_a_subir = [["cedula", "nombre", "clave", "accion", "rol", "parentesco", "fecha_nacimiento", "solvencia", "saldo"]]
    for socio in lista_socios: filas_a_subir.append([socio["cedula"], socio["nombre"], socio["clave"], socio["accion"], socio["rol"], socio["parentesco"], socio.get("fecha_nacimiento", ""), socio.get("solvencia", "Pendiente"), socio.get("saldo", 0.0)])
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
            if id_p: datos[id_p] = {"accion": str(f.get("accion", "")), "metodo": str(f.get("metodo", "")), "referencia": str(f.get("referencia", "")), "monto": str(f.get("monto", "")), "fecha_reporte": str(f.get("fecha_reporte", "")), "estatus": str(f.get("estatus", "")), "tipo": str(f.get("tipo", "Pago de Cuota"))}
        return datos
    except: return {}

def guardar_bd_pagos(datos):
    filas = [["id_pago", "accion", "metodo", "referencia", "monto", "fecha_reporte", "estatus", "tipo"]]
    for k, v in datos.items(): filas.append([k, v["accion"], v["metodo"], v["referencia"], v["monto"], v["fecha_reporte"], v["estatus"], v.get("tipo", "Pago de Cuota")])
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

# --- BLINDAJE DE MEMORIA INDEPENDIENTE ---
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
            
        st.markdown("<p style='text-align:center; color:#888; font-size:12px; margin-top:25px; cursor:pointer;'>¿Olvidaste tu contraseña?</p>", unsafe_allow_html=True)

        if boton_entrar:
            if cedula_ingresada in BASE_DATOS_SOCIOS:
                socio = BASE_DATOS_SOCIOS[cedula_ingresada]
                if clave_ingresada == str(socio["clave"]):
                    if socio.get("solvencia", "") == "En revision":
                        st.warning("⏳ Su cuenta fue creada y está en revisión. Debe esperar aprobación administrativa.")
                    else:
                        st.session_state.logueado = True; st.session_state.usuario_actual = socio; st.rerun()
                else: 
                    st.error("❌ Contraseña incorrecta.")
            else: 
                st.error("⚠️ Usuario no registrado.")

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
            if not r_cedula or not r_nombre or not r_accion or not r_clave: 
                st.error("⚠️ Todos los campos son obligatorios.")
            elif r_clave != r_clave_conf: 
                st.error("❌ Las contraseñas no coinciden.")
            elif r_cedula in BASE_DATOS_SOCIOS: 
                st.error("⚠️ Esta cédula ya se encuentra registrada.")
            else:
                r_acc_norm = r_accion.strip().lstrip('0') or "0"
                titular_existente = any(info["accion"] == r_acc_norm and info["rol"] == "Titular" for info in BASE_DATOS_SOCIOS.values()) if r_rol == "Titular" else False
                
                if titular_existente: 
                    st.error(f"⚠️ Operación Denegada: La Acción {r_acc_norm} ya tiene un Titular registrado.")
                else:
                    BASE_DATOS_SOCIOS[r_cedula] = {
                        "nombre": r_nombre, "clave": r_clave, "accion": r_acc_norm, "rol": r_rol, 
                        "parentesco": r_parentesco, "fecha_nacimiento": r_nacimiento.strftime("%d/%m/%Y"), 
                        "solvencia": "En revision", "saldo": 0.0, "cedula": r_cedula
                    }
                    guardar_bd(BASE_DATOS_SOCIOS)
                    st.success("✅ Su cuenta fue creada, esta en revision, debe esperar aprobacion.")

# ==========================================
# APP NATIVA INTERNA
# ==========================================
else:
    socio_actual = st.session_state.usuario_actual
    rol_actual = socio_actual["rol"]

    st.markdown(f"""
    <div style="display:flex; align-items:center; gap:10px; margin-bottom: 20px;">
        <img src="https://i.ibb.co/t7xWXXR/logo.png" width="25">
        <span style="font-size:16px; font-weight:700; letter-spacing: 1px;">VENTRY</span>
    </div>
    """, unsafe_allow_html=True)

    if rol_actual in ["Titular", "Familiar"]: opciones_menu = ["Inicio", "Invitados", "Carnet", "Pagos", "Ajustes"]
    elif rol_actual == "Vigilante": opciones_menu = ["Garita", "Ajustes"]
    elif rol_actual == "Administrador": opciones_menu = ["Inicio", "Invitados", "Garita", "Admin", "Ajustes"]

    modulo_seleccionado = st.radio("Nav", opciones_menu, horizontal=True, label_visibility="collapsed")

    if modulo_seleccionado == "Admin": st.markdown("<style>.block-container { max-width: 95% !important; padding-top: 2rem !important; }</style>", unsafe_allow_html=True)
    else: st.markdown("<style>.block-container { max-width: 46rem !important; }</style>", unsafe_allow_html=True)

    # --- MÓDULO 1: INICIO ---
    if modulo_seleccionado == "Inicio":
        st.markdown("""
<div style="text-align: center; margin-top: 20px;">
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

        datos_qr = f"CEDULA:{socio_actual['cedula']}|VENTRY|{socio_actual['nombre']}|{socio_actual['accion']}"
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

    # --- MÓDULO 3: INVITADOS ---
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
            
            if solvencia != "Al dia":
                st.error("❌ Operación Denegada. Debes estar al día con la administración para invitar.")
            else:
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
                        "accion": socio_actual["accion"], "fecha_visita": str_fecha, "cedula_invitado": n_cedula_inv, "nombre_invitado": n_nombre_inv, "fecha_nacimiento": "", "correo": "", "estatus": "Activo"
                    }
                    guardar_bd_invitaciones(BASE_DATOS_INVITACIONES)
                    st.session_state.ultimo_pase_generado = {"id": id_unico, "nombre": n_nombre_inv, "fecha": str_fecha}
                    st.rerun()

    # --- MÓDULO 4: PAGOS (NUEVA ARQUITECTURA DRILL-DOWN) ---
    elif modulo_seleccionado == "Pagos":
        
        if "sub_pagos" not in st.session_state: 
            st.session_state.sub_pagos = "menu"

        solvencia = socio_actual.get('solvencia', 'Desconocido')
        saldo_actual = float(socio_actual.get('saldo', 0.0))
        deuda = 104.00 if solvencia == "Moroso" else 0.00
        
        # VISTA 1: MENÚ PRINCIPAL Y BILLETERA
        if st.session_state.sub_pagos == "menu":
            st.markdown("<h3 style='font-size:22px; font-weight:800; color:#fff; margin-bottom: 20px;'>Billetera Ventry</h3>", unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"""
                <div class="wallet-card">
                    <p class="wallet-title">Saldo a Favor</p>
                    <h3 class="wallet-saldo">${saldo_actual:.2f}</h3>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                st.markdown(f"""
                <div class="wallet-card">
                    <p class="wallet-title">Deuda Actual</p>
                    <h3 class="wallet-deuda">${deuda:.2f}</h3>
                </div>
                """, unsafe_allow_html=True)

            st.write("")
            if st.button("Pagar Cuota Mantenimiento", type="primary"): 
                st.session_state.sub_pagos = "pagar"; st.rerun()
            st.write("")
            if st.button("Recargar Billetera", type="primary"): 
                st.session_state.sub_pagos = "recargar"; st.rerun()

        # VISTA 2: RECARGAR BILLETERA
        elif st.session_state.sub_pagos == "recargar":
            st.markdown("<h3 style='font-size:20px; font-weight:800; color:#FF6600;'>Recargar Billetera</h3>", unsafe_allow_html=True)
            st.write("Deposita dinero en tu cuenta para consumos del club o futuras cuotas.")
            
            with st.form("form_recarga"):
                metodo_r = st.selectbox("Método de Depósito", ["Pago Móvil (Ej. Mercantil, Banesco, etc.)", "Transferencia Nacional", "Zelle", "Efectivo en Taquilla"])
                ref_r = st.text_input("Nº de Referencia (Últimos 6 dígitos)")
                monto_r = st.number_input("Monto a depositar ($)", min_value=1.0)
                st.markdown("<br>", unsafe_allow_html=True)
                btn_recarga = st.form_submit_button("REPORTAR RECARGA")
                
            if btn_recarga and ref_r:
                id_pago = f"REC-{str(uuid.uuid4())[:6].upper()}"
                BASE_DATOS_PAGOS[id_pago] = {
                    "accion": socio_actual["accion"], "metodo": metodo_r, "referencia": ref_r, 
                    "monto": monto_r, "fecha_reporte": datetime.now().strftime("%d/%m/%Y"), 
                    "estatus": "En Revisión", "tipo": "Recarga Billetera"
                }
                guardar_bd_pagos(BASE_DATOS_PAGOS)
                st.success("✅ Depósito reportado. Se sumará a su saldo tras la conciliación.")
            
            st.write("")
            st.markdown("<div class='btn-secundario'>", unsafe_allow_html=True)
            if st.button("← Volver a Billetera", type="primary"): 
                st.session_state.sub_pagos = "menu"; st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        # VISTA 3: PAGAR CUOTA
        elif st.session_state.sub_pagos == "pagar":
            st.markdown("<h3 style='font-size:20px; font-weight:800; color:#FF6600;'>Pago de Mantenimiento</h3>", unsafe_allow_html=True)
            
            if deuda > 0:
                st.warning(f"Tienes un saldo pendiente de **${deuda:.2f}**.")
                
                if saldo_actual >= deuda:
                    st.info("💡 Tienes saldo suficiente en Ventry para cubrir la deuda.")
                    if st.button("Pagar con Saldo Ventry", type="primary"):
                        nuevo_saldo = saldo_actual - deuda
                        BASE_DATOS_SOCIOS[socio_actual['cedula']]['saldo'] = nuevo_saldo
                        BASE_DATOS_SOCIOS[socio_actual['cedula']]['solvencia'] = "Al dia"
                        guardar_bd(BASE_DATOS_SOCIOS)
                        
                        id_pago = f"PAG-{str(uuid.uuid4())[:6].upper()}"
                        BASE_DATOS_PAGOS[id_pago] = {
                            "accion": socio_actual["accion"], "metodo": "Saldo Ventry", "referencia": "PAGO-AUTOMATICO", 
                            "monto": deuda, "fecha_reporte": datetime.now().strftime("%d/%m/%Y"), 
                            "estatus": "Aprobado", "tipo": "Pago de Cuota"
                        }
                        guardar_bd_pagos(BASE_DATOS_PAGOS)
                        st.session_state.usuario_actual['saldo'] = nuevo_saldo
                        st.session_state.usuario_actual['solvencia'] = "Al dia"
                        st.success("✅ Deuda pagada exitosamente. Tu cuenta está al día.")
                        st.rerun()
                
                st.write("O reportar un pago externo:")
                with st.form("form_pago_cuota"):
                    metodo_p = st.selectbox("Vía de pago", ["Zelle", "Pago Móvil (Ej. Mercantil, Banesco, etc.)", "Transferencia Nacional"])
                    ref_p = st.text_input("Nº de Referencia (Últimos 6 dígitos)")
                    monto_p = st.number_input("Monto reportado ($)", min_value=1.0, value=float(deuda))
                    st.markdown("<br>", unsafe_allow_html=True)
                    btn_pago = st.form_submit_button("REPORTAR PAGO DE CUOTA")
                    
                if btn_pago and ref_p:
                    id_pago = f"PAG-{str(uuid.uuid4())[:6].upper()}"
                    BASE_DATOS_PAGOS[id_pago] = {
                        "accion": socio_actual["accion"], "metodo": metodo_p, "referencia": ref_p, 
                        "monto": monto_p, "fecha_reporte": datetime.now().strftime("%d/%m/%Y"), 
                        "estatus": "En Revisión", "tipo": "Pago de Cuota"
                    }
                    guardar_bd_pagos(BASE_DATOS_PAGOS)
                    st.success("✅ Recibo enviado a administración.")
            else:
                st.success("🎉 ¡Estás al día! No tienes deudas pendientes de mantenimiento.")
            
            st.write("")
            st.markdown("<div class='btn-secundario'>", unsafe_allow_html=True)
            if st.button("← Volver a Billetera", type="primary"): 
                st.session_state.sub_pagos = "menu"; st.rerun()
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
                    if pase["estatus"] == "Activo":
                        st.success(f"✅ ACCESO PERMITIDO\\n\\n**Invitado:** {pase['nombre_invitado']}\\n**Acción:** {pase['accion']}")
                        BASE_DATOS_INVITACIONES[id_pase]["estatus"] = "Adentro"
                        guardar_bd_invitaciones(BASE_DATOS_INVITACIONES)
                        registrar_acceso(pase["nombre_invitado"], pase["accion"], "QR Invitado", "Entrada")
                    elif pase["estatus"] == "Adentro": st.warning("⚠️ ALERTA: El invitado ya registró entrada previamente.")
                    else: st.error(f"❌ ACCESO DENEGADO: Pase {pase['estatus']}")
                else: st.error("❌ Pase no encontrado o falsificado.")
            elif "VENTRY" in data_qr:
                try:
                    cedula_qr = data_qr.split("|")[0].split(":")[1]
                    if cedula_qr in BASE_DATOS_SOCIOS:
                        socio_qr = BASE_DATOS_SOCIOS[cedula_qr]
                        solvencia_qr = socio_qr.get("solvencia", "")
                        if solvencia_qr == "Al dia":
                            st.success(f"✅ ACCESO PERMITIDO\\n\\n**Socio:** {socio_qr['nombre']}\\n**Acción:** {socio_qr['accion']}")
                            registrar_acceso(socio_qr["nombre"], socio_qr["accion"], "QR Socio", "Entrada")
                        else: st.error(f"❌ ACCESO DENEGADO\\n\\n**Socio:** {socio_qr['nombre']}\\n**Estatus:** {solvencia_qr.upper()}")
                    else: st.error("❌ Cédula de socio no registrada.")
                except: st.error("❌ Código de carnet ilegible.")
            else: st.error("❌ Código QR no pertenece al sistema Ventry.")

    # --- MÓDULO 5: ADMIN (DASHBOARD RESPONSIVO) ---
    elif modulo_seleccionado == "Admin":
        st.markdown("<h3 style='font-size:24px; font-weight:800; color:#FF6600;'>Consola Administrativa VIP</h3>", unsafe_allow_html=True)
        
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
        capital_riesgo = morosos_count * 104

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
                    tipo_trans = p_info.get("tipo", "Pago de Cuota")
                    with st.expander(f"Acción: {p_info['accion']} | ${p_info['monto']} ({p_info['metodo']}) - {tipo_trans}"):
                        st.write(f"**Ref:** {p_info['referencia']} | **Fecha:** {p_info['fecha_reporte']}")
                        btn_col1, btn_col2 = st.columns(2)
                        with btn_col1:
                            if st.button("✅ Aprobar", key=f"apr_{p_id}"):
                                BASE_DATOS_PAGOS[p_id]["estatus"] = "Aprobado"
                                guardar_bd_pagos(BASE_DATOS_PAGOS)
                                
                                if tipo_trans == "Recarga Billetera":
                                    for ced, info in BASE_DATOS_SOCIOS.items():
                                        if str(info["accion"]) == str(p_info["accion"]) and info["rol"] == "Titular":
                                            BASE_DATOS_SOCIOS[ced]["saldo"] = float(info.get("saldo", 0)) + float(p_info['monto'])
                                elif tipo_trans == "Pago de Cuota":
                                    for ced, info in BASE_DATOS_SOCIOS.items():
                                        if str(info["accion"]) == str(p_info["accion"]): 
                                            BASE_DATOS_SOCIOS[ced]["solvencia"] = "Al dia"
                                guardar_bd(BASE_DATOS_SOCIOS); st.rerun()
                        with btn_col2:
                            if st.button("❌ Rechazar", key=f"rec_{p_id}"): BASE_DATOS_PAGOS[p_id]["estatus"] = "Rechazado"; guardar_bd_pagos(BASE_DATOS_PAGOS); st.rerun()
            else: st.success("No hay pagos ni recargas pendientes de revisión.")

            st.write("")
            st.markdown("<h4 style='font-size:16px; color:#aaa;'>📥 Descargar Data (CSV)</h4>", unsafe_allow_html=True)
            if len(BASE_DATOS_SOCIOS) > 0:
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

        st.write("---")
        if st.button("🔄 Sincronizar DB en la Nube (Google Sheets)"):
            st.session_state.db_socios = cargar_bd(); st.session_state.db_invitaciones = cargar_invitaciones(); st.session_state.db_pagos = cargar_pagos(); st.session_state.db_directorio = cargar_directorio()
            st.success("Base de datos sincronizada.")

    # --- MÓDULO 6: AJUSTES (NAVEGACIÓN "DRILL-DOWN" SIN EMOJIS) ---
    elif modulo_seleccionado == "Ajustes":
        
        if "sub_ajustes" not in st.session_state: 
            st.session_state.sub_ajustes = "menu"

        if st.session_state.sub_ajustes == "menu":
            st.markdown("<h3 style='font-size:22px; font-weight:800; color:#fff; margin-bottom: 20px;'>Ajustes</h3>", unsafe_allow_html=True)
            
            if st.button("Seguridad de Cuenta", type="primary"): 
                st.session_state.sub_ajustes = "perfil"; st.rerun()
            st.write("")
            if st.button("Grupo Familiar", type="primary"): 
                st.session_state.sub_ajustes = "familia"; st.rerun()
            st.write("")
            if st.button("Historial de Accesos", type="primary"): 
                st.session_state.sub_ajustes = "historial"; st.rerun()
            
            st.write("---")
            st.markdown("<div class='btn-peligro'>", unsafe_allow_html=True)
            if st.button("Cerrar Sesión", type="primary"):
                st.session_state.logueado = False
                st.session_state.usuario_actual = None
                st.session_state.pantalla_auth = "login"
                st.session_state.sub_ajustes = "menu"
                st.session_state.sub_pagos = "menu"
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        elif st.session_state.sub_ajustes == "perfil":
            st.markdown("<h3 style='font-size:20px; font-weight:800; color:#FF6600;'>Seguridad de Cuenta</h3>", unsafe_allow_html=True)
            
            with st.form("form_cambio_clave"):
                clave_actual = st.text_input("Contraseña Actual", type="password")
                clave_nueva = st.text_input("Nueva Contraseña", type="password")
                clave_confirma = st.text_input("Confirmar Nueva Contraseña", type="password")
                st.markdown("<br>", unsafe_allow_html=True)
                btn_cambiar_clave = st.form_submit_button("ACTUALIZAR CONTRASEÑA")
                
            if btn_cambiar_clave:
                if clave_actual != str(socio_actual["clave"]):
                    st.error("❌ La contraseña actual es incorrecta.")
                elif clave_nueva != clave_confirma:
                    st.error("❌ Las contraseñas nuevas no coinciden.")
                elif len(clave_nueva) < 4:
                    st.error("⚠️ La contraseña debe tener al menos 4 caracteres.")
                else:
                    BASE_DATOS_SOCIOS[socio_actual["cedula"]]["clave"] = clave_nueva
                    guardar_bd(BASE_DATOS_SOCIOS)
                    st.session_state.usuario_actual["clave"] = clave_nueva
                    st.success("✅ Contraseña actualizada exitosamente.")
            
            st.write("")
            st.markdown("<div class='btn-secundario'>", unsafe_allow_html=True)
            if st.button("← Volver a Ajustes", type="primary"): 
                st.session_state.sub_ajustes = "menu"; st.rerun()
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
                else:
                    st.info("No hay familiares registrados bajo tu acción en este momento.")
            else:
                st.warning("🔒 Esta sección es exclusiva para la cuenta Titular de la Acción.")
                
            st.write("")
            st.markdown("<div class='btn-secundario'>", unsafe_allow_html=True)
            if st.button("← Volver a Ajustes", type="primary"): 
                st.session_state.sub_ajustes = "menu"; st.rerun()
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
            else:
                st.info("No hay registros de acceso recientes para tu acción.")
                
            st.write("")
            st.markdown("<div class='btn-secundario'>", unsafe_allow_html=True)
            if st.button("← Volver a Ajustes", type="primary"): 
                st.session_state.sub_ajustes = "menu"; st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)