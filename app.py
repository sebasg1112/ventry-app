import streamlit as st
from datetime import datetime
import qrcode
from io import BytesIO
import json
import os
import cv2
import numpy as np

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Ventry - Control de Acceso", page_icon="🔑", layout="centered")

st.markdown("""
    <style>
    .main { background-color: #ffffff; }
    .stButton>button { 
        width: 100%; border-radius: 8px; background-color: #003366; color: white; font-weight: bold; border: none;
    }
    h1, h2, h3 { color: #003366; }
    </style>
""", unsafe_allow_html=True)

# --- MOTOR DE BASE DE DATOS (JSON) ---
ARCHIVO_BD = "socios.json"

def cargar_bd():
    if not os.path.exists(ARCHIVO_BD):
        # Agregamos usuarios maestros por defecto para probar los roles
        datos_iniciales = {
            "28472315": {"nombre": "Sebastián Giménez", "clave": "Bowie1234", "accion": "0393", "rol": "Titular", "solvencia": "Al dia", "cedula": "28472315"},
            "admin": {"nombre": "Gerencia Ventry", "clave": "admin123", "accion": "0000", "rol": "Administrador", "solvencia": "Al dia", "cedula": "admin"},
            "garita": {"nombre": "Vigilancia Turno 1", "clave": "seguridad123", "accion": "0000", "rol": "Vigilante", "solvencia": "Al dia", "cedula": "garita"}
        }
        with open(ARCHIVO_BD, "w") as archivo:
            json.dump(datos_iniciales, archivo, indent=4)
            return datos_iniciales
            
    with open(ARCHIVO_BD, "r") as archivo:
        datos = json.load(archivo)
        for cedula, info in datos.items():
            info["cedula"] = cedula
        return datos

def guardar_bd(datos):
    with open(ARCHIVO_BD, "w") as archivo:
        json.dump(datos, archivo, indent=4)

BASE_DATOS_SOCIOS = cargar_bd()

# --- ESTADO DE SESIÓN ---
if "logueado" not in st.session_state:
    st.session_state.logueado = False
if "usuario_actual" not in st.session_state:
    st.session_state.usuario_actual = None
if "historial" not in st.session_state:
    st.session_state.historial = []

url_logo = "AQUÍ_PEGAS_EL_ENLACE_DE_TU_DRIVE"

# ==========================================
# PANTALLA ÚNICA DE LOGIN (Si no está logueado)
# ==========================================
if not st.session_state.logueado:
    try:
        st.image(url_logo, width=150)
    except:
        st.title("🔑 VENTRY SYSTEM")
        
    st.subheader("Acceso al Sistema Integrado")
    st.write("---")
    
    with st.form("login_form"):
        cedula_ingresada = st.text_input("Usuario / Cédula")
        clave_ingresada = st.text_input("Contraseña", type="password")
        boton_entrar = st.form_submit_button("Iniciar Sesión")

    if boton_entrar:
        if cedula_ingresada in BASE_DATOS_SOCIOS:
            socio = BASE_DATOS_SOCIOS[cedula_ingresada]
            if clave_ingresada == socio["clave"]:
                if socio["solvencia"] == "Al dia":
                    st.session_state.logueado = True
                    st.session_state.usuario_actual = socio
                    hora_ingreso = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    # Solo registramos en el historial si es un socio normal entrando a su app
                    if socio["rol"] not in ["Administrador", "Vigilante"]:
                        st.session_state.historial.insert(0, {"nombre": socio["nombre"], "accion": socio["accion"], "hora": hora_ingreso, "via": "App (Login)"})
                    st.rerun()
                else:
                    st.error("❌ ACCESO DENEGADO: Su cuenta se encuentra en estatus [Moroso].")
            else:
                st.error("Contraseña incorrecta.")
        else:
            st.error("Usuario no registrado.")

