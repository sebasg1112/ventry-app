import streamlit as st
from datetime import datetime, timedelta
import qrcode
from io import BytesIO
import cv2
import numpy as np
import gspread
import json
import pandas as pd
import uuid # Para generar códigos únicos de invitados

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Ventry - Control de Acceso", page_icon="🔑", layout="centered")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .main { background-color: #ffffff; }
    .stButton>button { 
        width: 100%; border-radius: 8px; background-color: #003366; color: white; font-weight: bold; border: none;
    }
    h1, h2, h3 { color: #003366; }
    </style>
""", unsafe_allow_html=True)

# --- MOTOR DE BASE DE DATOS (GOOGLE SHEETS) ---
try:
    if "google_credentials" in st.secrets:
        cred_dict = json.loads(st.secrets["google_credentials"])
        gc = gspread.service_account_from_dict(cred_dict)
    else:
        gc = gspread.service_account(filename="credenciales.json")
        
    hoja_bd = gc.open("Ventry_BD").sheet1
    hoja_invitaciones = gc.open("Ventry_BD").worksheet("Invitaciones") # NUEVA CONEXIÓN
except Exception as e:
    st.error(f"Error conectando a Google Sheets: {e}")
    st.stop()

# --- FUNCIONES DE LECTURA/ESCRITURA (SOCIOS) ---
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
                "solvencia": str(fila.get("solvencia", "")),
                "cedula": ced
            }
    return datos

def guardar_bd(datos):
    lista_socios = list(datos.values())
    lista_socios.sort(key=lambda x: (x.get("accion", ""), x.get("rol", "")), reverse=True) 
    filas_a_subir = [["cedula", "nombre", "clave", "accion", "rol", "parentesco", "solvencia"]]
    for socio in lista_socios:
        filas_a_subir.append([socio["cedula"], socio["nombre"], socio["clave"], socio["accion"], socio["rol"], socio["parentesco"], socio["solvencia"]])
    hoja_bd.clear()
    hoja_bd.update(values=filas_a_subir, range_name="A1")

# --- FUNCIONES DE LECTURA/ESCRITURA (INVITADOS) ---
def cargar_invitaciones():
    try:
        registros = hoja_invitaciones.get_all_records()
    except:
        return {} # Si la hoja está vacía
    
    datos = {}
    for fila in registros:
        id_qr = str(fila.get("id_qr", ""))
        if id_qr:
            datos[id_qr] = {
                "accion": str(fila.get("accion", "")),
                "tipo_pase": str(fila.get("tipo_pase", "")),
                "vencimiento": str(fila.get("vencimiento", "")),
                "estatus": str(fila.get("estatus", ""))
            }
    return datos

def guardar_bd_invitaciones(datos):
    filas_a_subir = [["id_qr", "accion", "tipo_pase", "vencimiento", "estatus"]]
    for id_qr, info in datos.items():
        filas_a_subir.append([id_qr, info["accion"], info["tipo_pase"], info["vencimiento"], info["estatus"]])
    hoja_invitaciones.clear()
    hoja_invitaciones.update(values=filas_a_subir, range_name="A1")

BASE_DATOS_SOCIOS = cargar_bd()
BASE_DATOS_INVITACIONES = cargar_invitaciones()

# --- ESTADO DE SESIÓN ---
if "logueado" not in st.session_state:
    st.session_state.logueado = False
if "usuario_actual" not in st.session_state:
    st.session_state.usuario_actual = None
if "historial" not in st.session_state:
    st.session_state.historial = []

# ==========================================
# PANTALLA ÚNICA DE LOGIN
# ==========================================
if not st.session_state.logueado:
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
    
    # --- MENÚ ACTUALIZADO ---
    opciones_menu = []
    if rol_actual in ["Titular", "Familiar"]:
        opciones_menu = ["Mi Carnet Digital", "Pases de Invitados"]
    elif rol_actual == "Vigilante":
        opciones_menu = ["Panel de Garita"]
    elif rol_actual == "Administrador":
        opciones_menu = ["Portal de Administración", "Panel de Garita", "Mi Carnet Digital", "Pases de Invitados"]

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
        st.write("---")
        datos_qr = f"CEDULA:{socio_actual['cedula']}|VENTRY|{socio_actual['nombre']}|{socio_actual['accion']}"
        img = qrcode.make(datos_qr)
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        col_A, col_B, col_C = st.columns([1,2,1])
        with col_B:
            st.image(buffer.getvalue(), caption="Muestre este código en Garita", width=220)

    # --- MÓDULO 2: PASES DE INVITADOS ---
    elif modulo_seleccionado == "Pases de Invitados":
        st.subheader("🎫 Generar Pase Temporal")
        st.write("Crea un código QR de un solo uso para tus invitados.")
        
        col1, col2 = st.columns(2)
        with col1:
            btn_1h = st.button("Pase de 1 Hora")
        with col2:
            btn_24h = st.button("Pase de 24 Horas")
            
        if btn_1h or btn_24h:
            # Validamos nuevamente que el socio esté solvente por seguridad
            if socio_actual["solvencia"] != "Al dia":
                st.error("❌ Operación Denegada. Tu grupo familiar presenta morosidad.")
            else:
                tipo = "1 Hora" if btn_1h else "24 Horas"
                horas_sumar = 1 if btn_1h else 24
                
                # Generamos un ID encriptado único (Ej. INV-393-A4B7D2)
                id_unico = f"INV-{socio_actual['accion']}-{str(uuid.uuid4())[:6].upper()}"
                
                # Calculamos matemáticamente la fecha de caducidad
                ahora = datetime.now()
                vence = ahora + timedelta(hours=horas_sumar)
                str_vence = vence.strftime("%Y-%m-%d %H:%M:%S")
                
                # Guardamos en la nueva pestaña de Google Sheets
                BASE_DATOS_INVITACIONES[id_unico] = {
                    "accion": socio_actual["accion"],
                    "tipo_pase": tipo,
                    "vencimiento": str_vence,
                    "estatus": "Activo"
                }
                guardar_bd_invitaciones(BASE_DATOS_INVITACIONES)
                
                # Inyectamos el ID en el QR
                datos_qr = f"INVITADO|{id_unico}"
                img = qrcode.make(datos_qr)
                buffer = BytesIO()
                img.save(buffer, format="PNG")
                
                st.success(f"✅ Pase generado con éxito. Válido hasta: {str_vence}")
                col_A, col_B, col_C = st.columns([1,2,1])
                with col_B:
                    st.image(buffer.getvalue(), caption="Comparte este QR con tu invitado", width=250)

    # --- MÓDULO 3: GARITA ---
    elif modulo_seleccionado == "Panel de Garita":
        st.title("🛡️ Módulo de Garita")
        st.write("---")
        foto_qr = st.camera_input("Apunte el código QR aquí")
        if foto_qr is not None:
            bytes_data = foto_qr.getvalue()
            cv2_img = cv2.imdecode(np.frombuffer(bytes_data, np.uint8), cv2.IMREAD_COLOR)
            detector = cv2.QRCodeDetector()
            datos_decodificados, bbox, _ = detector.detectAndDecode(cv2_img)
            
            if datos_decodificados:
                # 1. LECTURA DE SOCIO
                if "CEDULA:" in datos_decodificados:
                    cedula_escaneada = datos_decodificados.split("|")[0].replace("CEDULA:", "")
                    if cedula_escaneada in BASE_DATOS_SOCIOS:
                        socio = BASE_DATOS_SOCIOS[cedula_escaneada]
                        if socio["solvencia"] == "Al dia":
                            st.success("✅ ACCESO PERMITIDO (Socio)")
                            st.info(f"**Socio:** {socio['nombre']} | **Acción:** {socio['accion']} | **Rol:** {socio['rol']}")
                            st.session_state.historial.insert(0, {"nombre": socio["nombre"], "accion": socio["accion"], "hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "via": "QR (Socio)"})
                        else:
                            st.error("❌ ACCESO DENEGADO - SOCIO MOROSO")
                    else:
                        st.error("⚠️ El socio ya no existe en la Base de Datos.")
                
                # 2. LECTURA DE INVITADO
                elif "INVITADO|" in datos_decodificados:
                    id_qr = datos_decodificados.split("|")[1]
                    if id_qr in BASE_DATOS_INVITACIONES:
                        pase = BASE_DATOS_INVITACIONES[id_qr]
                        
                        if pase["estatus"] == "Activo":
                            vencimiento_dt = datetime.strptime(pase["vencimiento"], "%Y-%m-%d %H:%M:%S")
                            # Validar el tiempo
                            if datetime.now() <= vencimiento_dt:
                                # Validar que la acción que invita siga solvente
                                accion_invita = pase["accion"]
                                socio_solvente = any(s["accion"] == accion_invita and s["solvencia"] == "Al dia" for s in BASE_DATOS_SOCIOS.values())
                                
                                if socio_solvente:
                                    st.success(f"✅ ACCESO PERMITIDO (Invitado - {pase['tipo_pase']})")
                                    st.info(f"Autorizado por la Acción: {accion_invita}")
                                    
                                    # Quemar el pase para que no se use dos veces
                                    BASE_DATOS_INVITACIONES[id_qr]["estatus"] = "Usado"
                                    guardar_bd_invitaciones(BASE_DATOS_INVITACIONES)
                                    
                                    st.session_state.historial.insert(0, {"nombre": "Invitado Temporal", "accion": accion_invita, "hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "via": "QR (Invitado)"})
                                else:
                                    st.error("❌ ACCESO DENEGADO - La Acción que emitió este pase se encuentra Morosa.")
                            else:
                                st.error("❌ ACCESO DENEGADO - Este pase ha caducado.")
                                BASE_DATOS_INVITACIONES[id_qr]["estatus"] = "Vencido"
                                guardar_bd_invitaciones(BASE_DATOS_INVITACIONES)
                        else:
                            st.error(f"❌ ACCESO DENEGADO - Este código QR ya se encuentra {pase['estatus']}.")
                    else:
                        st.warning("⚠️ Código de invitado no encontrado o adulterado.")
            else:
                st.warning("⚠️ No se detectó un código válido.")
        
        st.write("---")
        st.markdown("### 📊 Registro de Entradas (Local)")
        if st.session_state.historial:
            for acceso in st.session_state.historial:
                st.write(f"🟢 **{acceso['nombre']}** (Acc. {acceso['accion']}) - {acceso['hora']} - {acceso.get('via', '')}")

    # --- MÓDULO 4: ADMINISTRACIÓN (Se mantiene exacto a la versión anterior) ---
    elif modulo_seleccionado == "Portal de Administración":
        st.title("⚙️ Administración General")
        
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["➕ Nuevo Usuario", "✏️ Editar Perfil", "📝 Gestión Familiar", "🗃️ Base de Datos", "📈 Analítica"])

        with tab1:
            with st.form("form_nuevo"):
                n_cedula = st.text_input("Usuario / Cédula")
                n_nombre = st.text_input("Nombre")
                n_clave = st.text_input("Contraseña")
                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    n_accion = st.text_input("Acción (0000 para staff)")
                with col_b:
                    n_rol = st.selectbox("Rol", ["Titular", "Familiar", "Vigilante", "Administrador"])
                with col_c:
                    n_parentesco = st.selectbox("Parentesco", ["N/A (Titular/Staff)", "Esposo(a)", "Hijo(a)", "Madre/Padre", "Hermano(a)", "Otro"])
                
                n_solvencia = st.selectbox("Estatus", ["Al dia", "Moroso"])

                if st.form_submit_button("Guardar Nuevo"):
                    if n_cedula and n_nombre and n_clave:
                        titular_existente = False
                        if n_rol == "Titular":
                            for info in BASE_DATOS_SOCIOS.values():
                                if info["accion"] == n_accion and info["rol"] == "Titular":
                                    titular_existente = True
                                    break
                        if titular_existente:
                            st.error(f"⚠️ Operación denegada: La Acción {n_accion} ya tiene un Titular registrado.")
                        else:
                            BASE_DATOS_SOCIOS[n_cedula] = {"nombre": n_nombre, "clave": n_clave, "accion": n_accion, "rol": n_rol, "parentesco": n_parentesco, "solvencia": n_solvencia, "cedula": n_cedula}
                            guardar_bd(BASE_DATOS_SOCIOS)
                            st.success("✅ Registrado.")
                    else:
                        st.error("⚠️ Faltan datos.")

        with tab2:
            st.markdown("### ✏️ Modificar Datos")
            opciones_editar = {ced: f"{d['nombre']} (C.I: {ced})" for ced, d in BASE_DATOS_SOCIOS.items()}
            if opciones_editar:
                socio_a_editar = st.selectbox("Seleccione el socio:", list(opciones_editar.keys()), format_func=lambda x: opciones_editar[x])
                socio_data = BASE_DATOS_SOCIOS[socio_a_editar]
                
                with st.form("form_editar"):
                    e_nombre = st.text_input("Nombre", value=socio_data["nombre"])
                    e_clave = st.text_input("Contraseña", value=socio_data["clave"])
                    col_a, col_b, col_c = st.columns(3)
                    with col_a:
                        e_accion = st.text_input("Acción", value=socio_data["accion"])
                    with col_b:
                        roles_lista = ["Titular", "Familiar", "Vigilante", "Administrador"]
                        idx_rol = roles_lista.index(socio_data["rol"]) if socio_data["rol"] in roles_lista else 0
                        e_rol = st.selectbox("Rol", roles_lista, index=idx_rol)
                    with col_c:
                        parentesco_lista = ["N/A (Titular/Staff)", "Esposo(a)", "Hijo(a)", "Madre/Padre", "Hermano(a)", "Otro"]
                        parentesco_actual = socio_data.get("parentesco", "N/A (Titular/Staff)")
                        idx_par = parentesco_lista.index(parentesco_actual) if parentesco_actual in parentesco_lista else 0
                        e_parentesco = st.selectbox("Parentesco", parentesco_lista, index=idx_par)
                    
                    if st.form_submit_button("Guardar Cambios"):
                        BASE_DATOS_SOCIOS[socio_a_editar]["nombre"] = e_nombre
                        BASE_DATOS_SOCIOS[socio_a_editar]["clave"] = e_clave
                        BASE_DATOS_SOCIOS[socio_a_editar]["accion"] = e_accion
                        BASE_DATOS_SOCIOS[socio_a_editar]["rol"] = e_rol
                        BASE_DATOS_SOCIOS[socio_a_editar]["parentesco"] = e_parentesco
                        guardar_bd(BASE_DATOS_SOCIOS)
                        st.success("✅ Perfil actualizado.")
            else:
                st.info("No hay usuarios.")

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
                    tabla_md = "| Nombre | Rol | Parentesco | Estatus |\n| :--- | :--- | :--- | :--- |\n"
                    for m in miembros_accion:
                        icono = "👑" if m["rol"] == "Titular" else "👤"
                        tabla_md += f"| {icono} {m['nombre']} | {m['rol']} | {m.get('parentesco', 'N/A')} | {m['solvencia']} |\n"
                    st.markdown(tabla_md)
                with col2:
                    with st.form("form_estatus"):
                        st.write(f"Estatus actual: **{estatus_actual_grupo}**")
                        n_estatus = st.radio("Modificar Estatus:", ["Al dia", "Moroso"])
                        if st.form_submit_button("Actualizar Todo"):
                            for ced, info in BASE_DATOS_SOCIOS.items():
                                if info["accion"] == accion_sel:
                                    BASE_DATOS_SOCIOS[ced]["solvencia"] = n_estatus
                            guardar_bd(BASE_DATOS_SOCIOS)
                            st.success("✅ Actualizado.")
            else:
                st.info("No hay acciones.")

        with tab4:
            st.write("Datos de tu archivo Ventry_BD (Socios):")
            st.json(BASE_DATOS_SOCIOS)

        with tab5:
            st.markdown("### 📊 Radiografía de la Cartera")
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
                capital_retenido = morosos_count * 104
                col1, col2, col3 = st.columns(3)
                col1.metric("Acciones Totales", total_acciones_unicas)
                col2.metric("Tasa de Morosidad", f"{tasa_morosidad:.1f}%")
                col3.metric("Capital en Riesgo", f"${capital_retenido:,.2f}")
                st.write("---")
                df_grafico = pd.DataFrame({
                    "Estatus": ["Al Día", "Moroso"],
                    "Cantidad": [al_dia_count, morosos_count],
                    "Color": ["#003366", "#FF4B4B"]
                })
                st.bar_chart(data=df_grafico, x="Estatus", y="Cantidad", color="Color")
            else:
                st.info("Datos insuficientes.")