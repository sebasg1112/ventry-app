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
    hoja_invitaciones = gc.open("Ventry_BD").worksheet("Invitaciones")
except Exception as e:
    st.error(f"Error conectando a Google Sheets: {e}")
    st.stop()

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

def cargar_invitaciones():
    try:
        registros = hoja_invitaciones.get_all_records()
    except:
        return {}
    datos = {}
    for fila in registros:
        id_qr = str(fila.get("id_qr", ""))
        if id_qr:
            datos[id_qr] = {
                "accion": str(fila.get("accion", "")),
                "fecha_visita": str(fila.get("fecha_visita", "")),
                "cedula_invitado": str(fila.get("cedula_invitado", "")),
                "nombre_invitado": str(fila.get("nombre_invitado", "")),
                "fecha_nacimiento": str(fila.get("fecha_nacimiento", "")),
                "correo": str(fila.get("correo", "")),
                "estatus": str(fila.get("estatus", ""))
            }
    return datos

def guardar_bd_invitaciones(datos):
    filas_a_subir = [["id_qr", "accion", "fecha_visita", "cedula_invitado", "nombre_invitado", "fecha_nacimiento", "correo", "estatus"]]
    for id_qr, info in datos.items():
        filas_a_subir.append([id_qr, info["accion"], info["fecha_visita"], info["cedula_invitado"], info["nombre_invitado"], info.get("fecha_nacimiento", ""), info.get("correo", ""), info["estatus"]])
    hoja_invitaciones.clear()
    hoja_invitaciones.update(values=filas_a_subir, range_name="A1")

