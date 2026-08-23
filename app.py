import streamlit as st
from datetime import datetime
import qrcode
from io import BytesIO
import cv2
import numpy as np
import gspread
import json
import pandas as pd

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Ventry - Control de Acceso", page_icon="🔑", layout="centered")

st.markdown("""
    <style>
    /* Ocultar menú superior, pie de página y botón de GitHub de Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Tu diseño corporativo original */
    .main { background-color: #ffffff; }
    .stButton>button { 
        width: 100%; border-radius: 8px; background-color: #003366; color: white; font-weight: bold; border: none;
    }
    h1, h2, h3 { color: #003366; }
    </style>
""", unsafe_allow_html=True)

# --- MOTOR DE BASE DE DATOS (GOOGLE SHEETS) ---
try:
    # Verificamos si estamos en la nube de Streamlit
    if "google_credentials" in st.secrets:
        cred_dict = json.loads(st.secrets["google_credentials"])
        gc = gspread.service_account_from_dict(cred_dict)
    # Si no estamos en la nube, usamos el archivo local
    else:
        gc = gspread.service_account(filename="credenciales.json")
        
    hoja_bd = gc.open("Ventry_BD").sheet1
except Exception as e:
    st.error(f"Error conectando a Google Sheets: {e}")
    st.stop()

def cargar_bd():
    """Descarga los datos de Google Sheets y los convierte al formato de la app"""
    registros = hoja_bd.get_all_records()
    datos = {}
    for fila in registros:
        ced = str(fila["cedula"])
        datos[ced] = {
            "nombre": str(fila["nombre"]),
            "clave": str(fila["clave"]),
            "accion": str(fila["accion"]),
            "rol": str(fila["rol"]),
            "solvencia": str(fila["solvencia"]),
            "cedula": ced
        }
    return datos

def guardar_bd(datos):
    """Sube los datos actualizados a Google Sheets"""
    filas_a_subir = [["cedula", "nombre", "clave", "accion", "rol", "solvencia"]]
    for ced, info in datos.items():
        filas_a_subir.append([ced, info["nombre"], info["clave"], info["accion"], info["rol"], info["solvencia"]])
    
    hoja_bd.clear()
    hoja_bd.update(values=filas_a_subir, range_name="A1")

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
# PANTALLA ÚNICA DE LOGIN
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
            if clave_ingresada == str(socio["clave"]):
                if socio["solvencia"] == "Al dia":
                    st.session_state.logueado = True
                    st.session_state.usuario_actual = socio
                    hora_ingreso = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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
# SISTEMA INTERNO
# ==========================================
else:
    socio_actual = st.session_state.usuario_actual
    rol_actual = socio_actual["rol"]

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
        
        tab1, tab2, tab3, tab4 = st.tabs(["➕ Nuevo Usuario", "📝 Estatus", "🗃️ Base de Datos en Vivo", "📈 Analítica Financiera"])

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
                        st.success("✅ Registrado en Google Sheets.")
                    else:
                        st.error("⚠️ Faltan datos.")

        with tab2:
            opciones_socios = {ced: f"{d['nombre']} (Acción: {d['accion']}) - {d['solvencia']}" for ced, d in BASE_DATOS_SOCIOS.items()}
            socio_sel = st.selectbox("Seleccione un Socio para ubicar su Acción:", list(opciones_socios.keys()), format_func=lambda x: opciones_socios[x])
            
            n_estatus = st.radio("Nuevo Estatus (Aplica a todo el grupo familiar):", ["Al dia", "Moroso"])
            
            if st.button("Actualizar Estatus"):
                accion_afectada = BASE_DATOS_SOCIOS[socio_sel]["accion"]
                
                # Magia: Buscamos a todos los que compartan la acción y los actualizamos juntos
                for ced, info in BASE_DATOS_SOCIOS.items():
                    if info["accion"] == accion_afectada:
                        BASE_DATOS_SOCIOS[ced]["solvencia"] = n_estatus
                        
                guardar_bd(BASE_DATOS_SOCIOS)
                st.success(f"✅ Se actualizó el estatus a '{n_estatus}' para todos los miembros de la Acción {accion_afectada}.")

        with tab3:
            st.write("Estos datos vienen directamente de tu archivo Ventry_BD:")
            st.json(BASE_DATOS_SOCIOS)

        with tab4:
            st.markdown("### 📊 Radiografía de la Cartera (Por Acciones)")
            
            # --- CORRECCIÓN LÓGICA: Contar Acciones únicas, no personas ---
            acciones_totales = set()
            acciones_morosas = set()
            
            for socio in BASE_DATOS_SOCIOS.values():
                acciones_totales.add(socio["accion"])
                if socio["solvencia"] == "Moroso":
                    acciones_morosas.add(socio["accion"])
            
            total_acciones_unicas = len(acciones_totales)
            
            if total_acciones_unicas > 0:
                morosos_count = len(acciones_morosas)
                al_dia_count = total_acciones_unicas - morosos_count
                tasa_morosidad = (morosos_count / total_acciones_unicas) * 100
                
                # Proyección financiera real (1 Cuota por Acción, no por familiar)
                capital_retenido = morosos_count * 104
                
                col1, col2, col3 = st.columns(3)
                col1.metric("Acciones Totales", total_acciones_unicas)
                col2.metric("Tasa de Morosidad", f"{tasa_morosidad:.1f}%")
                col3.metric("Capital en Riesgo", f"${capital_retenido:,.2f}")
                
                st.write("---")
                
                st.markdown("#### Distribución de Estatus")
                # Creamos la tabla de datos incluyendo el color exacto para cada barra
                df_grafico = pd.DataFrame({
                    "Estatus": ["Al Día", "Moroso"],
                    "Cantidad": [al_dia_count, morosos_count],
                    "Color": ["#003366", "#FF4B4B"] # Azul corporativo y Rojo alerta
                })
                
                st.bar_chart(data=df_grafico, x="Estatus", y="Cantidad", color="Color")
                
            else:
                st.info("No hay datos suficientes para generar analíticas.")