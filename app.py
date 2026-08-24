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

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Ventry - Control de Acceso", page_icon="🔑", layout="centered")

# --- CSS AVANZADO (AQUÍ ESTÁ LA MAGIA DEL CARNET VIP) ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .main { background-color: #f8f9fa; } 
    .stButton>button { 
        width: 100%; border-radius: 12px; background-color: #003366; color: white; font-weight: bold; border: none; padding: 10px;
    }
    h1, h2, h3 { color: #003366; }
    .pago-card {
        background-color: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 20px;
    }
    
    /* ESTILOS DEL CARNET VIP */
    .carnet-container {
        background: linear-gradient(135deg, #001f3f 0%, #003366 100%);
        padding: 25px;
        border-radius: 20px;
        box-shadow: 0 15px 25px rgba(0,0,0,0.2);
        border: 2px solid #d4af37; /* Borde Dorado */
        text-align: center;
        color: white;
        margin-bottom: 25px;
        position: relative;
        overflow: hidden;
    }
    .carnet-logo {
        font-size: 22px;
        font-weight: 900;
        letter-spacing: 3px;
        color: #d4af37; /* Dorado */
        text-transform: uppercase;
        margin-bottom: 15px;
        border-bottom: 1px solid rgba(212, 175, 55, 0.3);
        padding-bottom: 10px;
    }
    .carnet-nombre {
        font-size: 26px;
        font-weight: bold;
        margin-bottom: 5px;
    }
    .carnet-rol {
        font-size: 14px;
        text-transform: uppercase;
        letter-spacing: 1px;
        color: #a0b8d1;
        margin-bottom: 20px;
    }
    .carnet-datos {
        display: flex;
        justify-content: space-between;
        background: rgba(255, 255, 255, 0.1);
        padding: 15px;
        border-radius: 12px;
        margin-bottom: 20px;
    }
    .dato-item {
        display: flex;
        flex-direction: column;
        align-items: center;
    }
    .dato-label {
        font-size: 11px;
        color: #d4af37;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .dato-valor {
        font-size: 16px;
        font-weight: bold;
    }
    .qr-container {
        background-color: white;
        padding: 15px;
        border-radius: 15px;
        display: inline-block;
        box-shadow: 0 5px 15px rgba(0,0,0,0.3);
    }
    .estatus-badge {
        display: inline-block;
        padding: 5px 15px;
        border-radius: 20px;
        font-weight: bold;
        font-size: 14px;
        margin-top: 15px;
    }
    .badge-aldia { background-color: #28a745; color: white; }
    .badge-moroso { background-color: #dc3545; color: white; }
    .badge-pendiente { background-color: #ffc107; color: black; }
    </style>
""", unsafe_allow_html=True)

# --- MOTOR DE BASE DE DATOS (CONEXIÓN BLINDADA CON CACHÉ) ---
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

# --- FUNCIONES DE CÁLCULO Y AUDITORÍA ---
def calcular_edad(fecha_nac_str):
    if not fecha_nac_str: return "N/A"
    try:
        fecha_nac = datetime.strptime(fecha_nac_str, "%d/%m/%Y").date()
        hoy = datetime.today().date()
        return str(hoy.year - fecha_nac.year - ((hoy.month, hoy.day) < (fecha_nac.month, fecha_nac.day)))
    except:
        try:
            fecha_nac = datetime.strptime(fecha_nac_str, "%Y-%m-%d").date()
            hoy = datetime.today().date()
            return str(hoy.year - fecha_nac.year - ((hoy.month, hoy.day) < (fecha_nac.month, fecha_nac.day)))
        except: return "N/A"

def registrar_acceso(nombre, accion, via, movimiento):
    hora_actual = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    hoja_historial.append_row([hora_actual, str(accion), nombre, via, movimiento])
    st.session_state.historial.insert(0, {"nombre": nombre, "accion": accion, "hora": hora_actual, "via": via, "movimiento": movimiento})

# --- FUNCIONES DE LECTURA/ESCRITURA ---
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
                "solvencia": str(fila.get("solvencia", "")), "cedula": ced
            }
    return datos

def guardar_bd(datos):
    lista_socios = list(datos.values())
    lista_socios.sort(key=lambda x: (x.get("accion", ""), x.get("rol", "")), reverse=True) 
    filas_a_subir = [["cedula", "nombre", "clave", "accion", "rol", "parentesco", "fecha_nacimiento", "solvencia"]]
    for socio in lista_socios:
        filas_a_subir.append([socio["cedula"], socio["nombre"], socio["clave"], socio["accion"], socio["rol"], socio["parentesco"], socio.get("fecha_nacimiento", ""), socio["solvencia"]])
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
            if id_p:
                datos[id_p] = {
                    "accion": str(f.get("accion", "")), "metodo": str(f.get("metodo", "")),
                    "referencia": str(f.get("referencia", "")), "monto": str(f.get("monto", "")),
                    "fecha_reporte": str(f.get("fecha_reporte", "")), "estatus": str(f.get("estatus", ""))
                }
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
                datos[acc][ced] = {
                    "nombre": str(f.get("nombre_invitado", "")), "correo": str(f.get("correo", "")),
                    "fecha_nacimiento": str(f.get("fecha_nacimiento", ""))
                }
        return datos
    except: return {}

def guardar_bd_directorio(datos):
    filas = [["accion", "cedula_invitado", "nombre_invitado", "correo", "fecha_nacimiento"]]
    for acc, invitados in datos.items():
        for ced, info in invitados.items():
            filas.append([acc, ced, info["nombre"], info["correo"], info.get("fecha_nacimiento", "")])
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

if "logueado" not in st.session_state: st.session_state.logueado = False
if "usuario_actual" not in st.session_state: st.session_state.usuario_actual = None
if "historial" not in st.session_state: st.session_state.historial = []
if "ubicacion_socios" not in st.session_state: st.session_state.ubicacion_socios = {} 

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
                else: st.error("❌ Contraseña incorrecta.")
            else: st.error("⚠️ Usuario no registrado.")

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
            if not r_cedula or not r_nombre or not r_accion or not r_clave: st.error("⚠️ Todos los campos son obligatorios.")
            elif r_clave != r_clave_conf: st.error("❌ Las contraseñas no coinciden.")
            elif r_cedula in BASE_DATOS_SOCIOS: st.error("⚠️ Esta cédula ya se encuentra registrada.")
            else:
                r_acc_norm = r_accion.strip().lstrip('0') or "0"
                titular_existente = False
                if r_rol == "Titular":
                    for info in BASE_DATOS_SOCIOS.values():
                        if info["accion"] == r_acc_norm and info["rol"] == "Titular":
                            titular_existente = True
                            break
                if titular_existente: st.error(f"⚠️ Operación Denegada: La Acción {r_acc_norm} ya tiene un Titular registrado.")
                else:
                    BASE_DATOS_SOCIOS[r_cedula] = {
                        "nombre": r_nombre, "clave": r_clave, "accion": r_acc_norm, 
                        "rol": r_rol, "parentesco": r_parentesco, "fecha_nacimiento": r_nacimiento.strftime("%d/%m/%Y"),
                        "solvencia": "Pendiente", "cedula": r_cedula
                    }
                    guardar_bd(BASE_DATOS_SOCIOS)
                    st.success("✅ ¡Registro exitoso! Ya puedes iniciar sesión.")

# ==========================================
# SISTEMA INTERNO
# ==========================================
else:
    socio_actual = st.session_state.usuario_actual
    rol_actual = socio_actual["rol"]

    st.sidebar.image("https://cdn-icons-png.flaticon.com/512/6195/6195699.png", width=100)
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

    # --- MÓDULO 1: CARNET DIGITAL (VIP) ---
    if modulo_seleccionado == "Mi Carnet Digital":
        
        # Alertas de estatus que se muestran arriba del carnet
        if socio_actual['solvencia'] == "Moroso":
            st.error("⚠️ ATENCIÓN: Tu grupo familiar presenta un saldo pendiente.")
            st.warning("Tu acceso a las instalaciones está restringido. Por favor, regulariza tu estatus en el Módulo de Pagos.")
        elif socio_actual['solvencia'] == "Pendiente":
            st.warning("⏳ Tu cuenta se encuentra en revisión administrativa. El código QR no será válido hasta ser aprobado.")

        # Calculo de datos para inyectar en el HTML
        edad_socio = calcular_edad(socio_actual.get('fecha_nacimiento', ''))
        
        # Determinar clase del badge de estatus
        if socio_actual['solvencia'] == "Al dia":
            clase_badge = "badge-aldia"
            texto_badge = "✅ AL DÍA"
        elif socio_actual['solvencia'] == "Pendiente":
            clase_badge = "badge-pendiente"
            texto_badge = "⏳ PENDIENTE"
        else:
            clase_badge = "badge-moroso"
            texto_badge = "❌ MOROSO"

        # Generación de la imagen QR en formato base64 para inyectar en HTML
        datos_qr = f"CEDULA:{socio_actual['cedula']}|VENTRY|{socio_actual['nombre']}|{socio_actual['accion']}"
        img = qrcode.make(datos_qr)
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        img_str = base64.b64encode(buffer.getvalue()).decode()

        # ESTRUCTURA HTML DEL CARNET VIP
        carnet_html = f"""
        <div class="carnet-container">
            <div class="carnet-logo">Magnum City Club</div>
            <div class="carnet-nombre">{socio_actual['nombre']}</div>
            <div class="carnet-rol">{socio_actual['rol']} {socio_actual['parentesco'] if socio_actual['parentesco'] != "N/A (Titular)" else ""}</div>
            
            <div class="carnet-datos">
                <div class="dato-item">
                    <span class="dato-label">Acción</span>
                    <span class="dato-valor">{socio_actual['accion']}</span>
                </div>
                <div class="dato-item">
                    <span class="dato-label">Cédula</span>
                    <span class="dato-valor">{socio_actual['cedula']}</span>
                </div>
                <div class="dato-item">
                    <span class="dato-label">Edad</span>
                    <span class="dato-valor">{edad_socio}</span>
                </div>
            </div>
            
            <div class="qr-container">
                <img src="data:image/png;base64,{img_str}" width="180">
            </div>
            
            <div>
                <span class="estatus-badge {clase_badge}">{texto_badge}</span>
            </div>
        </div>
        """
        
        # Renderizamos el carnet en pantalla
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
        if deuda == 0: st.success("¡Tu grupo familiar se encuentra solvente!")
        st.markdown("</div>", unsafe_allow_html=True)
        
        st.write("¿Cómo deseas reportar tu pago?")
        metodo = st.radio("", ["Zelle", "Pago Móvil", "Transferencia Nacional"], horizontal=True)
        st.write("---")
        if metodo == "Zelle": st.info("📲 **Datos Zelle:**\n\n**Correo:** pagos@clubmagnum.com\n**Titular:** Inversiones Magnum LLC")
        elif metodo == "Pago Móvil": st.info("📱 **Datos Pago Móvil:**\n\n**Banco:** Bancamiga (0172)\n**RIF:** J-12345678-9\n**Teléfono:** 0414-1234567")
        else: st.info("🏦 **Cuentas Nacionales:**\n\n**Banco:** Banesco\n**Cuenta:** 0134-1234-5678-9012-3456\n**RIF:** J-12345678-9")

        st.markdown("### 📝 Reportar Transacción")
        with st.form("form_pago"):
            n_referencia = st.text_input("Número de Referencia (Últimos 6 dígitos)")
            n_monto = st.number_input("Monto Pagado ($ o Bs según método)", min_value=1.0)
            n_fecha_pago = st.date_input("Fecha de la transacción", max_value=datetime.today(), format="DD/MM/YYYY")
            btn_reportar = st.form_submit_button("Reportar Pago")
            
        if btn_reportar:
            if not n_referencia: st.error("Debes ingresar un número de referencia válido.")
            else:
                id_pago = f"PAG-{str(uuid.uuid4())[:6].upper()}"
                BASE_DATOS_PAGOS[id_pago] = {
                    "accion": socio_actual["accion"], "metodo": metodo, "referencia": str(n_referencia),
                    "monto": str(n_monto), "fecha_reporte": datetime.now().strftime("%d/%m/%Y %H:%M:%S"), "estatus": "En Revisión"
                }
                guardar_bd_pagos(BASE_DATOS_PAGOS)
                st.success("✅ Pago reportado con éxito. En breve será validado.")

    # --- MÓDULO 3: PASES DE INVITADOS ---
    elif modulo_seleccionado == "Pases de Invitados":
        st.subheader("🎫 Generar Pase de Invitado")
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
                        try: n_nacimiento_def = datetime.strptime(invitados_previos[inv_sel]["fecha_nacimiento"], "%d/%m/%Y").date()
                        except:
                            try: n_nacimiento_def = datetime.strptime(invitados_previos[inv_sel]["fecha_nacimiento"], "%Y-%m-%d").date()
                            except: pass
                else: st.info("Aún no tienes invitados guardados en tu directorio.")

            with st.form("form_invitacion"):
                col_a, col_b = st.columns(2)
                with col_a:
                    n_cedula_inv = st.text_input("Cédula del Invitado", value=n_cedula_def)
                    n_nombre_inv = st.text_input("Nombre del Invitado", value=n_nombre_def)
                with col_b:
                    n_correo_inv = st.text_input("Correo Electrónico", value=n_correo_def)
                    n_nacimiento_inv = st.date_input("Fecha de Nacimiento", value=n_nacimiento_def, min_value=datetime(1920, 1, 1), max_value=datetime.today(), format="DD/MM/YYYY")
                fecha_visita = st.date_input("Fecha de la visita (Válido por todo el día)", min_value=datetime.today(), format="DD/MM/YYYY")
                st.write("---")
                guardar_contacto = st.checkbox("⭐ Guardar/Actualizar en mi directorio de invitados frecuentes", value=False if modo_ingreso == "Directorio de Favoritos" else True)
                btn_generar = st.form_submit_button("Generar Pase QR")
                
            if btn_generar:
                if not n_cedula_inv or not n_nombre_inv: st.error("⚠️ Debes ingresar al menos la Cédula y el Nombre.")
                else:
                    if guardar_contacto:
                        if socio_actual["accion"] not in BASE_DATOS_DIRECTORIO: BASE_DATOS_DIRECTORIO[socio_actual["accion"]] = {}
                        BASE_DATOS_DIRECTORIO[socio_actual["accion"]][n_cedula_inv] = {
                            "nombre": n_nombre_inv, "correo": n_correo_inv, "fecha_nacimiento": n_nacimiento_inv.strftime("%d/%m/%Y")
                        }
                        guardar_bd_directorio(BASE_DATOS_DIRECTORIO)
                    str_fecha = fecha_visita.strftime("%d/%m/%Y")
                    id_unico = f"INV-{socio_actual['accion']}-{str(uuid.uuid4())[:6].upper()}"
                    BASE_DATOS_INVITACIONES[id_unico] = {
                        "accion": socio_actual["accion"], "fecha_visita": str_fecha,
                        "cedula_invitado": n_cedula_inv, "nombre_invitado": n_nombre_inv,
                        "fecha_nacimiento": n_nacimiento_inv.strftime("%d/%m/%Y"), "correo": n_correo_inv, "estatus": "Activo"
                    }
                    guardar_bd_invitaciones(BASE_DATOS_INVITACIONES)
                    datos_qr = f"INVITADO|{id_unico}"
                    img = qrcode.make(datos_qr)
                    buffer = BytesIO()
                    img.save(buffer, format="PNG")
                    st.success(f"✅ Pase generado para {n_nombre_inv}.")
                    if guardar_contacto: st.info(f"⭐ Datos de {n_nombre_inv} guardados en el directorio.")
                    col_A, col_B, col_C = st.columns([1,2,1])
                    with col_B: st.image(buffer.getvalue(), caption="Comparte este QR con tu invitado", width=250)

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
                                
                            edad_socio = calcular_edad(socio.get("fecha_nacimiento", ""))
                            st.info(f"**Socio:** {socio['nombre']} ({edad_socio} años) | **Acción:** {socio['accion']}")
                            registrar_acceso(socio["nombre"], socio["accion"], "QR (Socio)", sentido_str)
                        else: st.error(f"❌ ACCESO DENEGADO - SOCIO {socio['solvencia'].upper()}")
                    else: st.error("⚠️ El socio ya no existe en la BD.")
                        
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
                                else: st.error("❌ ACCESO DENEGADO - La Acción que emitió este pase no está solvente.")
                            else: st.error("❌ ACCESO DENEGADO - Este pase no es para el día de hoy.")
                        elif pase["estatus"] in ["Adentro", "Usado"]: 
                            st.success(f"✅ SALIDA REGISTRADA (Invitado: {pase['nombre_invitado']})")
                            BASE_DATOS_INVITACIONES[id_qr]["estatus"] = "Salió"
                            guardar_bd_invitaciones(BASE_DATOS_INVITACIONES)
                            registrar_acceso(f"Inv: {pase['nombre_invitado']}", pase["accion"], "QR (Invitado)", "Salida")
                        else: st.error(f"❌ ACCESO DENEGADO - Este QR ya registra el estatus: {pase['estatus']}.")
                    else: st.warning("⚠️ Código de invitado no encontrado.")
            else: st.warning("⚠️ No se detectó un código válido.")
        
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
                with col_a: n_accion = st.text_input("Acción (0000 para staff)")
                with col_b: n_rol = st.selectbox("Rol", ["Titular", "Familiar", "Vigilante", "Administrador"])
                with col_c: n_parentesco = st.selectbox("Parentesco", ["N/A", "Esposo(a)", "Hijo(a)", "Madre/Padre", "Hermano(a)", "Otro"])
                n_solvencia = st.selectbox("Estatus", ["Al dia", "Moroso", "Pendiente"])
                if st.form_submit_button("Guardar"):
                    if n_cedula and n_nombre:
                        n_acc_norm = n_accion.strip().lstrip('0') or "0"
                        titular_existente = False
                        if n_rol == "Titular":
                            for info in BASE_DATOS_SOCIOS.values():
                                if info["accion"] == n_acc_norm and info["rol"] == "Titular":
                                    titular_existente = True
                                    break
                        if titular_existente: st.error(f"⚠️ Operación Denegada: La Acción {n_acc_norm} ya tiene un Titular registrado.")
                        else:
                            BASE_DATOS_SOCIOS[n_cedula] = {
                                "nombre": n_nombre, "clave": n_clave, "accion": n_acc_norm, 
                                "rol": n_rol, "parentesco": n_parentesco, "fecha_nacimiento": n_nacimiento.strftime("%d/%m/%Y"),
                                "solvencia": n_solvencia, "cedula": n_cedula
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
                    try: e_nac_def = datetime.strptime(socio_data["fecha_nacimiento"], "%d/%m/%Y").date()
                    except:
                        try: e_nac_def = datetime.strptime(socio_data["fecha_nacimiento"], "%Y-%m-%d").date()
                        except: pass

                with st.form("form_editar_admin"):
                    e_nombre = st.text_input("Nombre", value=socio_data["nombre"])
                    e_clave = st.text_input("Contraseña", value=socio_data["clave"])
                    e_nacimiento = st.date_input("Fecha de Nacimiento", value=e_nac_def, min_value=datetime(1920, 1, 1), max_value=datetime.today(), format="DD/MM/YYYY")
                    col_a, col_b, col_c = st.columns(3)
                    with col_a: e_accion = st.text_input("Acción", value=socio_data["accion"])
                    with col_b:
                        r_list = ["Titular", "Familiar", "Vigilante", "Administrador"]
                        e_rol = st.selectbox("Rol", r_list, index=r_list.index(socio_data["rol"]) if socio_data["rol"] in r_list else 0)
                    with col_c:
                        p_list = ["N/A", "Esposo(a)", "Hijo(a)", "Madre/Padre", "Hermano(a)", "Otro"]
                        e_parentesco = st.selectbox("Parentesco", p_list, index=p_list.index(socio_data.get("parentesco", "N/A")) if socio_data.get("parentesco", "N/A") in p_list else 0)
                    
                    e_solvencia = st.selectbox("Estatus Individual", ["Al dia", "Moroso", "Pendiente"], index=["Al dia", "Moroso", "Pendiente"].index(socio_data["solvencia"]))
                    if st.form_submit_button("Guardar Cambios"):
                        BASE_DATOS_SOCIOS[socio_a_editar]["nombre"] = e_nombre
                        BASE_DATOS_SOCIOS[socio_a_editar]["clave"] = e_clave
                        BASE_DATOS_SOCIOS[socio_a_editar]["fecha_nacimiento"] = e_nacimiento.strftime("%d/%m/%Y")
                        BASE_DATOS_SOCIOS[socio_a_editar]["accion"] = e_accion.strip().lstrip('0') or "0"
                        BASE_DATOS_SOCIOS[socio_a_editar]["rol"] = e_rol
                        BASE_DATOS_SOCIOS[socio_a_editar]["parentesco"] = e_parentesco
                        BASE_DATOS_SOCIOS[socio_a_editar]["solvencia"] = e_solvencia
                        guardar_bd(BASE_DATOS_SOCIOS)
                        st.success("✅ Actualizado.")

        with tab3:
            st.markdown("### 🏠 Gestión de Grupos Familiares")
            acciones_disponibles = list(set(d["accion"] for d in BASE_DATOS_SOCIOS.values()))
            acciones_disponibles.sort()
            if acciones_disponibles:
                accion_sel = st.selectbox("Seleccione Acción:", acciones_disponibles)
                miembros_accion = [info for info in BASE_DATOS_SOCIOS.values() if info["accion"] == accion_sel]
                miembros_accion.sort(key=lambda x: x.get("rol", ""), reverse=True)
                estatus_actual_grupo = miembros_accion[0]["solvencia"] if miembros_accion else "Desconocido"

                st.write("---")
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.markdown(f"#### Acción {accion_sel}")
                    tabla_md = "| Nombre | Rol | Parentesco | Edad | Estatus |\n| :--- | :--- | :--- | :--- | :--- |\n"
                    for m in miembros_accion:
                        icono = "👑" if m["rol"] == "Titular" else "👤"
                        edad_m = calcular_edad(m.get('fecha_nacimiento', ''))
                        tabla_md += f"| {icono} {m['nombre']} | {m['rol']} | {m.get('parentesco', 'N/A')} | {edad_m} | {m['solvencia']} |\n"
                    st.markdown(tabla_md)
                with col2:
                    with st.form("form_estatus_admin"):
                        st.write(f"Estatus principal: **{estatus_actual_grupo}**")
                        n_estatus = st.radio("Modificar Estatus a todo el grupo:", ["Al dia", "Moroso", "Pendiente"])
                        if st.form_submit_button("Actualizar Todo"):
                            for ced, info in BASE_DATOS_SOCIOS.items():
                                if info["accion"] == accion_sel: BASE_DATOS_SOCIOS[ced]["solvencia"] = n_estatus
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
                                for ced, socio_info in BASE_DATOS_SOCIOS.items():
                                    if str(socio_info["accion"]) == str(p_info["accion"]): BASE_DATOS_SOCIOS[ced]["solvencia"] = "Al dia"
                                guardar_bd(BASE_DATOS_SOCIOS)
                                st.success(f"Pago aprobado. Familia {p_info['accion']} solvente.")
                                st.rerun()
                        with col2:
                            if st.button("❌ Rechazar", key=f"rec_{p_id}"):
                                BASE_DATOS_PAGOS[p_id]["estatus"] = "Rechazado"
                                guardar_bd_pagos(BASE_DATOS_PAGOS)
                                st.warning("Pago rechazado.")
                                st.rerun()
            else: st.info("No hay pagos pendientes por conciliar 🎉")

        with tab5:
            st.write("Base de Datos Maestra:")
            st.json(BASE_DATOS_SOCIOS)

        with tab6:
            st.markdown("### 📊 Radiografía de la Cartera")
            acciones_al_dia, acciones_morosas, acciones_pendientes = set(), set(), set()
            for socio in BASE_DATOS_SOCIOS.values():
                if socio["solvencia"] == "Moroso": acciones_morosas.add(socio["accion"])
                elif socio["solvencia"] == "Pendiente": acciones_pendientes.add(socio["accion"])
                else: acciones_al_dia.add(socio["accion"])
                    
            for acc in acciones_morosas:
                acciones_pendientes.discard(acc)
                acciones_al_dia.discard(acc)
            for acc in acciones_pendientes:
                acciones_al_dia.discard(acc)
                
            morosos_count, pendientes_count, al_dia_count = len(acciones_morosas), len(acciones_pendientes), len(acciones_al_dia)
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
                    st.download_button(label="Descargar Matriz de Socios", data=csv_socios, file_name=f"Reporte_Socios_Ventry_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv")
                with colB:
                    try:
                        historial_data = hoja_historial.get_all_records()
                        if historial_data:
                            df_historial = pd.DataFrame(historial_data)
                            csv_historial = df_historial.to_csv(index=False).encode('utf-8')
                            st.download_button(label="Descargar Auditoría de Garita", data=csv_historial, file_name=f"Auditoria_Accesos_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv")
                        else: st.info("El historial de garita aún está vacío.")
                    except: st.info("El historial de garita aún está vacío.")
            else: st.info("Datos insuficientes.")