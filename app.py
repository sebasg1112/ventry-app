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
  "name": "Ventry Magnum City Club",
  "short_name": "Ventry",
  "theme_color": "#121826",
  "background_color": "#121826",
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
        <meta name="theme-color" content="#121826">
        <link rel="apple-touch-icon" href="{icono_url}">
        <meta name="apple-mobile-web-app-capable" content="yes">
        <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
        <meta name="apple-mobile-web-app-title" content="Ventry">
    </head>
""", unsafe_allow_html=True)

# --- CSS AVANZADO ---
st.markdown("""
    <style>
    /* Ocultamos marca de agua y menú derecho de Streamlit, pero DEJAMOS el header para el menú móvil */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    .stApp { background-color: #f0f2f6; } 
    
    .stButton>button { 
        width: 100%; 
        border-radius: 12px; 
        background-color: #0d1117; 
        color: white; 
        font-weight: bold; 
        border: none; 
        padding: 10px;
    }
    h1, h2, h3 { color: #0d1117; }
    
    .pago-card { 
        background-color: white; 
        padding: 20px; 
        border-radius: 15px; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.05); 
        margin-bottom: 20px; 
    }
    
    /* ESTILOS DEL CARNET GLASSMORPHISM */
    .dark-wrapper { 
        background-color: #121826; 
        padding: 40px 20px; 
        border-radius: 24px; 
        display: flex; 
        justify-content: center; 
        align-items: center; 
        margin-bottom: 30px; 
        box-shadow: inset 0 0 50px rgba(0,0,0,0.5); 
    }
    .glass-card { 
        background: rgba(255, 255, 255, 0.03); 
        backdrop-filter: blur(16px); 
        -webkit-backdrop-filter: blur(16px); 
        border: 1px solid rgba(255, 255, 255, 0.1); 
        border-radius: 20px; 
        padding: 40px 30px; 
        width: 100%; 
        max-width: 360px; 
        color: white; 
        box-shadow: 0 15px 35px rgba(0,0,0,0.4); 
        position: relative; 
        overflow: hidden; 
    }
    .glow-effect { 
        position: absolute; 
        top: -20%; 
        left: -20%; 
        width: 140%; 
        height: 140%; 
        background: radial-gradient(circle at center, rgba(0, 123, 255, 0.15) 0%, transparent 60%); 
        z-index: 0; 
        pointer-events: none; 
    }
    .glass-content { position: relative; z-index: 1; }
    .magnum-logo { text-align: center; margin-bottom: 35px; }
    .logo-m { font-size: 50px; font-weight: 300; margin: 0; line-height: 1; color: #ffffff; }
    .logo-magnum { font-size: 16px; font-weight: 600; letter-spacing: 5px; margin: 5px 0 0 0; color: #ffffff; }
    .logo-city { font-size: 9px; letter-spacing: 2px; color: #8892b0; margin: 0; text-transform: uppercase; }
    .logo-line { width: 30px; height: 1px; background-color: #8892b0; margin: 15px auto 0 auto; }
    
    .info-group { margin-bottom: 18px; border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 8px; }
    .info-label { font-size: 12px; color: #8892b0; margin-bottom: 4px; letter-spacing: 0.5px; }
    .info-value { font-size: 18px; font-weight: 500; color: #e6f1ff; }
    
    .qr-container { text-align: center; margin-top: 30px; }
    .qr-box { background: rgba(255,255,255,0.9); padding: 10px; border-radius: 12px; display: inline-block; margin-bottom: 15px; }
    .qr-box img { width: 140px; display: block; }
    
    .status-badge { display: inline-block; padding: 6px 18px; border-radius: 30px; font-size: 12px; font-weight: bold; letter-spacing: 1px; text-transform: uppercase; }
    .badge-aldia { background: rgba(40, 167, 69, 0.15); color: #4ade80; border: 1px solid rgba(40, 167, 69, 0.3); }
    .badge-moroso { background: rgba(220, 53, 69, 0.15); color: #ff6b6b; border: 1px solid rgba(220, 53, 69, 0.3); }
    .badge-pendiente { background: rgba(255, 193, 7, 0.15); color: #ffc107; border: 1px solid rgba(255, 193, 7, 0.3); }
    
    /* Botón WhatsApp Fricción Cero */
    .whatsapp-btn {
        display: block; 
        width: 100%; 
        text-align: center; 
        background-color: #25D366; 
        color: white;
        padding: 12px; 
        border-radius: 12px; 
        text-decoration: none; 
        font-weight: bold; 
        margin-top: 15px;
        box-shadow: 0 4px 6px rgba(37,211,102,0.3);
    }
    .whatsapp-btn:hover { background-color: #128C7E; color: white; }
    </style>
""", unsafe_allow_html=True)

# --- MOTOR DE BASE DE DATOS (CON CACHÉ) ---
@st.cache_resource
def conectar_google_sheets():
    if "google_credentials" in st.secrets:
        cred_dict = json.loads(st.secrets["google_credentials"])
        gc = gspread.service_account_from_dict(cred_dict)
    else:
        gc = gspread.service_account(filename="credenciales.json")
    
    doc = gc.open("Ventry_BD")
    return (
        doc.worksheet("Socios Magnum City Club"),
        doc.worksheet("Invitaciones"),
        doc.worksheet("Pagos"),
        doc.worksheet("Directorio"),
        doc.worksheet("Historial")
    )

try:
    hoja_bd, hoja_invitaciones, hoja_pagos, hoja_directorio, hoja_historial = conectar_google_sheets()
except Exception as e:
    st.error(f"Error conectando a Google Sheets: {e}")
    st.stop()

# --- FUNCIONES BÁSICAS ---
def calcular_edad(fecha_nac_str):
    if not fecha_nac_str: 
        return "N/A"
    try:
        fecha_nac = datetime.strptime(fecha_nac_str, "%d/%m/%Y").date()
        hoy = datetime.today().date()
        return str(hoy.year - fecha_nac.year - ((hoy.month, hoy.day) < (fecha_nac.month, fecha_nac.day)))
    except:
        try:
            fecha_nac = datetime.strptime(fecha_nac_str, "%Y-%m-%d").date()
            hoy = datetime.today().date()
            return str(hoy.year - fecha_nac.year - ((hoy.month, hoy.day) < (fecha_nac.month, fecha_nac.day)))
        except: 
            return "N/A"

def registrar_acceso(nombre, accion, via, movimiento):
    hora_actual = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    hoja_historial.append_row([hora_actual, str(accion), nombre, via, movimiento])
    st.session_state.historial.insert(0, {
        "nombre": nombre, 
        "accion": accion, 
        "hora": hora_actual, 
        "via": via, 
        "movimiento": movimiento
    })

def cargar_bd():
    registros = hoja_bd.get_all_records()
    datos = {}
    for fila in registros:
        ced = str(fila.get("cedula", ""))
        if ced: 
            datos[ced] = {
                "nombre": str(fila.get("nombre", "")), 
                "clave": str(fila.get("clave", "")), 
                "accion": str(fila.get("accion", "")), 
                "rol": str(fila.get("rol", "")), 
                "parentesco": str(fila.get("parentesco", "N/A")), 
                "fecha_nacimiento": str(fila.get("fecha_nacimiento", "")), 
                "solvencia": str(fila.get("solvencia", "")), 
                "cedula": ced
            }
    return datos

def guardar_bd(datos):
    lista_socios = list(datos.values())
    lista_socios.sort(key=lambda x: (x.get("accion", ""), x.get("rol", "")), reverse=True) 
    filas_a_subir = [["cedula", "nombre", "clave", "accion", "rol", "parentesco", "fecha_nacimiento", "solvencia"]]
    for socio in lista_socios: 
        filas_a_subir.append([
            socio["cedula"], 
            socio["nombre"], 
            socio["clave"], 
            socio["accion"], 
            socio["rol"], 
            socio["parentesco"], 
            socio.get("fecha_nacimiento", ""), 
            socio["solvencia"]
        ])
    hoja_bd.clear()
    hoja_bd.update(values=filas_a_subir, range_name="A1")
    st.session_state.db_socios = datos

def cargar_invitaciones():
    try: 
        return {str(f["id_qr"]): f for f in hoja_invitaciones.get_all_records() if str(f.get("id_qr", ""))}
    except: 
        return {}

def guardar_bd_invitaciones(datos):
    filas = [["id_qr", "accion", "fecha_visita", "cedula_invitado", "nombre_invitado", "fecha_nacimiento", "correo", "estatus"]]
    for k, v in datos.items(): 
        filas.append([
            k, 
            v["accion"], 
            v["fecha_visita"], 
            v["cedula_invitado"], 
            v["nombre_invitado"], 
            v.get("fecha_nacimiento", ""), 
            v.get("correo", ""), 
            v["estatus"]
        ])
    hoja_invitaciones.clear()
    hoja_invitaciones.update(values=filas, range_name="A1")
    st.session_state.db_invitaciones = datos

def cargar_pagos():
    try: 
        registros = hoja_pagos.get_all_records()
        datos = {}
        for f in registros:
            id_p = str(f.get("id_pago", ""))
            if id_p: 
                datos[id_p] = {
                    "accion": str(f.get("accion", "")), 
                    "metodo": str(f.get("metodo", "")), 
                    "referencia": str(f.get("referencia", "")), 
                    "monto": str(f.get("monto", "")), 
                    "fecha_reporte": str(f.get("fecha_reporte", "")), 
                    "estatus": str(f.get("estatus", ""))
                }
        return datos
    except: 
        return {}

def guardar_bd_pagos(datos):
    filas = [["id_pago", "accion", "metodo", "referencia", "monto", "fecha_reporte", "estatus"]]
    for k, v in datos.items(): 
        filas.append([
            k, 
            v["accion"], 
            v["metodo"], 
            v["referencia"], 
            v["monto"], 
            v["fecha_reporte"], 
            v["estatus"]
        ])
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
                if acc not in datos: 
                    datos[acc] = {}
                datos[acc][ced] = {
                    "nombre": str(f.get("nombre_invitado", "")), 
                    "correo": str(f.get("correo", "")), 
                    "fecha_nacimiento": str(f.get("fecha_nacimiento", ""))
                }
        return datos
    except: 
        return {}

def guardar_bd_directorio(datos):
    filas = [["accion", "cedula_invitado", "nombre_invitado", "correo", "fecha_nacimiento"]]
    for acc, invitados in datos.items():
        for ced, info in invitados.items(): 
            filas.append([
                acc, 
                ced, 
                info["nombre"], 
                info["correo"], 
                info.get("fecha_nacimiento", "")
            ])
    hoja_directorio.clear()
    hoja_directorio.update(values=filas, range_name="A1")
    st.session_state.db_directorio = datos

# --- INICIALIZACIÓN DE MEMORIA LOCAL ---
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

if "logueado" not in st.session_state: 
    st.session_state.logueado = False
if "usuario_actual" not in st.session_state: 
    st.session_state.usuario_actual = None
if "historial" not in st.session_state: 
    st.session_state.historial = []
if "ubicacion_socios" not in st.session_state: 
    st.session_state.ubicacion_socios = {} 


# ==========================================
# 🛑 INTERCEPTOR DE PASES DIGITALES (GUEST VIEW)
# ==========================================
# Si un invitado abre el link de WhatsApp, Ventry muestra su pase y no el login.
params = st.query_params
if "pase" in params:
    id_pase_url = params["pase"]
    
    if id_pase_url in BASE_DATOS_INVITACIONES:
        pase = BASE_DATOS_INVITACIONES[id_pase_url]
        
        # Generar QR del pase
        datos_qr = f"INVITADO|{id_pase_url}"
        img = qrcode.make(datos_qr)
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        # Validaciones de estatus visuales
        if pase["estatus"] == "Activo": 
            clase_badge = "badge-aldia"
            texto_badge = "PASE VÁLIDO"
        elif pase["estatus"] == "Adentro": 
            clase_badge = "badge-aldia"
            texto_badge = "EN INSTALACIONES"
        else: 
            clase_badge = "badge-moroso"
            texto_badge = pase["estatus"].upper()
            
        if pase["fecha_visita"] != datetime.now().strftime("%d/%m/%Y") and pase["estatus"] == "Activo":
            clase_badge = "badge-pendiente"
            texto_badge = "FECHA INVÁLIDA"

        # HTML sin indentación para evitar el bug de Streamlit
        st.markdown(f"""
<div class="dark-wrapper" style="margin-top: 50px;">
<div class="glass-card">
<div class="glow-effect"></div>
<div class="glass-content">
<div class="magnum-logo">
<p class="logo-m">M</p>
<p class="logo-magnum">MAGNUM</p>
<p class="logo-city">CITY CLUB</p>
<div class="logo-line"></div>
</div>
<div style="text-align:center; color:#d4af37; font-size:12px; font-weight:bold; letter-spacing:2px; margin-bottom:20px;">
PASE DE INVITADO
</div>
<div class="info-group">
<p class="info-label">Invitado</p>
<p class="info-value">{pase['nombre_invitado']}</p>
</div>
<div class="info-group">
<p class="info-label">Válido para el día</p>
<p class="info-value">{pase['fecha_visita']}</p>
</div>
<div class="info-group">
<p class="info-label">Autorizado por (Acción)</p>
<p class="info-value">{pase['accion']}</p>
</div>
<div class="qr-container">
<div class="qr-box">
<img src="data:image/png;base64,{img_str}">
</div>
<br>
<span class="status-badge {clase_badge}">{texto_badge}</span>
</div>
</div>
</div>
</div>
""", unsafe_allow_html=True)
        
        st.info("💡 Muestra esta pantalla directamente en la garita de seguridad del club.")
    else:
        st.error("❌ Enlace de pase inválido o no encontrado.")
        
    st.stop() # Detiene la ejecución para que no cargue el Login regular


# ==========================================
# PANTALLA INICIAL: LOGIN Y AUTO-REGISTRO
# ==========================================
if not st.session_state.logueado:
    st.title("🔑 VENTRY SYSTEM")
    st.write("---")
    
    tab_login, tab_registro = st.tabs(["🔐 Iniciar Sesión", "📝 Crear Cuenta"])
    
    with tab_login:
        st.subheader("Acceso al Sistema Integrado")
        with st.form("login_form"):
            cedula_ingresada = st.text_input("Usuario / Cédula")
            clave_ingresada = st.text_input("Contraseña", type="password")
            boton_entrar = st.form_submit_button("Iniciar Sesión")

        if boton_entrar:
            if cedula_ingresada in BASE_DATOS_SOCIOS:
                socio = BASE_DATOS_SOCIOS[cedula_ingresada]
                if clave_ingresada == str(socio["clave"]):
                    st.session_state.logueado = True
                    st.session_state.usuario_actual = socio
                    st.rerun()
                else: 
                    st.error("❌ Contraseña incorrecta.")
            else: 
                st.error("⚠️ Usuario no registrado.")

    with tab_registro:
        st.subheader("Solicitud de Nuevo Ingreso")
        st.info("💡 Tu cuenta quedará en estatus **Pendiente** hasta ser validada por la Administración.")
        with st.form("registro_form"):
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
            btn_registrar = st.form_submit_button("Enviar Solicitud")
            
        if btn_registrar:
            if not r_cedula or not r_nombre or not r_accion or not r_clave: 
                st.error("⚠️ Todos los campos son obligatorios.")
            elif r_clave != r_clave_conf: 
                st.error("❌ Las contraseñas no coinciden.")
            elif r_cedula in BASE_DATOS_SOCIOS: 
                st.error("⚠️ Esta cédula ya se encuentra registrada.")
            else:
                r_acc_norm = r_accion.strip().lstrip('0') or "0"
                titular_existente = False
                
                if r_rol == "Titular":
                    for info in BASE_DATOS_SOCIOS.values():
                        if info["accion"] == r_acc_norm and info["rol"] == "Titular":
                            titular_existente = True
                            break
                
                if titular_existente: 
                    st.error(f"⚠️ Operación Denegada: La Acción {r_acc_norm} ya tiene un Titular registrado.")
                else:
                    BASE_DATOS_SOCIOS[r_cedula] = {
                        "nombre": r_nombre, 
                        "clave": r_clave, 
                        "accion": r_acc_norm, 
                        "rol": r_rol, 
                        "parentesco": r_parentesco, 
                        "fecha_nacimiento": r_nacimiento.strftime("%d/%m/%Y"), 
                        "solvencia": "Pendiente", 
                        "cedula": r_cedula
                    }
                    guardar_bd(BASE_DATOS_SOCIOS)
                    st.success("✅ ¡Registro exitoso! Ya puedes iniciar sesión.")

# ==========================================
# SISTEMA INTERNO
# ==========================================
else:
    socio_actual = st.session_state.usuario_actual
    rol_actual = socio_actual["rol"]

    st.sidebar.image("https://i.ibb.co/t7xWXXR/logo.png", width=100)
    st.sidebar.title(f"Hola, {socio_actual['nombre']}")
    st.sidebar.write(f"Rol: **{rol_actual}**")
    
    if rol_actual == "Administrador":
        if st.sidebar.button("🔄 Sincronizar Nube"):
            st.session_state.db_socios = cargar_bd()
            st.session_state.db_invitaciones = cargar_invitaciones()
            st.session_state.db_pagos = cargar_pagos()
            st.session_state.db_directorio = cargar_directorio()
            st.sidebar.success("Base de datos sincronizada")
            st.rerun()
            
    st.sidebar.write("---")
    
    opciones_menu = []
    if rol_actual in ["Titular", "Familiar"]: 
        opciones_menu = ["Mi Carnet Digital", "Módulo de Pagos", "Pases de Invitados"]
    elif rol_actual == "Vigilante": 
        opciones_menu = ["Panel de Garita"]
    elif rol_actual == "Administrador": 
        opciones_menu = ["Portal de Administración", "Panel de Garita", "Módulo de Pagos", "Mi Carnet Digital", "Pases de Invitados"]

    modulo_seleccionado = st.sidebar.radio("Navegación:", opciones_menu)
    
    st.sidebar.write("---")
    if st.sidebar.button("Cerrar Sesión"): 
        st.session_state.logueado = False
        st.session_state.usuario_actual = None
        st.rerun()

    # --- MÓDULO 1: CARNET DIGITAL ---
    if modulo_seleccionado == "Mi Carnet Digital":
        
        if socio_actual['solvencia'] == "Moroso": 
            st.error("⚠️ ATENCIÓN: Tu grupo familiar presenta un saldo pendiente.")
            st.warning("Tu acceso a las instalaciones está restringido. Por favor, regulariza tu estatus en el Módulo de Pagos.")
        elif socio_actual['solvencia'] == "Pendiente": 
            st.warning("⏳ Tu cuenta se encuentra en revisión administrativa. El código QR no será válido hasta ser aprobado.")

        if socio_actual['solvencia'] == "Al dia": 
            clase_badge = "badge-aldia"
            texto_badge = "AL DÍA"
        elif socio_actual['solvencia'] == "Pendiente": 
            clase_badge = "badge-pendiente"
            texto_badge = "PENDIENTE"
        else: 
            clase_badge = "badge-moroso"
            texto_badge = "MOROSO"

        edad_socio = calcular_edad(socio_actual.get('fecha_nacimiento', ''))
        
        datos_qr = f"CEDULA:{socio_actual['cedula']}|VENTRY|{socio_actual['nombre']}|{socio_actual['accion']}"
        img = qrcode.make(datos_qr)
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        img_str = base64.b64encode(buffer.getvalue()).decode()

        # HTML sin indentación para evitar el bug de Streamlit
        carnet_html = f"""
<div class="dark-wrapper">
<div class="glass-card">
<div class="glow-effect"></div>
<div class="glass-content">
<div class="magnum-logo">
<p class="logo-m">M</p>
<p class="logo-magnum">MAGNUM</p>
<p class="logo-city">CITY CLUB</p>
<div class="logo-line"></div>
</div>
<div class="info-group">
<p class="info-label">Nombre</p>
<p class="info-value">{socio_actual['nombre']}</p>
</div>
<div class="info-group">
<p class="info-label">ID (Cédula)</p>
<p class="info-value">{socio_actual['cedula']}</p>
</div>
<div class="info-group">
<p class="info-label">Acción</p>
<p class="info-value">{socio_actual['accion']} <span style="font-size:12px; color:#8892b0; font-weight:normal;">({socio_actual['rol']})</span></p>
</div>
<div class="qr-container">
<div class="qr-box">
<img src="data:image/png;base64,{img_str}">
</div>
<br>
<span class="status-badge {clase_badge}">{texto_badge}</span>
</div>
</div>
</div>
</div>
"""
        st.markdown(carnet_html, unsafe_allow_html=True)
        
        if socio_actual['solvencia'] != "Al dia": 
            st.error("❌ Código Inactivo en Garita.")

    # --- MÓDULO 2: PAGOS ---
    elif modulo_seleccionado == "Módulo de Pagos":
        st.subheader("💸 Depositar Fondos / Pagar Mensualidad")
        st.markdown("<div class='pago-card'>", unsafe_allow_html=True)
        st.markdown(f"#### Acción: {socio_actual['accion']}")
        deuda = 104.00 if socio_actual['solvencia'] == "Moroso" else 0.00
        st.metric("Saldo Pendiente Estimado", f"${deuda:.2f}")
        
        if deuda == 0: 
            st.success("¡Tu grupo familiar se encuentra solvente!")
        st.markdown("</div>", unsafe_allow_html=True)
        
        metodo = st.radio("¿Cómo deseas reportar tu pago?", ["Zelle", "Pago Móvil", "Transferencia Nacional"], horizontal=True)
        st.write("---")
        
        if metodo == "Zelle": 
            st.info("📲 **Datos Zelle:**\n\n**Correo:** pagos@clubmagnum.com\n**Titular:** Inversiones Magnum LLC")
        elif metodo == "Pago Móvil": 
            st.info("📱 **Datos Pago Móvil:**\n\n**Banco:** Bancamiga (0172)\n**RIF:** J-12345678-9\n**Teléfono:** 0414-1234567")
        else: 
            st.info("🏦 **Cuentas Nacionales:**\n\n**Banco:** Banesco\n**Cuenta:** 0134-1234-5678-9012-3456\n**RIF:** J-12345678-9")

        st.markdown("### 📝 Reportar Transacción")
        with st.form("form_pago"):
            n_referencia = st.text_input("Número de Referencia (Últimos 6 dígitos)")
            n_monto = st.number_input("Monto Pagado ($ o Bs según método)", min_value=1.0)
            n_fecha_pago = st.date_input("Fecha de la transacción", max_value=datetime.today(), format="DD/MM/YYYY")
            btn_reportar = st.form_submit_button("Reportar Pago")
            
        if btn_reportar:
            if not n_referencia: 
                st.error("Debes ingresar un número de referencia válido.")
            else:
                id_pago = f"PAG-{str(uuid.uuid4())[:6].upper()}"
                BASE_DATOS_PAGOS[id_pago] = {
                    "accion": socio_actual["accion"], 
                    "metodo": metodo, 
                    "referencia": str(n_referencia), 
                    "monto": str(n_monto), 
                    "fecha_reporte": datetime.now().strftime("%d/%m/%Y %H:%M:%S"), 
                    "estatus": "En Revisión"
                }
                guardar_bd_pagos(BASE_DATOS_PAGOS)
                st.success("✅ Pago reportado con éxito. En breve será validado.")

    # --- MÓDULO 3: PASES DE INVITADOS CON SMART LINKS ---
    elif modulo_seleccionado == "Pases de Invitados":
        st.subheader("🎫 Generar Pase de Invitado")
        
        # Memoria temporal para el link de WhatsApp
        if "ultimo_pase_generado" not in st.session_state:
            st.session_state.ultimo_pase_generado = None

        if socio_actual["solvencia"] != "Al dia":
            st.error("❌ Operación Denegada. Tu grupo familiar no se encuentra solvente.")
        else:
            invitados_previos = BASE_DATOS_DIRECTORIO.get(socio_actual["accion"], {})
            modo_ingreso = st.radio("Seleccione el tipo de registro:", ["Nuevo Invitado", "Directorio de Favoritos"])
            n_cedula_def, n_nombre_def, n_correo_def = "", "", ""
            n_nacimiento_def = datetime.today()
            
            if modo_ingreso == "Directorio de Favoritos":
                if invitados_previos:
                    inv_sel = st.selectbox("Seleccione de su directorio:", list(invitados_previos.keys()), format_func=lambda x: f"{invitados_previos[x]['nombre']} (C.I: {x})")
                    n_cedula_def = inv_sel
                    n_nombre_def = invitados_previos[inv_sel]['nombre']
                    n_correo_def = invitados_previos[inv_sel]['correo']
                    
                    if invitados_previos[inv_sel].get("fecha_nacimiento"):
                        try: 
                            n_nacimiento_def = datetime.strptime(invitados_previos[inv_sel]["fecha_nacimiento"], "%d/%m/%Y").date()
                        except: 
                            pass
                else: 
                    st.info("Aún no tienes invitados guardados en tu directorio.")

            with st.form("form_invitacion"):
                col_a, col_b = st.columns(2)
                with col_a: 
                    n_cedula_inv = st.text_input("Cédula del Invitado", value=n_cedula_def)
                    n_nombre_inv = st.text_input("Nombre del Invitado", value=n_nombre_def)
                with col_b: 
                    n_correo_inv = st.text_input("Correo Electrónico", value=n_correo_def)
                    n_nacimiento_inv = st.date_input("Fecha de Nacimiento", value=n_nacimiento_def, min_value=datetime(1920, 1, 1), max_value=datetime.today(), format="DD/MM/YYYY")
                
                fecha_visita = st.date_input("Fecha de la visita (Válido por todo el día)", min_value=datetime.today(), format="DD/MM/YYYY")
                
                guardar_contacto = False
                if modo_ingreso == "Nuevo Invitado":
                    st.write("---")
                    guardar_contacto = st.checkbox("⭐ Guardar en mi directorio de invitados frecuentes", value=True)
                
                btn_generar = st.form_submit_button("Generar Pase Digital")
                
            if btn_generar:
                if not n_cedula_inv or not n_nombre_inv: 
                    st.error("⚠️ Debes ingresar al menos la Cédula y el Nombre.")
                else:
                    if guardar_contacto:
                        if socio_actual["accion"] not in BASE_DATOS_DIRECTORIO: 
                            BASE_DATOS_DIRECTORIO[socio_actual["accion"]] = {}
                        BASE_DATOS_DIRECTORIO[socio_actual["accion"]][n_cedula_inv] = {
                            "nombre": n_nombre_inv, 
                            "correo": n_correo_inv, 
                            "fecha_nacimiento": n_nacimiento_inv.strftime("%d/%m/%Y")
                        }
                        guardar_bd_directorio(BASE_DATOS_DIRECTORIO)
                    
                    str_fecha = fecha_visita.strftime("%d/%m/%Y")
                    id_unico = f"INV-{socio_actual['accion']}-{str(uuid.uuid4())[:6].upper()}"
                    BASE_DATOS_INVITACIONES[id_unico] = {
                        "accion": socio_actual["accion"], 
                        "fecha_visita": str_fecha, 
                        "cedula_invitado": n_cedula_inv, 
                        "nombre_invitado": n_nombre_inv, 
                        "fecha_nacimiento": n_nacimiento_inv.strftime("%d/%m/%Y"), 
                        "correo": n_correo_inv, 
                        "estatus": "Activo"
                    }
                    guardar_bd_invitaciones(BASE_DATOS_INVITACIONES)
                    
                    # Guardamos el pase en memoria
                    st.session_state.ultimo_pase_generado = {
                        "id": id_unico,
                        "nombre": n_nombre_inv,
                        "fecha": str_fecha
                    }
                    st.success(f"✅ Pase digital generado para {n_nombre_inv}.")
            
            # MOSTRAR EL BOTÓN SI HAY UN PASE RECIÉN GENERADO
            if st.session_state.ultimo_pase_generado:
                pase_temp = st.session_state.ultimo_pase_generado
                
                # IMPORTANTE: CAMBIA ESTA URL SI TU LINK DE STREAMLIT ES DISTINTO
                url_base = "https://ventry.streamlit.app" 
                link_pase_digital = f"{url_base}/?pase={pase_temp['id']}"
                
                st.info("🎟️ **PASE LISTO PARA ENVIAR**")
                
                # Mensaje inteligente para WhatsApp
                mensaje_ws = f"¡Hola {pase_temp['nombre']}! 🏌️‍♂️\n\nAquí tienes tu Pase de Invitado para el *Magnum City Club*.\n\n*Fecha válida:* {pase_temp['fecha']}\n\n👉 *Toca este enlace para abrir tu pase digital y mostrarlo en garita:*\n{link_pase_digital}"
                mensaje_codificado = urllib.parse.quote(mensaje_ws)
                link_ws = f"https://wa.me/?text={mensaje_codificado}"
                
                # Botón directo de WhatsApp
                st.markdown(f'<a href="{link_ws}" target="_blank" class="whatsapp-btn">💬 Enviar Link por WhatsApp</a>', unsafe_allow_html=True)
                st.caption("Esto enviará un enlace seguro. Cuando el invitado lo abra, verá su código QR automáticamente en su celular.")

    # --- MÓDULO 4: GARITA ---
    elif modulo_seleccionado == "Panel de Garita":
        st.title("🛡️ Módulo de Garita (Automático)")
        st.write("---")
        foto_qr = st.camera_input("Apunte el código QR aquí")
        
        if foto_qr is not None:
            bytes_data = foto_qr.getvalue()
            cv2_img = cv2.imdecode(np.frombuffer(bytes_data, np.uint8), cv2.IMREAD_COLOR)
            detector = cv2.QRCodeDetector()
            datos_decodificados, bbox, _ = detector.detectAndDecode(cv2_img)
            
            if datos_decodificados:
                if "CEDULA:" in datos_decodificados:
                    cedula_escaneada = datos_decodificados.split("|")[0].replace("CEDULA:", "")
                    if cedula_escaneada in BASE_DATOS_SOCIOS:
                        socio = BASE_DATOS_SOCIOS[cedula_escaneada]
                        if socio["solvencia"] == "Al dia":
                            estado_actual = st.session_state.ubicacion_socios.get(cedula_escaneada, "Afuera")
                            if estado_actual == "Afuera": 
                                st.success("✅ ENTRADA PERMITIDA (Socio)")
                                st.session_state.ubicacion_socios[cedula_escaneada] = "Adentro"
                                sentido_str = "Entrada"
                            else: 
                                st.success("✅ SALIDA REGISTRADA (Socio)")
                                st.session_state.ubicacion_socios[cedula_escaneada] = "Afuera"
                                sentido_str = "Salida"
                                
                            st.info(f"**Socio:** {socio['nombre']} | **Acción:** {socio['accion']}")
                            registrar_acceso(socio["nombre"], socio["accion"], "QR (Socio)", sentido_str)
                        else: 
                            st.error(f"❌ ACCESO DENEGADO - SOCIO {socio['solvencia'].upper()}")
                    else: 
                        st.error("⚠️ El socio ya no existe en la BD.")
                        
                elif "INVITADO|" in datos_decodificados:
                    id_qr = datos_decodificados.split("|")[1]
                    if id_qr in BASE_DATOS_INVITACIONES:
                        pase = BASE_DATOS_INVITACIONES[id_qr]
                        if pase["estatus"] == "Activo":
                            if datetime.now().strftime("%d/%m/%Y") == pase["fecha_visita"]:
                                socio_solvente = any(str(s["accion"]) == str(pase["accion"]) and s["solvencia"] == "Al dia" for s in BASE_DATOS_SOCIOS.values())
                                if socio_solvente:
                                    st.success(f"✅ ENTRADA PERMITIDA (Invitado: {pase['nombre_invitado']})")
                                    BASE_DATOS_INVITACIONES[id_qr]["estatus"] = "Adentro"
                                    guardar_bd_invitaciones(BASE_DATOS_INVITACIONES)
                                    registrar_acceso(f"Inv: {pase['nombre_invitado']}", pase["accion"], "QR (Invitado)", "Entrada")
                                else: 
                                    st.error("❌ ACCESO DENEGADO - La Acción no está solvente.")
                            else: 
                                st.error("❌ ACCESO DENEGADO - Pase inválido hoy.")
                        elif pase["estatus"] in ["Adentro", "Usado"]: 
                            st.success(f"✅ SALIDA REGISTRADA (Invitado: {pase['nombre_invitado']})")
                            BASE_DATOS_INVITACIONES[id_qr]["estatus"] = "Salió"
                            guardar_bd_invitaciones(BASE_DATOS_INVITACIONES)
                            registrar_acceso(f"Inv: {pase['nombre_invitado']}", pase["accion"], "QR (Invitado)", "Salida")
                        else: 
                            st.error(f"❌ ACCESO DENEGADO - Estatus: {pase['estatus']}.")
                    else: 
                        st.warning("⚠️ Código de invitado no encontrado.")
            else: 
                st.warning("⚠️ No se detectó un código válido.")
        
        st.write("---")
        st.markdown("### 📊 Registro de Tránsito (En Vivo)")
        if st.session_state.historial:
            for acceso in st.session_state.historial[:15]: 
                icono_mov = "🟢" if acceso['movimiento'] == "Entrada" else "🔴"
                st.write(f"{icono_mov} **{acceso['movimiento'].upper()}** - {acceso['nombre']} (Acc. {acceso['accion']}) - {acceso['hora']}")

    # --- MÓDULO 5: ADMINISTRACIÓN ---
    elif modulo_seleccionado == "Portal de Administración":
        st.title("⚙️ Administración General")
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["➕ Nuevo Usuario", "✏️ Editar Perfil", "📝 Gestión Familiar", "💳 Conciliación", "🗃️ Base de Datos", "📈 Analítica"])

        with tab1:
            with st.form("form_nuevo_admin"):
                n_cedula = st.text_input("Usuario / Cédula")
                n_nombre = st.text_input("Nombre")
                n_nacimiento = st.date_input("Fecha de Nacimiento", min_value=datetime(1920, 1, 1), max_value=datetime.today(), format="DD/MM/YYYY")
                n_clave = st.text_input("Contraseña")
                
                col_a, col_b, col_c = st.columns(3)
                with col_a: 
                    n_accion = st.text_input("Acción (0000 para staff)")
                with col_b: 
                    n_rol = st.selectbox("Rol", ["Titular", "Familiar", "Vigilante", "Administrador"])
                with col_c: 
                    n_parentesco = st.selectbox("Parentesco", ["N/A", "Esposo(a)", "Hijo(a)", "Madre/Padre", "Hermano(a)", "Otro"])
                
                n_solvencia = st.selectbox("Estatus", ["Al dia", "Moroso", "Pendiente"])
                
                if st.form_submit_button("Guardar"):
                    if n_cedula and n_nombre:
                        n_acc_norm = n_accion.strip().lstrip('0') or "0"
                        titular_existente = False
                        
                        if n_rol == "Titular":
                            titular_existente = any(info["accion"] == n_acc_norm and info["rol"] == "Titular" for info in BASE_DATOS_SOCIOS.values())
                        
                        if titular_existente: 
                            st.error("⚠️ La Acción ya tiene Titular.")
                        else:
                            BASE_DATOS_SOCIOS[n_cedula] = {
                                "nombre": n_nombre, 
                                "clave": n_clave, 
                                "accion": n_acc_norm, 
                                "rol": n_rol, 
                                "parentesco": n_parentesco, 
                                "fecha_nacimiento": n_nacimiento.strftime("%d/%m/%Y"), 
                                "solvencia": n_solvencia, 
                                "cedula": n_cedula
                            }
                            guardar_bd(BASE_DATOS_SOCIOS)
                            st.success("✅ Guardado.")

        with tab2:
            st.markdown("### ✏️ Modificar Datos")
            opciones_editar = {ced: f"{d['nombre']} (C.I: {ced})" for ced, d in BASE_DATOS_SOCIOS.items()}
            
            if opciones_editar:
                socio_a_editar = st.selectbox("Seleccione el socio:", list(opciones_editar.keys()), format_func=lambda x: opciones_editar[x])
                socio_data = BASE_DATOS_SOCIOS[socio_a_editar]
                e_nac_def = datetime.today()
                
                if socio_data.get("fecha_nacimiento"):
                    try: 
                        e_nac_def = datetime.strptime(socio_data["fecha_nacimiento"], "%d/%m/%Y").date()
                    except: 
                        pass
                
                with st.form("form_editar_admin"):
                    e_nombre = st.text_input("Nombre", value=socio_data["nombre"])
                    e_clave = st.text_input("Contraseña", value=socio_data["clave"])
                    e_nacimiento = st.date_input("Fecha de Nacimiento", value=e_nac_def, min_value=datetime(1920, 1, 1), max_value=datetime.today(), format="DD/MM/YYYY")
                    
                    col_a, col_b, col_c = st.columns(3)
                    with col_a: 
                        e_accion = st.text_input("Acción", value=socio_data["accion"])
                    with col_b: 
                        lista_roles = ["Titular", "Familiar", "Vigilante", "Administrador"]
                        e_rol = st.selectbox("Rol", lista_roles, index=lista_roles.index(socio_data["rol"]) if socio_data["rol"] in lista_roles else 0)
                    with col_c: 
                        lista_parentescos = ["N/A", "Esposo(a)", "Hijo(a)", "Madre/Padre", "Hermano(a)", "Otro"]
                        e_parentesco = st.selectbox("Parentesco", lista_parentescos, index=lista_parentescos.index(socio_data.get("parentesco", "N/A")) if socio_data.get("parentesco", "N/A") in lista_parentescos else 0)
                    
                    lista_estatus = ["Al dia", "Moroso", "Pendiente"]
                    e_solvencia = st.selectbox("Estatus Individual", lista_estatus, index=lista_estatus.index(socio_data["solvencia"]))
                    
                    if st.form_submit_button("Guardar Cambios"):
                        BASE_DATOS_SOCIOS[socio_a_editar] = {
                            "nombre": e_nombre, 
                            "clave": e_clave, 
                            "accion": e_accion.strip().lstrip('0') or "0", 
                            "rol": e_rol, 
                            "parentesco": e_parentesco, 
                            "fecha_nacimiento": e_nacimiento.strftime("%d/%m/%Y"), 
                            "solvencia": e_solvencia, 
                            "cedula": socio_a_editar
                        }
                        guardar_bd(BASE_DATOS_SOCIOS)
                        st.success("✅ Actualizado.")

        with tab3:
            st.markdown("### 🏠 Gestión de Grupos Familiares")
            acciones_disponibles = sorted(list(set(d["accion"] for d in BASE_DATOS_SOCIOS.values())))
            
            if acciones_disponibles:
                accion_sel = st.selectbox("Seleccione Acción:", acciones_disponibles)
                miembros_accion = sorted([info for info in BASE_DATOS_SOCIOS.values() if info["accion"] == accion_sel], key=lambda x: x.get("rol", ""), reverse=True)
                estatus_actual_grupo = miembros_accion[0]["solvencia"] if miembros_accion else "Desconocido"

                st.write("---")
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.markdown(f"#### Acción {accion_sel}")
                    tabla_md = "| Nombre | Rol | Edad | Estatus |\n| :--- | :--- | :--- | :--- |\n"
                    for m in miembros_accion: 
                        icono = '👑' if m['rol'] == 'Titular' else '👤'
                        edad = calcular_edad(m.get('fecha_nacimiento', ''))
                        tabla_md += f"| {icono} {m['nombre']} | {m['rol']} | {edad} | {m['solvencia']} |\n"
                    st.markdown(tabla_md)
                
                with col2:
                    with st.form("form_estatus_admin"):
                        st.write(f"Estatus principal: **{estatus_actual_grupo}**")
                        n_estatus = st.radio("Modificar Estatus a todo el grupo:", ["Al dia", "Moroso", "Pendiente"])
                        
                        if st.form_submit_button("Actualizar Todo"):
                            for ced, info in BASE_DATOS_SOCIOS.items():
                                if info["accion"] == accion_sel: 
                                    BASE_DATOS_SOCIOS[ced]["solvencia"] = n_estatus
                            guardar_bd(BASE_DATOS_SOCIOS)
                            st.success("✅ Grupo familiar actualizado.")

        with tab4:
            st.markdown("### 💳 Conciliación de Pagos")
            pagos_pendientes = {k: v for k, v in BASE_DATOS_PAGOS.items() if v["estatus"] == "En Revisión"}
            
            if pagos_pendientes:
                for p_id, p_info in pagos_pendientes.items():
                    with st.expander(f"Reporte de Acción: {p_info['accion']} | Monto: {p_info['monto']} | Vía: {p_info['metodo']}"):
                        st.write(f"**Referencia:** {p_info['referencia']}")
                        st.write(f"**Fecha reportada:** {p_info['fecha_reporte']}")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("✅ Aprobar Pago & Liberar Acceso", key=f"apr_{p_id}"):
                                BASE_DATOS_PAGOS[p_id]["estatus"] = "Aprobado"
                                guardar_bd_pagos(BASE_DATOS_PAGOS)
                                for ced, info in BASE_DATOS_SOCIOS.items():
                                    if str(info["accion"]) == str(p_info["accion"]): 
                                        BASE_DATOS_SOCIOS[ced]["solvencia"] = "Al dia"
                                guardar_bd(BASE_DATOS_SOCIOS)
                                st.success(f"Pago aprobado. Familia {p_info['accion']} solvente.")
                                st.rerun()
                        with col2:
                            if st.button("❌ Rechazar", key=f"rec_{p_id}"):
                                BASE_DATOS_PAGOS[p_id]["estatus"] = "Rechazado"
                                guardar_bd_pagos(BASE_DATOS_PAGOS)
                                st.warning("Pago rechazado.")
                                st.rerun()
            else: 
                st.info("No hay pagos pendientes por conciliar 🎉")

        with tab5:
            st.write("Base de Datos Maestra:")
            st.json(BASE_DATOS_SOCIOS)

        with tab6:
            st.markdown("### 📊 Radiografía de la Cartera")
            acciones_al_dia, acciones_morosas, acciones_pendientes = set(), set(), set()
            
            for socio in BASE_DATOS_SOCIOS.values():
                if socio["solvencia"] == "Moroso": 
                    acciones_morosas.add(socio["accion"])
                elif socio["solvencia"] == "Pendiente": 
                    acciones_pendientes.add(socio["accion"])
                else: 
                    acciones_al_dia.add(socio["accion"])
                    
            for acc in acciones_morosas:
                acciones_pendientes.discard(acc)
                acciones_al_dia.discard(acc)
            for acc in acciones_pendientes:
                acciones_al_dia.discard(acc)
                
            morosos_count = len(acciones_morosas)
            pendientes_count = len(acciones_pendientes)
            al_dia_count = len(acciones_al_dia)
            total_acciones_unicas = morosos_count + pendientes_count + al_dia_count
            
            if total_acciones_unicas > 0:
                tasa_morosidad = (morosos_count / total_acciones_unicas) * 100
                capital_retenido = morosos_count * 104
                
                col1, col2, col3 = st.columns(3)
                col1.metric("Acciones Totales", total_acciones_unicas)
                col2.metric("Tasa de Morosidad", f"{tasa_morosidad:.1f}%")
                col3.metric("Capital en Riesgo", f"${capital_retenido:,.2f}")
                
                st.write("---")
                df_grafico = pd.DataFrame({
                    "Estatus": ["Al Día", "Moroso", "Pendiente"],
                    "Cantidad": [al_dia_count, morosos_count, pendientes_count],
                    "Color": ["#003366", "#FF4B4B", "#FFA500"]
                })
                st.bar_chart(data=df_grafico, x="Estatus", y="Cantidad", color="Color")
                
                st.write("---")
                st.markdown("#### 📥 Exportar Reportes (CSV)")
                colA, colB = st.columns(2)
                with colA:
                    df_socios = pd.DataFrame(list(BASE_DATOS_SOCIOS.values()))
                    csv_socios = df_socios.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="Descargar Matriz de Socios", 
                        data=csv_socios, 
                        file_name=f"Reporte_Socios_Ventry_{datetime.now().strftime('%Y%m%d')}.csv", 
                        mime="text/csv"
                    )
                with colB:
                    try:
                        historial_data = hoja_historial.get_all_records()
                        if historial_data:
                            df_historial = pd.DataFrame(historial_data)
                            csv_historial = df_historial.to_csv(index=False).encode('utf-8')
                            st.download_button(
                                label="Descargar Auditoría de Garita", 
                                data=csv_historial, 
                                file_name=f"Auditoria_Accesos_{datetime.now().strftime('%Y%m%d')}.csv", 
                                mime="text/csv"
                            )
                        else: 
                            st.info("El historial de garita aún está vacío.")
                    except: 
                        st.info("El historial de garita aún está vacío.")
            else: 
                st.info("Datos insuficientes para generar métricas.")