BASE_DATOS_SOCIOS = cargar_bd()
BASE_DATOS_INVITACIONES = cargar_invitaciones()

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
                # ¡NUEVA LÓGICA! Dejamos entrar a todos, sin importar la solvencia.
                st.session_state.logueado = True
                st.session_state.usuario_actual = socio
                
                # Solo registramos el log de entrada a la app si están al día (opcional)
                if socio["solvencia"] == "Al dia" and socio["rol"] not in ["Administrador", "Vigilante"]:
                    st.session_state.historial.insert(0, {"nombre": socio["nombre"], "accion": socio["accion"], "hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "via": "App (Login)"})
                st.rerun()
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
        
        # Si está moroso, le mostramos una alerta gigante
        if socio_actual['solvencia'] != "Al dia":
            st.error("⚠️ ATENCIÓN: Tu grupo familiar presenta un saldo pendiente.")
            st.warning("Tu acceso a las instalaciones se encuentra temporalmente restringido. Por favor, regulariza tu estatus en el módulo de pagos (Próximamente).")
            
        st.markdown("### 🎫 Tu Carnet Digital")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**Acción:** `{socio_actual['accion']}`")
            # Cambia el color del texto dependiendo de la solvencia
            estatus_color = "✅ Al dia" if socio_actual['solvencia'] == "Al dia" else "❌ MOROSO"
            st.markdown(f"**Estatus:** `{estatus_color}`")
        with col2:
            st.markdown(f"**Cédula:** `{socio_actual['cedula']}`")
        st.write("---")
        
        datos_qr = f"CEDULA:{socio_actual['cedula']}|VENTRY|{socio_actual['nombre']}|{socio_actual['accion']}"
        img = qrcode.make(datos_qr)
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        
        col_A, col_B, col_C = st.columns([1,2,1])
        with col_B:
            # Si está moroso, mostramos el QR pero le advertimos que no funcionará
            st.image(buffer.getvalue(), caption="Muestre este código en Garita", width=220)
            if socio_actual['solvencia'] != "Al dia":
                st.error("❌ Este código será rechazado en la garita.")

    # --- MÓDULO 2: PASES DE INVITADOS ---
    elif modulo_seleccionado == "Pases de Invitados":
        st.subheader("🎫 Generar Pase de Invitado")
        st.write("Crea un código QR válido por un día completo para tu invitado.")
        
        # Buscar invitados anteriores del mismo socio y guardar sus datos extra
        invitados_previos = {}
        for inv in BASE_DATOS_INVITACIONES.values():
            if inv["accion"] == socio_actual["accion"]:
                invitados_previos[inv["cedula_invitado"]] = {
                    "nombre": inv["nombre_invitado"],
                    "correo": inv.get("correo", "")
                }

        # Selectores dinámicos FUERA del formulario para permitir autocompletado
        modo_ingreso = st.radio("Seleccione el tipo de registro:", ["Nuevo Invitado", "Invitado Frecuente"])
        
        n_cedula_def = ""
        n_nombre_def = ""
        n_correo_def = ""
        
        if modo_ingreso == "Invitado Frecuente":
            if invitados_previos:
                inv_sel = st.selectbox("Seleccione de su directorio:", list(invitados_previos.keys()), format_func=lambda x: f"{invitados_previos[x]['nombre']} (C.I: {x})")
                n_cedula_def = inv_sel
                n_nombre_def = invitados_previos[inv_sel]['nombre']
                n_correo_def = invitados_previos[inv_sel]['correo']
            else:
                st.info("Aún no tienes invitados guardados en tu directorio.")

        with st.form("form_invitacion"):
            col_a, col_b = st.columns(2)
            with col_a:
                n_cedula_inv = st.text_input("Cédula del Invitado", value=n_cedula_def)
                n_nombre_inv = st.text_input("Nombre del Invitado", value=n_nombre_def)
            with col_b:
                n_correo_inv = st.text_input("Correo Electrónico", value=n_correo_def)
                n_nacimiento_inv = st.date_input("Fecha de Nacimiento", min_value=datetime(1920, 1, 1), max_value=datetime.today())
            
            st.write("---")
            st.markdown("#### 📸 Documento de Identidad")
            foto_cedula = st.file_uploader("Sube la foto de la Cédula (Fase Beta - Interfaz Lista)", type=["jpg", "png", "jpeg"])
            st.write("---")
            
            fecha_visita = st.date_input("Fecha de la visita (Válido por todo el día)", min_value=datetime.today())
            btn_generar = st.form_submit_button("Generar Pase QR")
            
        if btn_generar:
            if socio_actual["solvencia"] != "Al dia":
                st.error("❌ Operación Denegada. Tu grupo familiar presenta morosidad.")
            elif not n_cedula_inv or not n_nombre_inv:
                st.error("⚠️ Debes ingresar al menos la Cédula y el Nombre del invitado.")
            else:
                str_fecha = fecha_visita.strftime("%Y-%m-%d")
                str_nacimiento = n_nacimiento_inv.strftime("%Y-%m-%d")
                id_unico = f"INV-{socio_actual['accion']}-{str(uuid.uuid4())[:6].upper()}"
                
                BASE_DATOS_INVITACIONES[id_unico] = {
                    "accion": socio_actual["accion"],
                    "fecha_visita": str_fecha,
                    "cedula_invitado": n_cedula_inv,
                    "nombre_invitado": n_nombre_inv,
                    "fecha_nacimiento": str_nacimiento,
                    "correo": n_correo_inv,
                    "estatus": "Activo"
                }
                guardar_bd_invitaciones(BASE_DATOS_INVITACIONES)
                
                datos_qr = f"INVITADO|{id_unico}"
                img = qrcode.make(datos_qr)
                buffer = BytesIO()
                img.save(buffer, format="PNG")
                
                st.success(f"✅ Pase generado para {n_nombre_inv}. Válido para el día: {str_fecha}")
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
                if "CEDULA:" in datos_decodificados:
                    cedula_escaneada = datos_decodificados.split("|")[0].replace("CEDULA:", "")
                    if cedula_escaneada in BASE_DATOS_SOCIOS:
                        socio = BASE_DATOS_SOCIOS[cedula_escaneada]
                        if socio["solvencia"] == "Al dia":
                            st.success("✅ ACCESO PERMITIDO (Socio)")
                            st.info(f"**Socio:** {socio['nombre']} | **Acción:** {socio['accion']}")
                            st.session_state.historial.insert(0, {"nombre": socio["nombre"], "accion": socio["accion"], "hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "via": "QR (Socio)"})
                        else:
                            st.error("❌ ACCESO DENEGADO - SOCIO MOROSO")
                    else:
                        st.error("⚠️ El socio ya no existe en la BD.")
                
                elif "INVITADO|" in datos_decodificados:
                    id_qr = datos_decodificados.split("|")[1]
                    if id_qr in BASE_DATOS_INVITACIONES:
                        pase = BASE_DATOS_INVITACIONES[id_qr]
                        
                        if pase["estatus"] == "Activo":
                            fecha_hoy = datetime.now().strftime("%Y-%m-%d")
                            fecha_pase = pase["fecha_visita"]
                            
                            if fecha_hoy == fecha_pase:
                                accion_invita = pase["accion"]
                                socio_solvente = any(s["accion"] == accion_invita and s["solvencia"] == "Al dia" for s in BASE_DATOS_SOCIOS.values())
                                
                                if socio_solvente:
                                    st.success(f"✅ ACCESO PERMITIDO (Invitado: {pase['nombre_invitado']})")
                                    st.info(f"C.I: {pase['cedula_invitado']} | Autorizado por Acción: {accion_invita}")
                                    
                                    BASE_DATOS_INVITACIONES[id_qr]["estatus"] = "Usado"
                                    guardar_bd_invitaciones(BASE_DATOS_INVITACIONES)
                                    
                                    st.session_state.historial.insert(0, {"nombre": f"Inv: {pase['nombre_invitado']}", "accion": accion_invita, "hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "via": "QR (Invitado)"})
                                else:
                                    st.error("❌ ACCESO DENEGADO - La Acción que emitió este pase está Morosa.")
                            elif fecha_hoy > fecha_pase:
                                st.error("❌ ACCESO DENEGADO - Este pase expiró.")
                                BASE_DATOS_INVITACIONES[id_qr]["estatus"] = "Vencido"
                                guardar_bd_invitaciones(BASE_DATOS_INVITACIONES)
                            else:
                                st.warning("⚠️ ACCESO DENEGADO - Este pase es para una fecha futura.")
                        else:
                            st.error(f"❌ ACCESO DENEGADO - Este código QR ya se encuentra {pase['estatus']}.")
                    else:
                        st.warning("⚠️ Código de invitado no encontrado.")
            else:
                st.warning("⚠️ No se detectó un código válido.")
        
        st.write("---")
        st.markdown("### 📊 Registro de Entradas (Local)")
        if st.session_state.historial:
            for acceso in st.session_state.historial:
                st.write(f"🟢 **{acceso['nombre']}** (Acc. {acceso['accion']}) - {acceso['hora']}")

    # --- MÓDULO 4: ADMINISTRACIÓN (Intacto) ---
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
                            st.error(f"⚠️ Operación denegada: La Acción {n_accion} ya tiene un Titular.")
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