# ==========================================
# SISTEMA INTERNO (Si YA está logueado)
# ==========================================
else:
    socio_actual = st.session_state.usuario_actual
    rol_actual = socio_actual["rol"]

    # --- CONSTRUCCIÓN DEL MENÚ LATERAL SEGÚN EL ROL ---
    st.sidebar.image("https://cdn-icons-png.flaticon.com/512/6195/6195699.png", width=100)
    st.sidebar.title(f"Hola, {socio_actual['nombre']}")
    st.sidebar.write(f"Rol: **{rol_actual}**")
    st.sidebar.write("---")
    
    opciones_menu = []
    if rol_actual in ["Titular", "Familiar", "Invitado"]:
        opciones_menu = ["Mi Carnet Digital"]
    elif rol_actual == "Vigilante":
        opciones_menu = ["Panel de Garita"]
    elif rol_actual == "Administrador":
        opciones_menu = ["Portal de Administración", "Panel de Garita", "Mi Carnet Digital"]

    modulo_seleccionado = st.sidebar.radio("Navegación:", opciones_menu)
    
    st.sidebar.write("---")
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.logueado = False
        st.session_state.usuario_actual = None
        st.rerun()

    # --- MÓDULO 1: CARNET DIGITAL ---
    if modulo_seleccionado == "Mi Carnet Digital":
        st.subheader("Club Exclusivo Magnum")
        st.markdown("### 🎫 Tu Carnet Digital")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**Acción:** `{socio_actual['accion']}`")
            st.markdown(f"**Estatus:** `{socio_actual['solvencia']} ✅`")
        with col2:
            st.markdown(f"**Cédula:** `{socio_actual['cedula']}`")
            st.markdown("**Vencimiento:** `2 horas`")

        st.write("---")
        datos_qr = f"CEDULA:{socio_actual['cedula']}|VENTRY|{socio_actual['nombre']}|{socio_actual['accion']}"
        img = qrcode.make(datos_qr)
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        
        col_A, col_B, col_C = st.columns([1,2,1])
        with col_B:
            st.image(buffer.getvalue(), caption="Muestre este código en Garita", width=220)

    # --- MÓDULO 2: GARITA ---
    elif modulo_seleccionado == "Panel de Garita":
        st.title("🛡️ Módulo de Garita")
        st.write("---")
        
        foto_qr = st.camera_input("Apunte el código QR aquí")

        if foto_qr is not None:
            bytes_data = foto_qr.getvalue()
            cv2_img = cv2.imdecode(np.frombuffer(bytes_data, np.uint8), cv2.IMREAD_COLOR)
            detector = cv2.QRCodeDetector()
            datos_decodificados, bbox, _ = detector.detectAndDecode(cv2_img)
            
            if datos_decodificados and "CEDULA:" in datos_decodificados:
                cedula_escaneada = datos_decodificados.split("|")[0].replace("CEDULA:", "")
                if cedula_escaneada in BASE_DATOS_SOCIOS:
                    socio = BASE_DATOS_SOCIOS[cedula_escaneada]
                    if socio["solvencia"] == "Al dia":
                        st.success("✅ ACCESO PERMITIDO (QR Detectado)")
                        st.info(f"**Socio:** {socio['nombre']} | **Acción:** {socio['accion']} | **Rol:** {socio['rol']}")
                        st.session_state.historial.insert(0, {"nombre": socio["nombre"], "accion": socio["accion"], "hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "via": "Lector QR"})
                    else:
                        st.error("❌ ACCESO DENEGADO - SOCIO MOROSO (QR Detectado)")
                else:
                    st.error("⚠️ El socio ya no existe en la Base de Datos.")
            else:
                st.warning("⚠️ Código no válido.")
        
        st.write("---")
        st.markdown("### ⌨️ Búsqueda Manual")
        busqueda_cedula = st.text_input("Ingrese Cédula:")
        if st.button("Verificar"):
            if busqueda_cedula in BASE_DATOS_SOCIOS:
                socio = BASE_DATOS_SOCIOS[busqueda_cedula]
                if socio["solvencia"] == "Al dia":
                    st.success("✅ ACCESO PERMITIDO")
                    st.session_state.historial.insert(0, {"nombre": socio["nombre"], "accion": socio["accion"], "hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "via": "Manual"})
                else:
                    st.error("❌ ACCESO DENEGADO - MOROSO")
            else:
                st.error("⚠️ Cédula no encontrada.")

        st.write("---")
        st.markdown("### 📊 Registro de Entradas")
        if st.session_state.historial:
            for acceso in st.session_state.historial:
                st.write(f"🟢 **{acceso['nombre']}** (Acc. {acceso['accion']}) - {acceso['hora']} - {acceso.get('via', '')}")

    # --- MÓDULO 3: ADMINISTRACIÓN ---
    elif modulo_seleccionado == "Portal de Administración":
        st.title("⚙️ Administración General")
        tab1, tab2, tab3 = st.tabs(["➕ Nuevo Usuario", "📝 Estatus", "🗃️ Base de Datos"])

        with tab1:
            with st.form("form_nuevo"):
                n_cedula = st.text_input("Usuario / Cédula")
                n_nombre = st.text_input("Nombre")
                n_clave = st.text_input("Contraseña")
                col_a, col_b = st.columns(2)
                with col_a:
                    n_accion = st.text_input("Acción (0000 para staff)")
                    n_rol = st.selectbox("Rol", ["Titular", "Familiar", "Vigilante", "Administrador"])
                with col_b:
                    n_solvencia = st.selectbox("Estatus", ["Al dia", "Moroso"])

                if st.form_submit_button("Guardar"):
                    if n_cedula and n_nombre and n_clave:
                        BASE_DATOS_SOCIOS[n_cedula] = {"nombre": n_nombre, "clave": n_clave, "accion": n_accion, "rol": n_rol, "solvencia": n_solvencia, "cedula": n_cedula}
                        guardar_bd(BASE_DATOS_SOCIOS)
                        st.success("✅ Registrado.")
                    else:
                        st.error("⚠️ Faltan datos.")

        with tab2:
            opciones_socios = {ced: f"{d['nombre']} - {d['solvencia']}" for ced, d in BASE_DATOS_SOCIOS.items()}
            socio_sel = st.selectbox("Seleccione:", list(opciones_socios.keys()), format_func=lambda x: opciones_socios[x])
            n_estatus = st.radio("Estatus:", ["Al dia", "Moroso"])
            if st.button("Actualizar"):
                BASE_DATOS_SOCIOS[socio_sel]["solvencia"] = n_estatus
                guardar_bd(BASE_DATOS_SOCIOS)
                st.success("✅ Actualizado.")

        with tab3:
            st.json(BASE_DATOS_SOCIOS)