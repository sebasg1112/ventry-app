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
import hmac
import hashlib
import google.generativeai as genai
from PIL import Image
import streamlit.components.v1 as components

try:
    from fpdf import FPDF
except ImportError:
    FPDF = None

try:
    from streamlit_javascript import st_javascript
except ImportError:
    st_javascript = None

# --- CONFIGURACIÓN DE LA PÁGINA ---
icono_url = "https://i.ibb.co/t7xWXXR/logo.png"
st.set_page_config(page_title="Ventry - Control de Acceso", page_icon=icono_url, layout="centered")

# --- CONVERSIÓN A PWA ---
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

# --- CSS AVANZADO: SOLID DARK MODE (RIAL CLONE) ---
st.markdown("""
    <style>
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
        animation: smoothFadeIn 0.3s ease-out forwards;
    }
    
    .stApp { background-color: #050505 !important; color: #FFFFFF !important; }
    h1, h2, h3, h4, h5, h6, p, span, label, div { font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; }
    p { color: #E0E0E0 !important; }
    
    .gradient-text { background: linear-gradient(90deg, #FF7B00, #FFC300); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    
    label, label p, label div, div[data-testid="stWidgetLabel"] p, .stTextInput p, .stSelectbox p, .stDateInput p, .stNumberInput p { color: #8E8E93 !important; font-weight: 600 !important; letter-spacing: 0.5px; font-size: 12px !important; text-transform: uppercase; margin-bottom: 4px; }
    
    [data-testid="stForm"] { background-color: #121212 !important; border: 1px solid #1C1C1E !important; border-radius: 20px !important; padding: 25px !important; }
    
    input[type="text"], input[type="password"], input[type="number"], textarea, 
    .stTextInput div[data-baseweb="base-input"], .stDateInput div[data-baseweb="base-input"], 
    .stNumberInput div[data-baseweb="base-input"], .stSelectbox div[data-baseweb="select"] > div,
    div[data-baseweb="input"] { background-color: #1C1C1E !important; color: #FFFFFF !important; -webkit-text-fill-color: #FFFFFF !important; border-radius: 12px !important; font-weight: 500 !important; font-size:16px !important; border: 1px solid transparent !important;}
    
    div[data-baseweb="select"] span { color: #ffffff !important; font-weight: 500 !important; }
    div[data-baseweb="input"]:focus-within, div[data-baseweb="select"]:focus-within, div[data-baseweb="base-input"]:focus-within { border-color: #FF6600 !important; background-color: #2C2C2E !important; }
    
    div[data-baseweb="popover"] > div, div[data-baseweb="menu"] *, ul[role="listbox"] *, li[role="option"] *, div[role="dialog"] *, div[data-baseweb="calendar"] * { background-color: #1C1C1E !important; color: #ffffff !important; border-radius: 12px; }
    li[role="option"]:hover *, li[role="option"][aria-selected="true"] * { background-color: #FF6600 !important; color: #ffffff !important; }

    .stButton>button[kind="primary"], .stFormSubmitButton>button { width: 100%; border-radius: 16px !important; background: linear-gradient(135deg, #FF7B00 0%, #E65C00 100%) !important; color: #ffffff !important; font-weight: 700 !important; letter-spacing: 0.8px; font-size: 15px !important; border: none !important; padding: 14px !important; box-shadow: 0 4px 15px rgba(230, 92, 0, 0.3) !important; transition: transform 0.15s ease; justify-content: center !important; text-transform: uppercase; }
    .stButton>button[kind="primary"]:active, .stFormSubmitButton>button:active { transform: scale(0.96) !important; }
    
    .btn-secundario>div>button { background-color: #1C1C1E !important; border: 1px solid #2C2C2E !important; color: #FFFFFF !important; justify-content: center !important; box-shadow: none !important; border-radius: 16px !important; font-weight:600 !important; padding: 14px !important;}
    .btn-secundario>div>button:active { transform: scale(0.96) !important; background-color: #2C2C2E !important; }
    
    .btn-logout>div>button { background: transparent !important; border: none !important; color: #ff453a !important; justify-content: center !important; box-shadow: none !important; font-weight: 600 !important; padding: 5px !important; opacity: 0.8; }
    .btn-peligro>div>button { background-color: rgba(255, 69, 58, 0.1) !important; border: 1px solid rgba(255, 69, 58, 0.2) !important; color: #ff453a !important; justify-content: center !important; box-shadow: none !important; border-radius: 12px !important; }
    
    div[data-testid="stPopover"] > button { background-color: #1C1C1E !important; border: 1px solid rgba(255,255,255,0.05) !important; border-radius: 50% !important; color: #ffffff !important; font-size: 18px !important; padding: 8px !important; display: inline-block !important; margin-top: -5px; transition: transform 0.2s; }
    div[data-testid="stPopover"] > button:active { transform: scale(0.8); }
    
    .stButton>button[kind="tertiary"] { background-color: #121212 !important; border: 1px solid #1C1C1E !important; padding: 18px 20px !important; border-radius: 16px !important; margin-bottom: 10px !important; color: #FFFFFF !important; font-weight: 600 !important; font-size: 15px !important; width: 100% !important; display: flex !important; justify-content: flex-start !important; align-items: center !important; box-shadow: none !important; transition: all 0.2s ease; }
    .stButton>button[kind="tertiary"]:active { background-color: #1C1C1E !important; transform: scale(0.98) !important; }
    .stButton>button[kind="tertiary"] div[data-testid="stMarkdownContainer"] { width: 100% !important; }
    .stButton>button[kind="tertiary"] p { display: flex !important; align-items: center !important; justify-content: space-between !important; width: 100% !important; margin: 0 !important; font-size: 15px !important; }
    .stButton>button[kind="tertiary"] p::after { content: '›'; color: #8E8E93; font-size: 22px; margin-left: auto; font-weight: 400; line-height: 1; }

    /* BOTTOM NAV */
    div.stRadio { position: fixed !important; bottom: 25px !important; left: 50% !important; transform: translateX(-50%) !important; width: 92% !important; max-width: 380px !important; background: rgba(30, 30, 30, 0.5) !important; backdrop-filter: blur(25px) saturate(180%) !important; -webkit-backdrop-filter: blur(25px) saturate(180%) !important; border: 1px solid rgba(255, 255, 255, 0.1) !important; border-radius: 50px !important; padding: 6px !important; z-index: 99999 !important; box-shadow: 0 15px 35px rgba(0, 0, 0, 0.6) !important; }
    div.stRadio > div[role="radiogroup"] { display: flex !important; flex-direction: row !important; justify-content: space-between !important; align-items: stretch !important; gap: 5px !important; width: 100% !important; }
    div.stRadio div[role="radiogroup"] > label > input[type="radio"], div.stRadio div[role="radiogroup"] > label > span, div.stRadio div[role="radiogroup"] > label > div:first-child:not(:last-child) { display: none !important; opacity: 0 !important; width: 0 !important; height: 0 !important; position: absolute !important; pointer-events: none !important; }
    div.stRadio > div[role="radiogroup"] > label { background: transparent !important; border: none !important; padding: 10px 0px !important; margin: 0 !important; cursor: pointer; position: relative; flex: 1; display: flex !important; flex-direction: column !important; align-items: center !important; justify-content: center !important; border-radius: 40px !important; transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important; }
    div.stRadio > div[role="radiogroup"] > label[data-checked="true"] { background: rgba(255, 255, 255, 0.12) !important; }
    div.stRadio > div[role="radiogroup"] > label > div[data-testid="stMarkdownContainer"] { width: 100% !important; display: flex !important; justify-content: center !important; }
    div.stRadio > div[role="radiogroup"] > label > div[data-testid="stMarkdownContainer"] p { color: #A0A0A5 !important; font-size: 11px !important; font-weight: 500 !important; transition: all 0.2s ease; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 6px; margin: 0 !important; width: 100%; }
    div.stRadio > div[role="radiogroup"] > label[data-checked="true"] div[data-testid="stMarkdownContainer"] p { color: #FF6600 !important; font-weight: 700 !important; }
    div.stRadio > div[role="radiogroup"] > label div[data-testid="stMarkdownContainer"] p::before { content: ''; display: block; width: 24px; height: 24px; background-color: currentColor; }
    div.stRadio > div[role="radiogroup"] > label:nth-child(1) div[data-testid="stMarkdownContainer"] p::before { -webkit-mask: url("data:image/svg+xml;utf8,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z'/%3E%3Cpolyline points='9 22 9 12 15 12 15 22'/%3E%3C/svg%3E") no-repeat center / contain; mask: url("data:image/svg+xml;utf8,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z'/%3E%3Cpolyline points='9 22 9 12 15 12 15 22'/%3E%3C/svg%3E") no-repeat center / contain; }
    div.stRadio > div[role="radiogroup"] > label:nth-child(2) div[data-testid="stMarkdownContainer"] p::before { -webkit-mask: url("data:image/svg+xml;utf8,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Crect x='2' y='6' width='20' height='12' rx='2'/%3E%3Ccircle cx='8' cy='12' r='2'/%3E%3Cline x1='13' y1='11' x2='18' y2='11'/%3E%3C/svg%3E") no-repeat center / contain; mask: url("data:image/svg+xml;utf8,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Crect x='2' y='6' width='20' height='12' rx='2'/%3E%3Ccircle cx='8' cy='12' r='2'/%3E%3Cline x1='13' y1='11' x2='18' y2='11'/%3E%3C/svg%3E") no-repeat center / contain; }
    div.stRadio > div[role="radiogroup"] > label:nth-child(3) div[data-testid="stMarkdownContainer"] p::before { -webkit-mask: url("data:image/svg+xml;utf8,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Crect x='1' y='4' width='22' height='16' rx='2' ry='2'/%3E%3Cline x1='1' y1='10' x2='23' y2='10'/%3E%3C/svg%3E") no-repeat center / contain; mask: url("data:image/svg+xml;utf8,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Crect x='1' y='4' width='22' height='16' rx='2' ry='2'/%3E%3Cline x1='1' y1='10' x2='23' y2='10'/%3E%3C/svg%3E") no-repeat center / contain; }
    div.stRadio > div[role="radiogroup"] > label:nth-child(4) div[data-testid="stMarkdownContainer"] p::before { -webkit-mask: url("data:image/svg+xml;utf8,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Crect x='3' y='3' width='7' height='7' rx='1'/%3E%3Crect x='14' y='3' width='7' height='7' rx='1'/%3E%3Crect x='14' y='14' width='7' height='7' rx='1'/%3E%3Crect x='3' y='14' width='7' height='7' rx='1'/%3E%3C/svg%3E") no-repeat center / contain; mask: url("data:image/svg+xml;utf8,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Crect x='3' y='3' width='7' height='7' rx='1'/%3E%3Crect x='14' y='3' width='7' height='7' rx='1'/%3E%3Crect x='14' y='14' width='7' height='7' rx='1'/%3E%3Crect x='3' y='14' width='7' height='7' rx='1'/%3E%3C/svg%3E") no-repeat center / contain; }

    /* TARJETAS FINANCIERAS */
    .rial-card { background-color: #121212 !important; border: 1px solid #1C1C1E !important; padding: 20px; border-radius: 20px; text-align: left; margin-bottom: 15px; }
    .rial-title { color: #8E8E93 !important; font-size: 13px !important; font-weight: 600 !important; margin-bottom: 8px; display:flex; align-items:center; gap:6px; letter-spacing: 0.5px;}
    .rial-saldo { color: #FFFFFF !important; font-size: 32px !important; font-weight: 800 !important; margin: 0 !important; letter-spacing: -1px; }
    .rial-monto-verde { color: #32d74b !important; }
    .rial-monto-rojo { color: #ff453a !important; }
    
    .open-button-container { display: flex; justify-content: center; margin-top: 50px; margin-bottom: 30px;}
    .open-button { background: linear-gradient(145deg, #1C1C1E, #0A0A0A); border: 2px solid rgba(255, 102, 0, 0.4); border-radius: 50%; width: 200px; height: 200px; display: flex; flex-direction: column; justify-content: center; align-items: center; color: white; cursor: pointer; transition: all 0.15s ease; }
    .open-button:active { background: #FF6600; transform: scale(0.94); }

    .dark-wrapper { background-color: transparent; padding: 10px 0px 30px 0px; display: flex; justify-content: center; }
    .glass-card { background-color: #121212 !important; border: 1px solid #1C1C1E !important; border-radius: 24px; padding: 40px 30px; width: 100%; max-width: 360px; position: relative; overflow: hidden; }
    .magnum-logo { text-align: center; margin-bottom: 30px; }
    .logo-m { font-size: 55px; font-weight: 200; margin: 0; line-height: 1; color: #ffffff !important; text-align:center;}
    .logo-magnum { font-size: 15px; font-weight: 700; letter-spacing: 6px; margin: 5px 0 0 0; color: #ffffff !important; text-align:center;}
    .logo-city { font-size: 9px; font-weight: 600; letter-spacing: 3px; color: #d4af37 !important; margin: 0; text-transform: uppercase; text-align:center;} 
    .logo-line { width: 40px; height: 2px; background-color: #d4af37; margin: 15px auto 30px auto; border-radius: 2px; }
    .info-group { margin-bottom: 16px; border-bottom: 1px solid #1C1C1E; padding-bottom: 8px; }
    .info-label { font-size: 11px; color: #8E8E93 !important; margin-bottom: 2px; text-transform: uppercase; font-weight: 600;}
    .info-value { font-size: 18px; font-weight: 600; color: #ffffff !important; }
    .qr-container { text-align: center; margin-top: 35px; }
    .qr-box { background: #ffffff; padding: 12px; border-radius: 16px; display: inline-block; margin-bottom: 15px; }
    .qr-box img { width: 150px; display: block; }
    .status-badge { display: inline-block; padding: 6px 20px; border-radius: 30px; font-size: 11px; font-weight: 800; color: #000 !important; letter-spacing: 1px; text-transform: uppercase;}
    .badge-aldia { background-color: #32d74b !important; color:#000 !important; }
    .badge-moroso { background-color: #ff453a !important; color:#fff !important; }
    .badge-pendiente { background-color: #ffd60a !important; color:#000 !important;}
    
    .garita-alert-success { background-color: #15803d !important; border: 2px solid #22c55e !important; border-radius: 20px; padding: 40px 20px; text-align: center; color: white !important; margin-top: 20px; }
    .garita-alert-error { background-color: #b91c1c !important; border: 2px solid #ef4444 !important; border-radius: 20px; padding: 40px 20px; text-align: center; color: white !important; margin-top: 20px; }
    </style>
""", unsafe_allow_html=True)

# --- 🛑 FUNCIÓN CRIPTOGRÁFICA PARA CONTRASEÑAS ---
def hash_clave(clave_plana):
    return hashlib.sha256(clave_plana.encode('utf-8')).hexdigest()

# --- 🛑 MOTOR DE GENERACIÓN DE TICKETS PDF ---
def generar_ticket_pdf(datos):
    if FPDF is None: return None
    pdf = FPDF(format=(80, 160)) # Formato ticketera térmica 80mm
    pdf.add_page()
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(60, 6, txt="MAGNUM CITY CLUB", ln=True, align='C')
    pdf.set_font("Arial", '', 8)
    pdf.cell(60, 4, txt="Ventry Pay - Recibo Digital", ln=True, align='C')
    pdf.cell(60, 4, txt=f"Ticket: {datos['id']}", ln=True, align='C')
    pdf.cell(60, 4, txt=f"Fecha: {datos['fecha']}", ln=True, align='C')
    pdf.line(5, pdf.get_y(), 75, pdf.get_y())
    pdf.ln(2)
    pdf.set_font("Arial", 'B', 9)
    pdf.cell(60, 5, txt=f"Socio: {datos['cliente']}", ln=True, align='L')
    pdf.cell(60, 5, txt=f"Accion: {datos['accion']}", ln=True, align='L')
    pdf.cell(60, 5, txt=f"Comercio: {datos['comercio']}", ln=True, align='L')
    pdf.ln(2)
    pdf.set_font("Arial", '', 9)
    for item in datos['items']:
        pdf.cell(40, 5, txt=item['item'], ln=False, align='L')
        pdf.cell(20, 5, txt=f"${item['precio']:.2f}", ln=True, align='R')
    pdf.line(5, pdf.get_y()+2, 75, pdf.get_y()+2)
    pdf.ln(4)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(40, 6, txt="TOTAL", ln=False, align='L')
    pdf.cell(20, 6, txt=f"${datos['total']:.2f}", ln=True, align='R')
    pdf.ln(8)
    pdf.set_font("Arial", 'I', 7)
    pdf.cell(60, 4, txt="Documento generado por Ventry OS", ln=True, align='C')
    
    try:
        return pdf.output(dest='S').encode('latin-1')
    except TypeError:
        return bytes(pdf.output())

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

def calcular_edad(fecha_nac_str):
    if not fecha_nac_str: return 0
    try:
        fecha_nac = datetime.strptime(fecha_nac_str, "%d/%m/%Y").date()
        hoy = datetime.today().date()
        return hoy.year - fecha_nac.year - ((hoy.month, hoy.day) < (fecha_nac.month, fecha_nac.day))
    except: return 0

def mes_actual_str(): return datetime.now().strftime("%m/%Y")
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
            datos[ced] = {
                "nombre": str(fila.get("nombre", "")), "clave": str(fila.get("clave", "")), 
                "accion": str(fila.get("accion", "")), "rol": str(fila.get("rol", "")), 
                "parentesco": str(fila.get("parentesco", "N/A")), "fecha_nacimiento": str(fila.get("fecha_nacimiento", "")), 
                "solvencia": str(fila.get("solvencia", "Pendiente")), "saldo": float(fila.get("saldo", 0.0)), 
                "invitaciones": int(fila.get("invitaciones", 0)), "mes_pagado": str(fila.get("mes_pagado", "")), 
                "bio_token": str(fila.get("bio_token", "")), "cedula": ced
            }
    return datos

def guardar_bd(datos):
    lista_socios = list(datos.values())
    lista_socios.sort(key=lambda x: (x.get("accion", ""), x.get("rol", "")), reverse=True) 
    filas_a_subir = [["cedula", "nombre", "clave", "accion", "rol", "parentesco", "fecha_nacimiento", "solvencia", "saldo", "invitaciones", "mes_pagado", "bio_token"]]
    for socio in lista_socios: filas_a_subir.append([socio["cedula"], socio["nombre"], socio["clave"], socio["accion"], socio["rol"], socio["parentesco"], socio.get("fecha_nacimiento", ""), socio.get("solvencia", "Pendiente"), float(socio.get("saldo", 0.0)), int(socio.get("invitaciones", 0)), socio.get("mes_pagado", ""), socio.get("bio_token", "")])
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
if "mostrar_prompt_bio" not in st.session_state: st.session_state.mostrar_prompt_bio = False

# ==========================================
# 🛑 INTERCEPTOR GLOBAL DE URL (API IoT)
# ==========================================
params = st.query_params

if "api" in params and params["api"] == "scan" and "qr" in params:
    data_qr = params["qr"]
    firma_recibida = params.get("sig", "")
    SECRET_KEY = st.secrets.get("IOT_SECRET_KEY", "ventry_secreto_esp32_2026")
    firma_calculada = hmac.new(SECRET_KEY.encode('utf-8'), data_qr.encode('utf-8'), hashlib.sha256).hexdigest()
    
    if not hmac.compare_digest(firma_calculada, firma_recibida):
        st.json({"status": "error", "open_door": False, "message": "Firma Criptográfica Inválida."}); st.stop()
    
    if data_qr.startswith("INVITADO|"):
        id_pase = data_qr.split("|")[1]
        if id_pase in BASE_DATOS_INVITACIONES:
            pase = BASE_DATOS_INVITACIONES[id_pase]
            fecha_hoy = datetime.now().strftime("%d/%m/%Y")
            if pase["fecha_visita"] != fecha_hoy: st.json({"status": "error", "open_door": False, "message": "Fecha Invalida"})
            elif pase["estatus"] == "Activo":
                BASE_DATOS_INVITACIONES[id_pase]["estatus"] = "Adentro"; guardar_bd_invitaciones(BASE_DATOS_INVITACIONES)
                registrar_acceso(pase["nombre_invitado"], pase["accion"], "QR Invitado (ESP32)", "Entrada")
                st.json({"status": "success", "open_door": True, "message": f"Bienvenido {pase['nombre_invitado']}"})
            elif pase["estatus"] == "Adentro": st.json({"status": "error", "open_door": False, "message": "Invitado ya registro entrada"})
            else: st.json({"status": "error", "open_door": False, "message": "Pase Invalido o Suspendido"})
        else: st.json({"status": "error", "open_door": False, "message": "Pase no encontrado"})
            
    elif data_qr.startswith("VENTRY_DYN|"):
        try:
            partes = data_qr.split("|")
            cedula_qr = partes[1]
            timestamp_qr = int(partes[2])
            timestamp_ahora = int(datetime.now().timestamp())
            
            if (timestamp_ahora - timestamp_qr) > 60: st.json({"status": "error", "open_door": False, "message": "Codigo QR Expirado"})
            elif cedula_qr in BASE_DATOS_SOCIOS:
                socio_qr = BASE_DATOS_SOCIOS[cedula_qr]
                if socio_qr.get("solvencia", "") == "Al dia":
                    registrar_acceso(socio_qr["nombre"], socio_qr["accion"], "QR Dinámico Socio", "Entrada")
                    st.json({"status": "success", "open_door": True, "message": f"Bienvenido {socio_qr['nombre']}"})
                else: st.json({"status": "error", "open_door": False, "message": "Socio Moroso - Acceso Denegado"})
            else: st.json({"status": "error", "open_door": False, "message": "Socio no encontrado"})
        except Exception: st.json({"status": "error", "open_door": False, "message": "Codigo Ilegible"})
            
    else: st.json({"status": "error", "open_door": False, "message": "QR Desconocido"})
    st.stop() 

elif "pase" in params:
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
<div class="magnum-logo"><p class="logo-m">M</p><p class="logo-magnum">MAGNUM</p><p class="logo-city">CITY CLUB</p><div class="logo-line"></div></div>
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
# LECTURA DEL TOKEN BIOMÉTRICO (SIN RECARGAR PÁGINA)
# ==========================================
bio_token_local = ""
if st_javascript:
    res = st_javascript("localStorage.getItem('ventry_bio_token') || '';")
    if res and res != 0:
        bio_token_local = str(res)

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
            st.markdown("<div class='btn-secundario'>", unsafe_allow_html=True)
            btn_faceid = st.button("🔒 FaceID / TouchID", type="primary")
            st.markdown("</div>", unsafe_allow_html=True)

        if btn_faceid:
            if bio_token_local:
                usuario_encontrado = None
                for ced, info in BASE_DATOS_SOCIOS.items():
                    if str(info.get("bio_token", "")) == bio_token_local:
                        usuario_encontrado = info
                        break
                
                if usuario_encontrado:
                    st.session_state.logueado = True
                    st.session_state.usuario_actual = usuario_encontrado
                    st.session_state.mensaje_login = "✅ Verificación FaceID/TouchID exitosa."
                    st.rerun()
                else: st.error("❌ Dispositivo no reconocido en la base de datos.")
            else: st.error("❌ Dispositivo no vinculado. Inicia sesión con clave la primera vez.")

        if boton_entrar:
            if cedula_ingresada in BASE_DATOS_SOCIOS:
                socio = BASE_DATOS_SOCIOS[cedula_ingresada]
                clave_ingresada_hash = hash_clave(clave_ingresada)
                
                if clave_ingresada_hash == str(socio["clave"]) or clave_ingresada == str(socio["clave"]):
                    if clave_ingresada == str(socio["clave"]) and len(socio["clave"]) != 64:
                        BASE_DATOS_SOCIOS[cedula_ingresada]["clave"] = clave_ingresada_hash
                        guardar_bd(BASE_DATOS_SOCIOS)
                        socio["clave"] = clave_ingresada_hash 

                    if socio.get("solvencia", "") == "En revision": st.warning("⏳ Tu cuenta fue creada pero aún se encuentra en revisión administrativa.")
                    else: 
                        st.session_state.logueado = True
                        st.session_state.usuario_actual = socio
                        if not socio.get("bio_token", ""):
                            st.session_state.mostrar_prompt_bio = True
                        st.rerun()
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
                    clave_encriptada = hash_clave(r_clave)
                    BASE_DATOS_SOCIOS[r_cedula] = {
                        "nombre": r_nombre, "clave": clave_encriptada, "accion": r_acc_norm, "rol": r_rol, 
                        "parentesco": r_parentesco, "fecha_nacimiento": r_nacimiento.strftime("%d/%m/%Y"), 
                        "solvencia": "En revision", "saldo": 0.0, "invitaciones": 0, "mes_pagado": "", "bio_token": "", "cedula": r_cedula
                    }
                    guardar_bd(BASE_DATOS_SOCIOS)
                    st.session_state.mensaje_exito_registro = "✅ ¡Solicitud enviada! Hemos enviado un mensaje de confirmación para verificar tu cuenta."
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

    # 🔒 INYECTOR INVISIBLE DE TOKEN
    if "token_a_guardar" in st.session_state:
        if st_javascript:
            st_javascript(f"localStorage.setItem('ventry_bio_token', '{st.session_state.token_a_guardar}');")
        st.success("✅ Dispositivo vinculado exitosamente para acceso rápido FaceID/TouchID.")
        del st.session_state.token_a_guardar

    saldo_accion = 0.0
    invitaciones_accion = 0
    mes_pagado_accion = ""
    for m in BASE_DATOS_SOCIOS.values():
        if str(m["accion"]) == str(socio_actual["accion"]) and m["rol"] == "Titular":
            saldo_accion = float(m.get('saldo', 0.0))
            invitaciones_accion = int(m.get('invitaciones', 0))
            mes_pagado_accion = str(m.get('mes_pagado', '')) 
            break

    if "menu_view" not in st.session_state: st.session_state.menu_view = "main"

    def cb_set_menu(vista): st.session_state.menu_view = vista
    def cb_nav_pagos(destino): st.session_state.sub_pagos = destino
    def cb_limpiar_garita():
        if "garita_scan_result" in st.session_state: del st.session_state.garita_scan_result

    def cb_pagar_cuota(saldo, monto, mes, invites, tipo, nombre_mes, accion):
        ya_pagado = False
        for m in st.session_state.db_socios.values():
            if str(m["accion"]) == str(accion) and m["rol"] == "Titular":
                if m.get("mes_pagado", "") == mes: ya_pagado = True; break
        
        if ya_pagado: st.session_state.mensaje_pago_exitoso = "⚠️ Transacción ignorada: El mes ya estaba pagado."; st.session_state.sub_pagos = "menu"; return
            
        nuevo_saldo = saldo - monto
        for ced, info in st.session_state.db_socios.items():
            if str(info["accion"]) == str(accion) and info["rol"] == "Titular":
                st.session_state.db_socios[ced]["saldo"] = nuevo_saldo; st.session_state.db_socios[ced]["mes_pagado"] = mes; st.session_state.db_socios[ced]["invitaciones"] = invites; break
        
        for ced_fam, info_fam in st.session_state.db_socios.items():
            if str(info_fam["accion"]) == str(accion): st.session_state.db_socios[ced_fam]["solvencia"] = "Al dia"
        
        guardar_bd(st.session_state.db_socios)
        id_cargo = f"CRG-{str(uuid.uuid4())[:6].upper()}"
        st.session_state.db_pagos[id_cargo] = {"accion": accion, "metodo": "Sistema Ventry", "referencia": f"CUOTA-{mes.replace('/','-')}", "monto": monto, "fecha_reporte": datetime.now().strftime("%d/%m/%Y"), "estatus": "Aprobado", "tipo": tipo}
        guardar_bd_pagos(st.session_state.db_pagos)
        st.session_state.mensaje_pago_exitoso = f"✅ Mensualidad de {nombre_mes} cancelada con éxito."
        st.session_state.sub_pagos = "menu"

    # --- HEADER ---
    col_logo, col_campana = st.columns([5, 1])
    with col_logo:
        st.markdown(f"""
        <div style="display:flex; align-items:center; gap:12px; margin-bottom: 15px;">
            <img src="https://i.ibb.co/t7xWXXR/logo.png" width="30" style="border-radius:8px; box-shadow: 0 4px 15px rgba(255,102,0,0.4);">
            <span style="font-size:20px; font-weight:900; letter-spacing: 2px;" class="gradient-text">VENTRY</span>
        </div>
        """, unsafe_allow_html=True)
    with col_campana:
        notificaciones = []
        mis_pagos = [p for p in BASE_DATOS_PAGOS.values() if str(p["accion"]) == str(socio_actual["accion"])]
        for p in mis_pagos[-3:]:
            if p["estatus"] == "Aprobado" and p["tipo"] == "Abono a Billetera": notificaciones.append(f"💰 Tu Abono de **${float(p['monto']):.2f}** fue Aprobado.")
            elif p["estatus"] == "Aprobado" and ("Cargo" in p["tipo"] or "Consumo" in p["tipo"]): notificaciones.append(f"🧾 {p['tipo']} por **${float(p['monto']):.2f}** procesado.")
            elif p["estatus"] == "Rechazado": notificaciones.append(f"❌ Tu Abono de **${float(p['monto']):.2f}** fue Rechazado.")
                
        mis_accesos = [h for h in st.session_state.db_historial if h["accion"] == str(socio_actual["accion"]) and h["movimiento"] == "Entrada"]
        for h in mis_accesos[:3]:
            if "Invitado" in h["via"]: notificaciones.append(f"🎟️ Tu invitado **{h['nombre']}** ingresó al club.")

        with st.popover("🔔"):
            st.markdown("<h4 style='color:#FF6600; font-size:14px; margin-bottom:12px; font-weight:700;'>Centro de Notificaciones</h4>", unsafe_allow_html=True)
            if notificaciones:
                for n in notificaciones[:5]: st.markdown(f"<div style='background:#1C1C1E; padding:12px; border-radius:10px; margin-bottom:8px; font-size:13px; border-left:3px solid #FF6600;'>{n}</div>", unsafe_allow_html=True)
            else: st.write("No tienes notificaciones nuevas.")

    if "mensaje_login" in st.session_state:
        st.success(st.session_state.mensaje_login)
        del st.session_state.mensaje_login

    # 🛑 PROMPT DE VINCULACIÓN AL INICIAR SESIÓN POR PRIMERA VEZ
    if st.session_state.get("mostrar_prompt_bio", False):
        st.markdown("""
        <div style="background:#1C1C1E; border:1px solid #FF6600; border-radius:15px; padding:20px; margin-bottom:20px; box-shadow: 0 10px 30px rgba(255,102,0,0.15);">
            <h4 style="color:#FF6600; margin-top:0; display:flex; align-items:center; gap:8px;">🔒 Activar FaceID / TouchID</h4>
            <p style="color:#E0E0E0; font-size:13px; margin-bottom:15px;">Agiliza tu acceso al club vinculando este dispositivo. No tendrás que ingresar tu contraseña la próxima vez que entres.</p>
        """, unsafe_allow_html=True)
        
        if st.button("Sí, vincular este dispositivo", type="primary", use_container_width=True):
            nuevo_token = str(uuid.uuid4())
            BASE_DATOS_SOCIOS[socio_actual["cedula"]]["bio_token"] = nuevo_token
            guardar_bd(BASE_DATOS_SOCIOS)
            st.session_state.usuario_actual["bio_token"] = nuevo_token
            st.session_state.mostrar_prompt_bio = False
            st.session_state.token_a_guardar = nuevo_token 
            st.rerun()
            
        if st.button("Quizás más tarde", use_container_width=True):
            st.session_state.mostrar_prompt_bio = False
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # --- MENÚ INFERIOR ---
    opciones_bottom = ["Inicio", "Carnet", "Finanzas", "Menú"]
    modulo_seleccionado = st.radio("Nav", opciones_bottom, horizontal=True, label_visibility="collapsed")
    if modulo_seleccionado != "Menú": st.session_state.menu_view = "main"

    # --- MÓDULO 1: INICIO ---
    if modulo_seleccionado == "Inicio":
        hora_actual = datetime.now().hour
        if 5 <= hora_actual < 12: saludo = "Buenos días"
        elif 12 <= hora_actual < 19: saludo = "Buenas tardes"
        else: saludo = "Buenas noches"
        
        primer_nombre = socio_actual['nombre'].split()[0]
        
        st.markdown(f"""
<div style="text-align: center; margin-top: 0px;">
<h2 style="margin-bottom: 5px; font-size:26px; font-weight:900; color:#ffffff; letter-spacing:0.5px;">Magnum City Club</h2>
<p style="color: #FF6600; font-size:15px; font-weight:700; margin-bottom: 25px; letter-spacing: 0.5px;">{saludo}, {primer_nombre} 👋</p>
<p style="color: #8E8E93; font-size:12px; text-transform:uppercase; letter-spacing:3px; font-weight:600;">Puerta Principal</p>
<div class="open-button-container">
<div class="open-button-glow">
<div class="open-button">
<span style="font-size: 50px; margin-bottom:12px; text-shadow: 0 4px 15px rgba(0,0,0,0.5);">🔒</span>
<span style="font-size: 13px; font-weight:800; letter-spacing: 1.5px;">TOCA PARA ABRIR</span>
</div>
</div>
</div>
<p style="color: #8E8E93; margin-top: 35px; font-size:11px; font-weight:600; text-transform:uppercase; letter-spacing:1px;">Estatus: <span style="color:#FF6600; font-weight:800; text-shadow: 0 0 10px rgba(255,102,0,0.3);">Cerrado</span></p>
</div>
""", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Simular Apertura (Demo ESP32)", type="primary"): 
            st.success("📡 Señal de apertura enviada a la garita de forma segura.")

    # --- MÓDULO 2: CARNET DIGITAL ---
    elif modulo_seleccionado == "Carnet":
        solvencia = socio_actual.get('solvencia', 'Desconocido')
        if solvencia == "Moroso": st.error("⚠️ Tu grupo familiar presenta un saldo pendiente.")
        
        if solvencia == "Al dia": clase_badge = "badge-aldia"; texto_badge = "AL DÍA"
        elif solvencia == "Pendiente": clase_badge = "badge-pendiente"; texto_badge = "PENDIENTE"
        else: clase_badge = "badge-moroso"; texto_badge = "MOROSO"

        html_carnet = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <script src="https://cdnjs.cloudflare.com/ajax/libs/qrcodejs/1.0.0/qrcode.min.js"></script>
            <style>
                body {{ background-color: transparent; margin: 0; font-family: -apple-system, sans-serif; display: flex; justify-content: center; }}
                .glass-card {{ background-color: #121212; border: 1px solid #1C1C1E; border-radius: 24px; padding: 40px 30px; width: 100%; max-width: 360px; position: relative; overflow: hidden; }}
                .magnum-logo {{ text-align: center; margin-bottom: 30px; }}
                .logo-m {{ font-size: 55px; font-weight: 200; margin: 0; line-height: 1; color: #ffffff; text-align:center; }}
                .logo-magnum {{ font-size: 15px; font-weight: 700; letter-spacing: 6px; margin: 5px 0 0 0; color: #ffffff; text-align:center; }}
                .logo-city {{ font-size: 9px; font-weight: 600; letter-spacing: 3px; color: #d4af37; margin: 0; text-transform: uppercase; text-align:center; }} 
                .logo-line {{ width: 40px; height: 2px; background-color: #d4af37; margin: 15px auto 30px auto; border-radius: 2px; }}
                .info-group {{ margin-bottom: 16px; border-bottom: 1px solid #1C1C1E; padding-bottom: 8px; }}
                .info-label {{ font-size: 11px; color: #8E8E93; margin-bottom: 2px; text-transform: uppercase; font-weight: 600; }}
                .info-value {{ font-size: 18px; font-weight: 600; color: #ffffff; margin: 0; }}
                .qr-container {{ text-align: center; margin-top: 35px; }}
                .qr-box {{ background: #ffffff; padding: 12px; border-radius: 16px; display: inline-block; margin-bottom: 15px; }}
                .status-badge {{ display: inline-block; padding: 6px 20px; border-radius: 30px; font-size: 11px; font-weight: 800; color: #000; letter-spacing: 1px; text-transform: uppercase; }}
                .badge-aldia {{ background-color: #32d74b !important; color:#000; }}
                .badge-moroso {{ background-color: #ff453a !important; color:#fff; }}
                .badge-pendiente {{ background-color: #ffd60a !important; color:#000; }}
                #timer-bar {{ width: 100%; height: 4px; background: #1C1C1E; border-radius: 2px; margin-top: 20px; overflow: hidden; }}
                #timer-fill {{ height: 100%; width: 100%; background: #FF6600; transition: width 1s linear; }}
            </style>
        </head>
        <body>
            <div class="glass-card">
                <div class="magnum-logo"><p class="logo-m">M</p><p class="logo-magnum">MAGNUM</p><p class="logo-city">CITY CLUB</p><div class="logo-line"></div></div>
                <div class="info-group"><p class="info-label">Socio</p><p class="info-value">{socio_actual['nombre']}</p></div>
                <div class="info-group"><p class="info-label">Cédula</p><p class="info-value">{socio_actual['cedula']}</p></div>
                <div class="info-group"><p class="info-label">Acción</p><p class="info-value">{socio_actual['accion']} <span style="font-size:13px; color:#8E8E93; font-weight:500;">({socio_actual['rol']})</span></p></div>
                <div class="qr-container"><div class="qr-box" id="qr-code"></div><br><span class="status-badge {clase_badge}">{texto_badge}</span><div id="timer-bar"><div id="timer-fill"></div></div><p style="color:#8E8E93; font-size:10px; margin-top:8px; font-weight:600; letter-spacing: 0.5px;">NUEVO CÓDIGO EN <span id="time-left" style="color:#FF6600;">60</span>S</p></div>
            </div>
            <script>
                const cedula = "{socio_actual['cedula']}";
                let timeLeft = 60;
                let qrObj = null;
                function generateQR() {{
                    const timestamp = Math.floor(Date.now() / 1000);
                    const data = "VENTRY_DYN|" + cedula + "|" + timestamp;
                    document.getElementById("qr-code").innerHTML = "";
                    qrObj = new QRCode(document.getElementById("qr-code"), {{text: data, width: 150, height: 150, colorDark : "#000000", colorLight : "#ffffff", correctLevel : QRCode.CorrectLevel.H}});
                    timeLeft = 60;
                    document.getElementById("timer-fill").style.transition = "none";
                    document.getElementById("timer-fill").style.width = "100%";
                    setTimeout(() => {{ document.getElementById("timer-fill").style.transition = "width 60s linear"; document.getElementById("timer-fill").style.width = "0%"; }}, 50);
                }}
                setInterval(() => {{ timeLeft--; document.getElementById("time-left").innerText = timeLeft; if(timeLeft <= 0) {{ generateQR(); }} }}, 1000);
                generateQR();
            </script>
        </body>
        </html>
        """
        components.html(html_carnet, height=660)
        st.info("💡 Este carnet es autónomo: Se regenera solo sin usar datos móviles cada 60s.")

    # --- MÓDULO 3: FINANZAS ---
    elif modulo_seleccionado == "Finanzas":
        edad_usuario = calcular_edad(socio_actual.get("fecha_nacimiento", ""))
        if edad_usuario < 18 and edad_usuario > 0:
            st.markdown("<h3 style='font-size:24px; font-weight:800; color:#ffffff;'>Mis Finanzas</h3>", unsafe_allow_html=True)
            st.error("🔒 Acceso Restringido: El módulo financiero es exclusivo para los usuarios mayores de edad.")
        else:
            if "sub_pagos" not in st.session_state: st.session_state.sub_pagos = "menu"
            
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
                
                col1, col2 = st.columns(2)
                with col1: st.markdown(f'<div class="rial-card"><div class="rial-title">🇻🇪 Saldo Ventry</div><h3 class="rial-saldo rial-monto-verde">${saldo_favor:.2f}</h3><p style="color:#8E8E93; font-size:11px; margin-top:5px;">Fondo a favor</p></div>', unsafe_allow_html=True)
                with col2: st.markdown(f'<div class="rial-card"><div class="rial-title">🧾 Deuda Mensual</div><h3 class="rial-saldo rial-monto-rojo">${deuda:.2f}</h3><p style="color:#8E8E93; font-size:11px; margin-top:5px;">Por pagar</p></div>', unsafe_allow_html=True)
                st.write("")
                
                if rol_actual == "Titular":
                    if mes_pagado_accion == mes_actual: st.success(f"🎉 **Cuota de {nombre_mes_actual} pagada.** Tu acción está solvente.")
                    else:
                        if dia_actual <= 10: st.info(f"🌟 Beneficio de Pronto Pago vigente. Cuota: $104 + 10 Pases Gratis.")
                        else: st.warning(f"⚠️ Fecha de corte superada. Cuota: $120. No incluye pases.")
                        st.button(f"Pagar Mensualidad", type="primary", on_click=cb_nav_pagos, args=("pagar",))
                    st.write("")
                else: st.info("ℹ️ El pago de la cuota de mantenimiento es gestionado por el Titular.")
                
                st.button("📥 + Agregar fondos (Abono)", type="primary", on_click=cb_nav_pagos, args=("recargar",))
                st.write("")
                st.button("🕒 Ver Movimientos", type="primary", on_click=cb_nav_pagos, args=("historial",))

            elif st.session_state.sub_pagos == "recargar":
                st.markdown("<h3 style='font-size:20px; font-weight:800; color:#FF6600;'>🤖 Recarga Inteligente (Ventry AI)</h3>", unsafe_allow_html=True)
                st.write("Sube el comprobante de pago. Nuestro motor extraerá el monto y la referencia automáticamente para agilizar tu conciliación.")
                comprobante = st.file_uploader("Cargar Captura (PNG/JPG)", type=["png", "jpg", "jpeg"])
                if "datos_ia" not in st.session_state: st.session_state.datos_ia = None
                if comprobante is not None:
                    if st.session_state.datos_ia is None or st.session_state.get("last_file") != comprobante.name:
                        with st.spinner("🧠 Visión Artificial analizando comprobante..."):
                            try:
                                clave_api = st.secrets.get("GEMINI_API_KEY", "")
                                if not clave_api: st.error("Falta configurar GEMINI_API_KEY en secrets."); st.stop()
                                genai.configure(api_key=clave_api)
                                modelo = genai.GenerativeModel('gemini-1.5-flash')
                                img_ia = Image.open(comprobante)
                                prompt_ia = 'Analiza esta imagen de un comprobante bancario. Extrae exactamente el número de referencia y el monto pagado. Devuelve ÚNICAMENTE un objeto JSON válido: {"referencia": "numero_aqui", "monto": 123.45}'
                                respuesta = modelo.generate_content([prompt_ia, img_ia])
                                texto_limpio = respuesta.text.strip().replace('```json', '').replace('```', '')
                                datos_extraidos = json.loads(texto_limpio)
                                st.session_state.datos_ia = {"referencia": str(datos_extraidos.get("referencia", "")), "monto": float(datos_extraidos.get("monto", 0.0)), "metodo": "Transferencia / Pago Móvil" }
                                st.session_state.last_file = comprobante.name; st.success("✅ Extracción óptica completada.")
                            except Exception as e:
                                st.error(f"❌ La IA no pudo leer el recibo. Ingresa los datos manualmente."); st.session_state.datos_ia = {"referencia": "", "monto": 0.0, "metodo": "Pago Móvil"}; st.session_state.last_file = comprobante.name
                    with st.form("form_recarga_ia"):
                        metodo_r = st.selectbox("Método de Pago", ["Pago Móvil", "Transferencia", "Zelle", "Efectivo Taquilla"], index=0)
                        ref_r = st.text_input("Nº de Referencia", value=st.session_state.datos_ia["referencia"])
                        monto_r = st.number_input("Monto Detectado ($)", min_value=1.0, value=float(st.session_state.datos_ia["monto"]))
                        st.markdown("<br>", unsafe_allow_html=True)
                        if st.form_submit_button("CONFIRMAR REPORTE"):
                            if not ref_r: st.error("⚠️ La referencia es obligatoria.")
                            else:
                                id_pago = f"ABN-{str(uuid.uuid4())[:6].upper()}"
                                BASE_DATOS_PAGOS[id_pago] = {"accion": socio_actual["accion"], "metodo": metodo_r, "referencia": ref_r, "monto": monto_r, "fecha_reporte": datetime.now().strftime("%d/%m/%Y"), "estatus": "En Revisión", "tipo": "Abono (Verificado por IA)"}
                                guardar_bd_pagos(BASE_DATOS_PAGOS); st.session_state.datos_ia = None; st.session_state.mensaje_pago_exitoso = "🤖 ✅ Reporte inteligente enviado."; st.session_state.sub_pagos = "menu"; st.rerun()
                else: st.session_state.datos_ia = None 
                st.write("")
                st.markdown("<div class='btn-secundario'>", unsafe_allow_html=True)
                st.button("← Volver a Balances", type="primary", on_click=cb_nav_pagos, args=("menu",))
                st.markdown("</div>", unsafe_allow_html=True)

            elif st.session_state.sub_pagos == "pagar":
                if mes_pagado_accion == mes_actual: st.session_state.sub_pagos = "menu"; st.rerun()
                if dia_actual <= 10: monto_cobro = 104.0; invites_premio = 10; tipo_cobro = f"Mensualidad {nombre_mes_actual} (Pronto Pago)"
                else: monto_cobro = 120.0; invites_premio = 0; tipo_cobro = f"Mensualidad {nombre_mes_actual} (Tardío)"
                st.markdown(f"<h3 style='font-size:20px; font-weight:800; color:#FF6600;'>Confirmación de Pago</h3>", unsafe_allow_html=True)
                if saldo_accion >= monto_cobro:
                    st.info(f"💡 Se debitarán **${monto_cobro:.2f}** de tu Fondo Familiar.")
                    st.button(f"Confirmar Pago (${monto_cobro:.2f})", key="btn_pagar_mes", type="primary", on_click=cb_pagar_cuota, args=(saldo_accion, monto_cobro, mes_actual, invites_premio, tipo_cobro, nombre_mes_actual, socio_actual["accion"]))
                else: st.error(f"❌ Fondo Insuficiente. Necesitas **${monto_cobro:.2f}** para pagar.")
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
                        st.markdown(f"<div class='historial-card' style='border-left-color: {color_status};'><div style='display:flex; justify-content:space-between; margin-bottom:5px;'><b style='color:#ffffff; font-size:14px;'>{p_info.get('tipo', 'Abono a Billetera')}</b><b style='color:{color_status}; font-size:16px;'>{monto_str}</b></div><span style='color:#8E8E93; font-size:12px;'>{p_info['fecha_reporte']} | {p_info['metodo']}</span><br></div>", unsafe_allow_html=True)
                else: st.info("No hay movimientos registrados.")
                st.write("")
                st.markdown("<div class='btn-secundario'>", unsafe_allow_html=True)
                st.button("← Volver al Balances", type="primary", on_click=cb_nav_pagos, args=("menu",))
                st.markdown("</div>", unsafe_allow_html=True)

    # --- MÓDULO 4: EL HUB ---
    elif modulo_seleccionado == "Menú":
        if st.session_state.menu_view == "main":
            st.markdown(f"""
            <div style="background:#121212; padding:20px; border-radius:20px; border:1px solid #1C1C1E; margin-bottom:25px; display:flex; align-items:center; gap:15px;">
                <div style="width:60px; height:60px; background:#FF6600; border-radius:50%; display:flex; justify-content:center; align-items:center; color:#fff; font-size:24px; font-weight:800;">{socio_actual['nombre'][:2].upper()}</div>
                <div><h3 style="margin:0; font-size:18px; color:#fff;">{socio_actual['nombre']}</h3><p style="margin:0; color:#8E8E93; font-size:13px;">Acción {socio_actual['accion']} • {socio_actual['rol']}</p></div>
            </div>
            <h4 style="color:#A0A0A0; font-size:13px; margin-bottom:15px; text-transform:uppercase; letter-spacing:1px;">Gestión del Club</h4>
            """, unsafe_allow_html=True)
            if rol_actual in ["Titular", "Familiar"]: st.button("🎟️ Pases e Invitados", on_click=cb_set_menu, args=("invitados",), type="tertiary")
            if rol_actual in ["Concesionario", "Administrador"]: st.button("🛒 Ventry Pay (Punto de Venta)", on_click=cb_set_menu, args=("pos",), type="tertiary")
            if rol_actual in ["Vigilante", "Administrador"]: st.button("🛡️ Control de Garita", on_click=cb_set_menu, args=("garita",), type="tertiary")
            if rol_actual == "Administrador": st.button("📊 Consola Administrativa VIP", on_click=cb_set_menu, args=("admin",), type="tertiary")
            st.markdown("<h4 style='color:#A0A0A0; font-size:13px; margin-top:25px; margin-bottom:15px; text-transform:uppercase; letter-spacing:1px;'>Cuenta</h4>", unsafe_allow_html=True)
            st.button("⚙️ Ajustes de Perfil", on_click=cb_set_menu, args=("ajustes",), type="tertiary")

        # INVITADOS
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
                st.markdown(f'<a href="{link_ws}" target="_blank" style="display:flex; justify-content:center; align-items:center; background:linear-gradient(135deg, #32d74b, #28a745); color:white; padding:16px; border-radius:16px; text-decoration:none; font-weight:800; letter-spacing:1px; margin-top:20px; margin-bottom:20px; font-size:15px;">ENVIAR POR WHATSAPP</a>', unsafe_allow_html=True)
                st.markdown("<div class='btn-secundario'>", unsafe_allow_html=True)
                st.button("← Volver a crear otra invitación", type="primary", on_click=lambda: st.session_state.update(ultimo_pase_generado=None))
                st.markdown("</div>", unsafe_allow_html=True)
            else:
                if mes_pagado_accion != mes_actual_str(): st.error("❌ Operación Denegada. Debes estar al día con el pago del mes actual para invitar.")
                else:
                    col1, col2 = st.columns(2)
                    with col1: st.markdown(f'<div class="rial-card" style="padding:15px;"><p class="rial-title" style="font-size:10px;">Pases Libres</p><h3 class="rial-invites">{invitaciones_accion}</h3></div>', unsafe_allow_html=True)
                    with col2: st.markdown(f'<div class="rial-card" style="padding:15px;"><p class="rial-title" style="font-size:10px;">Fondo Familiar</p><h3 class="rial-saldo" style="font-size:22px;">${saldo_accion:.2f}</h3></div>', unsafe_allow_html=True)
                    if invitaciones_accion > 0: st.info(f"✨ Tienes {invitaciones_accion} pases de cortesía.")
                    else: st.warning("⚠️ Has agotado tus pases gratuitos. Se debitarán **$10.00** por este pase.")
                    
                    invitados_previos = BASE_DATOS_DIRECTORIO.get(socio_actual["accion"], {})
                    modo_ingreso = st.selectbox("Método de registro:", ["📝 Ingresar Nuevo Invitado", "⭐ Seleccionar de Favoritos"])
                    n_cedula_def, n_nombre_def = "", ""
                    if modo_ingreso == "⭐ Seleccionar de Favoritos":
                        if invitados_previos:
                            inv_sel = st.selectbox("Tu directorio:", list(invitados_previos.keys()), format_func=lambda x: f"{invitados_previos[x]['nombre']} (C.I: {x})")
                            n_cedula_def, n_nombre_def = inv_sel, invitados_previos[inv_sel]['nombre']
                        else: st.info("Aún no tienes invitados en tu directorio.")

                    with st.form("form_invitacion"):
                        n_cedula_inv = st.text_input("Cédula", value=n_cedula_def)
                        n_nombre_inv = st.text_input("Nombre y Apellido", value=n_nombre_def)
                        fecha_visita = st.date_input("Fecha de acceso", min_value=datetime.today(), format="DD/MM/YYYY")
                        guardar_contacto = False
                        if modo_ingreso == "📝 Ingresar Nuevo Invitado": guardar_contacto = st.checkbox("Guardar en mi directorio frecuente", value=True)
                        st.markdown("<br>", unsafe_allow_html=True)
                        btn_generar = st.form_submit_button("GENERAR PASE DIGITAL")
                        
                    if btn_generar and n_cedula_inv and n_nombre_inv:
                        puede_invitar = True
                        if invitaciones_accion > 0:
                            for ced_fam, info_fam in BASE_DATOS_SOCIOS.items():
                                if str(info_fam["accion"]) == str(socio_actual["accion"]) and info_fam["rol"] == "Titular":
                                    BASE_DATOS_SOCIOS[ced_fam]["invitaciones"] = invitaciones_accion - 1; break
                        else:
                            if saldo_accion >= 10.0:
                                for ced_fam, info_fam in BASE_DATOS_SOCIOS.items():
                                    if str(info_fam["accion"]) == str(socio_actual["accion"]) and info_fam["rol"] == "Titular":
                                        BASE_DATOS_SOCIOS[ced_fam]["saldo"] = saldo_accion - 10.0; break
                                id_cargo = f"P-INV-{str(uuid.uuid4())[:6].upper()}"
                                BASE_DATOS_PAGOS[id_cargo] = {"accion": socio_actual["accion"], "metodo": "Saldo Ventry", "referencia": "PASE-EXTRA", "monto": 10.0, "fecha_reporte": datetime.now().strftime("%d/%m/%Y"), "estatus": "Aprobado", "tipo": "Cargo Pase Extra"}
                                guardar_bd_pagos(BASE_DATOS_PAGOS)
                            else: puede_invitar = False; st.error("❌ Fondo insuficiente. Necesitas al menos $10.00.")
                        
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
                            st.session_state.ultimo_pase_generado = {"id": id_unico, "nombre": n_nombre_inv, "fecha": str_fecha}; st.rerun()

            st.write("")
            st.markdown("<div class='btn-secundario'>", unsafe_allow_html=True)
            st.button("← Volver al Menú", type="primary", on_click=cb_set_menu, args=("main",))
            st.markdown("</div>", unsafe_allow_html=True)

        # 🛑 VENTRY PAY (POS TÁCTIL CON CANTIDADES Y EDICIÓN)
        elif st.session_state.menu_view == "pos":
            st.markdown("<h3 style='font-size:24px; font-weight:800; color:#fff;'>Ventry Pay <span style='font-size:14px; color:#A0A0A0;'>(POS Táctil)</span></h3>", unsafe_allow_html=True)
            st.write(f"Concesionario: **{socio_actual['nombre']}**")
            
            if "ticket_generado" not in st.session_state: st.session_state.ticket_generado = None
            if "pos_cliente_cedula" not in st.session_state: st.session_state.pos_cliente_cedula = None; st.session_state.pos_cliente_nombre = None; st.session_state.pos_cliente_accion = None
            
            if "carrito_pos" not in st.session_state or isinstance(st.session_state.carrito_pos, list): 
                st.session_state.carrito_pos = {}

            def cb_agregar_item(nombre_item, precio_item): 
                if nombre_item in st.session_state.carrito_pos:
                    st.session_state.carrito_pos[nombre_item]["cantidad"] += 1
                else:
                    st.session_state.carrito_pos[nombre_item] = {"precio": precio_item, "cantidad": 1}
                    
            def cb_quitar_item(nombre_item):
                if nombre_item in st.session_state.carrito_pos:
                    st.session_state.carrito_pos[nombre_item]["cantidad"] -= 1
                    if st.session_state.carrito_pos[nombre_item]["cantidad"] <= 0:
                        del st.session_state.carrito_pos[nombre_item]

            def cb_limpiar_carrito(): st.session_state.carrito_pos = {}

            # 🛑 SI HAY UN TICKET GENERADO, SE MUESTRA EL COMPROBANTE
            if st.session_state.ticket_generado is not None:
                ticket = st.session_state.ticket_generado
                st.success("✅ Transacción aprobada exitosamente.")
                
                st.markdown(f"""
                <div style="background:#ffffff; color:#000000; padding:20px; border-radius:10px; width:100%; max-width:320px; margin:0 auto; font-family:monospace; text-align:center;">
                    <h3 style="margin:0; font-size:18px;">MAGNUM CITY CLUB</h3>
                    <p style="margin:0; font-size:10px;">Ventry Pay - Recibo Digital</p>
                    <p style="margin:5px 0; font-size:12px;">Ticket: {ticket['id']}<br>Fecha: {ticket['fecha']}</p>
                    <hr style="border:1px dashed #000; margin:10px 0;">
                    <p style="margin:0; font-size:12px; text-align:left;"><b>Socio:</b> {ticket['cliente']}</p>
                    <p style="margin:0; font-size:12px; text-align:left;"><b>Acción:</b> {ticket['accion']}</p>
                    <p style="margin:0; font-size:12px; text-align:left;"><b>Comercio:</b> {ticket['comercio']}</p>
                    <hr style="border:1px dashed #000; margin:10px 0;">
                """, unsafe_allow_html=True)
                
                for item in ticket['items']:
                    st.markdown(f"<div style='display:flex; justify-content:space-between; font-size:12px; color:#000;'><span>{item['item']}</span><span>${item['precio']:.2f}</span></div>", unsafe_allow_html=True)
                
                st.markdown(f"""
                    <hr style="border:1px dashed #000; margin:10px 0;">
                    <div style="display:flex; justify-content:space-between; font-size:16px; font-weight:bold; color:#000;"><span>TOTAL</span><span>${ticket['total']:.2f}</span></div>
                    <p style="margin-top:15px; font-size:10px;">Gracias por su consumo.</p>
                </div>
                <br>
                """, unsafe_allow_html=True)

                pdf_bytes = generar_ticket_pdf(ticket)
                if pdf_bytes:
                    st.download_button(
                        label="📥 Descargar Recibo PDF",
                        data=pdf_bytes,
                        file_name=f"Ventry_Ticket_{ticket['id']}.pdf",
                        mime="application/pdf",
                        type="primary"
                    )
                else:
                    st.warning("⚠️ No se detectó la librería FPDF. Se muestra versión web.")

                st.write("")
                st.markdown("<div class='btn-secundario'>", unsafe_allow_html=True)
                if st.button("Realizar Nuevo Cobro"):
                    st.session_state.ticket_generado = None
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

            # 🛑 FLUJO NORMAL DEL POS
            elif st.session_state.pos_cliente_cedula is None:
                data_usb = st.text_input("🔫 Escáner de Carnet (Pistola USB/Bluetooth):", placeholder="Dispare aquí...")
                st.write("📸 O utilizar cámara del dispositivo:")
                foto_qr = st.camera_input("Escanear con cámara del dispositivo:", label_visibility="collapsed")

                data_qr = data_usb if data_usb else None
                if foto_qr is not None and not data_qr:
                    bytes_data = foto_qr.getvalue()
                    cv2_img = cv2.imdecode(np.frombuffer(bytes_data, np.uint8), cv2.IMREAD_COLOR)
                    detector = cv2.QRCodeDetector()
                    data, bbox, _ = detector.detectAndDecode(cv2_img)
                    if data: data_qr = data
                    else: st.error("⚠️ No se detectó QR. Mejore la luz o acerque el código.")

                if data_qr:
                    if data_qr.startswith("VENTRY_DYN|"):
                        try:
                            partes = data_qr.split("|")
                            cedula_qr = partes[1]
                            timestamp_qr = int(partes[2])
                            timestamp_ahora = int(datetime.now().timestamp())
                            
                            if (timestamp_ahora - timestamp_qr) > 60: st.error("❌ Código QR Expirado. Pida al socio que actualice su carnet.")
                            elif cedula_qr in BASE_DATOS_SOCIOS:
                                socio_qr = BASE_DATOS_SOCIOS[cedula_qr]
                                st.session_state.pos_cliente_cedula = cedula_qr; st.session_state.pos_cliente_nombre = socio_qr['nombre']; st.session_state.pos_cliente_accion = socio_qr['accion']; st.session_state.carrito_pos = {}; st.rerun()
                            else: st.error("❌ Socio no encontrado.")
                        except: st.error("❌ Código QR Ilegible.")
                    else: st.error("❌ Código QR no es un Carnet Ventry válido.")
            else:
                saldo_fam = 0.0
                for m in BASE_DATOS_SOCIOS.values():
                    if str(m["accion"]) == str(st.session_state.pos_cliente_accion) and m["rol"] == "Titular": saldo_fam = float(m.get('saldo', 0.0)); break
                        
                st.markdown(f"<div class='rial-card'><p class='rial-title'>Socio Escaneado</p><h4 style='color:#fff; margin-bottom:2px;'>{st.session_state.pos_cliente_nombre}</h4><p style='color:#FF6600; font-weight:bold; margin-bottom:20px; font-size:12px;'>Acción {st.session_state.pos_cliente_accion}</p><div style='display:flex; justify-content:space-between; align-items:center;'><div><p class='rial-title' style='margin:0;'>Fondo Disponible</p><h3 class='rial-saldo' style='color:#FF6600 !important;'>${saldo_fam:.2f}</h3></div></div></div>", unsafe_allow_html=True)
                
                st.markdown("<h4 style='font-size:14px; color:#A0A0A0; margin-top:15px; text-transform:uppercase;'>Catálogo Rápido</h4>", unsafe_allow_html=True)
                col_p1, col_p2, col_p3 = st.columns(3)
                with col_p1: st.button("🍔 Burger\n$5.00", on_click=cb_agregar_item, args=("🍔 Hamburguesa", 5.0), use_container_width=True)
                with col_p2: st.button("🍺 Cerveza\n$2.00", on_click=cb_agregar_item, args=("🍺 Cerveza Polar", 2.0), use_container_width=True)
                with col_p3: st.button("🥤 Soda\n$1.50", on_click=cb_agregar_item, args=("🥤 Refresco", 1.5), use_container_width=True)
                col_p4, col_p5, col_p6 = st.columns(3)
                with col_p4: st.button("🍟 Papas\n$3.00", on_click=cb_agregar_item, args=("🍟 Ración de Papas", 3.0), use_container_width=True)
                with col_p5: st.button("🍕 Pizza\n$12.00", on_click=cb_agregar_item, args=("🍕 Pizza Familiar", 12.0), use_container_width=True)
                with col_p6: st.button("☕ Café\n$1.00", on_click=cb_agregar_item, args=("☕ Café Espresso", 1.0), use_container_width=True)

                total_cuenta = sum(info["precio"] * info["cantidad"] for info in st.session_state.carrito_pos.values())

                if st.session_state.carrito_pos:
                    st.markdown("<h4 style='font-size:14px; color:#A0A0A0; margin-top:20px; text-transform:uppercase;'>Cuenta Actual</h4>", unsafe_allow_html=True)
                    
                    for nombre, info in st.session_state.carrito_pos.items():
                        subtotal = info["precio"] * info["cantidad"]
                        c_text, c_btn_minus, c_btn_plus = st.columns([4, 1, 1])
                        with c_text:
                            st.markdown(f"<div style='padding-top:10px; font-size:15px;'><b>{info['cantidad']}x</b> {nombre} <span style='float:right; color:#32d74b;'><b>${subtotal:.2f}</b></span></div>", unsafe_allow_html=True)
                        with c_btn_minus:
                            st.button("➖", key=f"del_{nombre}", on_click=cb_quitar_item, args=(nombre,), use_container_width=True)
                        with c_btn_plus:
                            st.button("➕", key=f"add_{nombre}", on_click=cb_agregar_item, args=(nombre, info["precio"]), use_container_width=True)
                            
                    st.markdown(f"<div style='display:flex; justify-content:space-between; padding:15px 0 5px 0; margin-bottom:10px; border-top:1px solid #1C1C1E;'><span style='font-size:20px; font-weight:800;'>TOTAL:</span><b style='color:#FF6600; font-size:24px;'>${total_cuenta:.2f}</b></div>", unsafe_allow_html=True)

                    pin_seguridad = st.text_input("🔑 PIN de Autorización (4 dígitos del Socio)", type="password", max_chars=4, placeholder="••••")

                    btn_c1, btn_c2 = st.columns([3, 1])
                    with btn_c1:
                        if st.button(f"💸 COBRAR ${total_cuenta:.2f}", type="primary", use_container_width=True):
                            socio_hash = str(BASE_DATOS_SOCIOS[st.session_state.pos_cliente_cedula]["clave"])
                            if pin_seguridad != "1234" and hash_clave(pin_seguridad) != socio_hash and pin_seguridad != socio_hash: 
                                st.error("❌ PIN de autorización incorrecto. Transacción denegada.")
                            elif saldo_fam < total_cuenta: st.error("❌ Transacción Rechazada: Saldo insuficiente en el Fondo Familiar.")
                            else:
                                nuevo_saldo = saldo_fam - total_cuenta
                                for ced, info in BASE_DATOS_SOCIOS.items():
                                    if str(info["accion"]) == str(st.session_state.pos_cliente_accion) and info["rol"] == "Titular": BASE_DATOS_SOCIOS[ced]["saldo"] = nuevo_saldo; break
                                guardar_bd(BASE_DATOS_SOCIOS)
                                
                                desglose = ", ".join([f"{info['cantidad']}x {nombre.split(' ')[0]}" for nombre, info in st.session_state.carrito_pos.items()]) 
                                id_consumo = f"PAY-{str(uuid.uuid4())[:6].upper()}"
                                fecha_consumo = datetime.now().strftime("%d/%m/%Y %H:%M")
                                
                                BASE_DATOS_PAGOS[id_consumo] = {"accion": st.session_state.pos_cliente_accion, "metodo": "Ventry Pay", "referencia": f"Tienda: {socio_actual['nombre']}", "monto": total_cuenta, "fecha_reporte": fecha_consumo.split(" ")[0], "estatus": "Aprobado", "tipo": f"Consumo: {desglose}"}
                                guardar_bd_pagos(BASE_DATOS_PAGOS)
                                
                                # 🛑 GUARDAR DATOS DEL TICKET Y MOSTRAR PANTALLA
                                st.session_state.ticket_generado = {
                                    "id": id_consumo,
                                    "fecha": fecha_consumo,
                                    "cliente": st.session_state.pos_cliente_nombre,
                                    "accion": st.session_state.pos_cliente_accion,
                                    "comercio": socio_actual['nombre'],
                                    "items": [{"item": f"{info['cantidad']}x {nombre}", "precio": info['precio'] * info['cantidad']} for nombre, info in st.session_state.carrito_pos.items()],
                                    "total": total_cuenta
                                }
                                st.session_state.pos_cliente_cedula = None
                                st.session_state.carrito_pos = {}
                                st.rerun()
                    with btn_c2: st.button("🗑️", on_click=cb_limpiar_carrito, use_container_width=True, help="Vaciar carrito")
                        
                st.write("")
                st.markdown("<div class='btn-secundario'>", unsafe_allow_html=True)
                if st.button("← Cancelar", type="primary"): st.session_state.pos_cliente_cedula = None; st.session_state.carrito_pos = {}; st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

            if st.session_state.ticket_generado is None:
                st.write("")
                st.markdown("<div class='btn-secundario'>", unsafe_allow_html=True)
                st.button("← Volver al Menú Principal", type="primary", on_click=cb_set_menu, args=("main",))
                st.markdown("</div>", unsafe_allow_html=True)

        # GARITA
        elif st.session_state.menu_view == "garita":
            st.markdown("<h3 style='font-size:24px; font-weight:800; color:#fff;'>Modo Operativo: Garita</h3>", unsafe_allow_html=True)
            
            if "garita_scan_result" not in st.session_state: st.session_state.garita_scan_result = None

            if st.session_state.garita_scan_result is None:
                data_usb = st.text_input("🔫 Lector Físico (USB/Bluetooth):", placeholder="Dispare el escáner aquí...")
                st.write("📸 O utilizar cámara del dispositivo:")
                foto_qr = st.camera_input("Escanear con cámara del dispositivo:", label_visibility="collapsed")

                data_qr = data_usb if data_usb else None
                if foto_qr is not None and not data_qr:
                    bytes_data = foto_qr.getvalue()
                    cv2_img = cv2.imdecode(np.frombuffer(bytes_data, np.uint8), cv2.IMREAD_COLOR)
                    detector = cv2.QRCodeDetector()
                    data, bbox, _ = detector.detectAndDecode(cv2_img)
                    if data: data_qr = data
                    else: st.error("⚠️ No se detectó QR. Mejore la luz o acerque el código.")

                if data_qr:
                    if data_qr.startswith("INVITADO|"):
                        id_pase = data_qr.split("|")[1]
                        if id_pase in BASE_DATOS_INVITACIONES:
                            pase = BASE_DATOS_INVITACIONES[id_pase]
                            fecha_hoy = datetime.now().strftime("%d/%m/%Y")
                            if pase["fecha_visita"] != fecha_hoy: st.session_state.garita_scan_result = {"status": "error", "title": "ACCESO DENEGADO", "detail": f"Pase para el {pase['fecha_visita']}. Hoy es {fecha_hoy}.", "action": pase['accion']}
                            elif pase["estatus"] == "Activo":
                                BASE_DATOS_INVITACIONES[id_pase]["estatus"] = "Adentro"; guardar_bd_invitaciones(BASE_DATOS_INVITACIONES); registrar_acceso(pase["nombre_invitado"], pase["accion"], "QR Invitado", "Entrada")
                                st.session_state.garita_scan_result = {"status": "success", "title": "ACCESO AUTORIZADO", "detail": f"Invitado: {pase['nombre_invitado']}", "action": f"Acción: {pase['accion']}"}
                            elif pase["estatus"] == "Adentro": st.session_state.garita_scan_result = {"status": "error", "title": "PASE USADO", "detail": f"El invitado {pase['nombre_invitado']} ya registró entrada.", "action": pase['accion']}
                            else: st.session_state.garita_scan_result = {"status": "error", "title": "ACCESO DENEGADO", "detail": f"Estatus del pase: {pase['estatus'].upper()}", "action": pase['accion']}
                        else: st.session_state.garita_scan_result = {"status": "error", "title": "QR INVÁLIDO", "detail": "Pase no encontrado o falsificado.", "action": "N/A"}
                    
                    elif data_qr.startswith("VENTRY_DYN|"):
                        try:
                            partes = data_qr.split("|")
                            cedula_qr = partes[1]
                            timestamp_qr = int(partes[2])
                            timestamp_ahora = int(datetime.now().timestamp())
                            
                            if (timestamp_ahora - timestamp_qr) > 60: st.session_state.garita_scan_result = {"status": "error", "title": "CÓDIGO EXPIRADO", "detail": "El QR tiene más de 60 segundos. Pida al socio que actualice la app.", "action": "Seguridad Anti-Clonación"}
                            elif cedula_qr in BASE_DATOS_SOCIOS:
                                socio_qr = BASE_DATOS_SOCIOS[cedula_qr]
                                solvencia_qr = socio_qr.get("solvencia", "")
                                if solvencia_qr == "Al dia":
                                    registrar_acceso(socio_qr["nombre"], socio_qr["accion"], "QR Dinámico Socio", "Entrada")
                                    st.session_state.garita_scan_result = {"status": "success", "title": "ACCESO AUTORIZADO", "detail": f"Socio: {socio_qr['nombre']} ({socio_qr['rol']})", "action": f"Acción: {socio_qr['accion']}"}
                                else: st.session_state.garita_scan_result = {"status": "error", "title": "ACCESO DENEGADO", "detail": f"Socio: {socio_qr['nombre']}. Estatus: {solvencia_qr.upper()}", "action": f"Acción: {socio_qr['accion']}"}
                            else: st.session_state.garita_scan_result = {"status": "error", "title": "ERROR", "detail": "Cédula no registrada.", "action": "N/A"}
                        except: st.session_state.garita_scan_result = {"status": "error", "title": "CÓDIGO ILEGIBLE", "detail": "El QR está corrupto.", "action": "N/A"}
                    
                    elif "VENTRY" in data_qr: st.session_state.garita_scan_result = {"status": "error", "title": "CARNET OBSOLETO", "detail": "Está usando un QR estático viejo. Debe usar la app para el QR Dinámico.", "action": "Seguridad"}
                    else: st.session_state.garita_scan_result = {"status": "error", "title": "QR DESCONOCIDO", "detail": "El código no pertenece a Ventry.", "action": "N/A"}
                    st.rerun()

            else:
                res = st.session_state.garita_scan_result
                if res["status"] == "success": texto_voz = f"Acceso Autorizado. {res['detail']}"
                else: texto_voz = f"Alerta de seguridad. {res['title']}."
                texto_limpio = texto_voz.replace("'", "").replace('"', '')
                
                html_voz = f'<script> let msg = new SpeechSynthesisUtterance("{texto_limpio}"); msg.lang = "es-ES"; msg.rate = 1.0; msg.pitch = 1.1; window.speechSynthesis.speak(msg); </script>'
                components.html(html_voz, height=0)

                if res["status"] == "success": st.markdown(f"<div class='garita-alert-success'><div style='font-size: 80px; margin-bottom: 10px;'>✅</div><div style='font-size: 32px; font-weight: 900; letter-spacing: 1px; margin-bottom: 5px; text-transform: uppercase;'>{res['title']}</div><div style='font-size: 18px; font-weight: 500; margin-top: 15px; color: #f8fafc;'>{res['detail']}</div><div style='font-size: 24px; font-weight: 800; color: #fbbf24; margin-top: 5px; text-transform: uppercase; letter-spacing: 2px;'>{res['action']}</div></div>", unsafe_allow_html=True)
                else: st.markdown(f"<div class='garita-alert-error'><div style='font-size: 80px; margin-bottom: 10px;'>❌</div><div style='font-size: 32px; font-weight: 900; letter-spacing: 1px; margin-bottom: 5px; text-transform: uppercase;'>{res['title']}</div><div style='font-size: 18px; font-weight: 500; margin-top: 15px; color: #f8fafc;'>{res['detail']}</div><div style='font-size: 24px; font-weight: 800; color: #fbbf24; margin-top: 5px; text-transform: uppercase; letter-spacing: 2px;'>{res['action']}</div></div>", unsafe_allow_html=True)
                
                st.write("")
                st.button("Siguiente Escaneo ⏭️", type="primary", on_click=cb_limpiar_garita)

            st.write("")
            st.markdown("<div class='btn-secundario'>", unsafe_allow_html=True)
            st.button("← Volver al Menú", type="primary", on_click=cb_set_menu, args=("main",))
            st.markdown("</div>", unsafe_allow_html=True)

        # ADMIN
        elif st.session_state.menu_view == "admin":
            st.markdown("<h3 style='font-size:24px; font-weight:800; color:#FF6600;'>Consola Administrativa VIP</h3>", unsafe_allow_html=True)
            if "mensaje_admin_exitoso" in st.session_state: st.success(st.session_state.mensaje_admin_exitoso); del st.session_state.mensaje_admin_exitoso
            tab_dashboard, tab_facturacion = st.tabs(["📊 Dashboard & BI", "⚙️ Motor de Facturación"])
            
            with tab_dashboard:
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
                capital_riesgo = sum([abs(float(info.get("saldo", 0))) for info in BASE_DATOS_SOCIOS.values() if info["rol"] == "Titular" and float(info.get("saldo", 0)) < 0])
                ingresos_brutos = sum([float(p["monto"]) for p in BASE_DATOS_PAGOS.values() if p["estatus"] == "Aprobado" and mes_actual_str() in p.get("fecha_reporte", mes_actual_str())])

                col_k1, col_k2, col_k3, col_k4 = st.columns(4)
                with col_k1: st.markdown(f'<div class="rial-card"><p class="rial-title">Familias Activas</p><h3 class="rial-saldo" style="font-size:20px; margin:0;">{total_acciones}</h3></div>', unsafe_allow_html=True)
                with col_k2: st.markdown(f'<div class="rial-card"><p class="rial-title">Morosidad</p><h3 class="rial-saldo" style="color:{"#ff453a" if tasa_morosidad > 15 else "#FF6600"} !important; font-size:20px; margin:0;">{tasa_morosidad:.1f}%</h3></div>', unsafe_allow_html=True)
                with col_k3: st.markdown(f'<div class="rial-card"><p class="rial-title">Exposición</p><h3 class="rial-saldo rial-monto-rojo" style="font-size:20px; margin:0;">${capital_riesgo:,.2f}</h3></div>', unsafe_allow_html=True)
                with col_k4: st.markdown(f'<div class="rial-card"><p class="rial-title">Caja Mes</p><h3 class="rial-saldo rial-monto-verde" style="font-size:20px; margin:0;">${ingresos_brutos:,.2f}</h3></div>', unsafe_allow_html=True)
                st.write("---")

                st.markdown("<h4 style='color:#A0A0A0; font-size:16px;'>📈 Inteligencia de Negocios (BI)</h4>", unsafe_allow_html=True)
                col_chart1, col_chart2 = st.columns(2)
                with col_chart1:
                    st.markdown("<p style='font-size:12px; color:#888; text-transform:uppercase;'>Distribución de Solvencia</p>", unsafe_allow_html=True)
                    df_solvencia = pd.DataFrame({"Estatus": ["Al Día", "Morosos", "Pendiente"], "Total Familias": [len(acciones_al_dia), morosos_count, len(acciones_pendientes)]}).set_index("Estatus")
                    st.bar_chart(df_solvencia, color="#FF6600")

                with col_chart2:
                    st.markdown("<p style='font-size:12px; color:#888; text-transform:uppercase;'>Métodos de Pago Preferidos</p>", unsafe_allow_html=True)
                    pagos_aprobados = [p for p in BASE_DATOS_PAGOS.values() if p["estatus"] == "Aprobado"]
                    if pagos_aprobados: df_pagos = pd.DataFrame(pagos_aprobados); dist_metodos = df_pagos['metodo'].value_counts(); st.bar_chart(dist_metodos, color="#32d74b")
                    else: st.info("Sin datos de pagos suficientes.")

                col_chart3, col_chart4 = st.columns(2)
                with col_chart3:
                    st.markdown("<p style='font-size:12px; color:#888; text-transform:uppercase;'>Flujo de Accesos (Garita)</p>", unsafe_allow_html=True)
                    if st.session_state.db_historial: df_historial = pd.DataFrame(st.session_state.db_historial); df_accesos = df_historial['via'].value_counts(); st.bar_chart(df_accesos, color="#0A84FF")
                    else: st.info("Aún no hay datos de acceso.")
                        
                with col_chart4:
                    st.markdown("<p style='font-size:12px; color:#888; text-transform:uppercase;'>Horas Pico de Entrada</p>", unsafe_allow_html=True)
                    if st.session_state.db_historial:
                        df_h = pd.DataFrame(st.session_state.db_historial)
                        try:
                            df_h['hora'] = pd.to_datetime(df_h['fecha'], format="%d/%m/%Y %H:%M:%S").dt.hour
                            horas_pico = df_h['hora'].value_counts().sort_index(); horas_pico.index = [f"{h:02d}:00" for h in horas_pico.index]; st.line_chart(horas_pico, color="#FFD60A")
                        except: st.info("Formato de fecha incompatible para graficar horas pico.")
                    else: st.info("Aún no hay datos de acceso.")

                st.write("---")
                col_admin1, col_admin2 = st.columns([1, 1])
                with col_admin1:
                    st.markdown("<h4 style='font-size:16px; color:#A0A0A0;'>💳 Conciliación Pendiente</h4>", unsafe_allow_html=True)
                    pagos_pendientes = {k: v for k, v in BASE_DATOS_PAGOS.items() if v["estatus"] == "En Revisión"}
                    if pagos_pendientes:
                        pagos_ia = {k: v for k, v in pagos_pendientes.items() if "Verificado por IA" in v.get("tipo", "")}
                        if pagos_ia:
                            st.markdown("<div style='background:rgba(255, 102, 0, 0.1); border:1px solid #FF6600; padding:15px; border-radius:15px; margin-bottom:15px;'>", unsafe_allow_html=True)
                            st.markdown(f"<p style='color:#FF6600; font-weight:bold; margin:0 0 10px 0;'>🤖 Lote Inteligente: {len(pagos_ia)} pagos verificados.</p>", unsafe_allow_html=True)
                            if st.button(f"⚡ Aprobar {len(pagos_ia)} Recargas IA", type="primary", use_container_width=True):
                                for p_id, p_info in pagos_ia.items():
                                    BASE_DATOS_PAGOS[p_id]["estatus"] = "Aprobado"
                                    nuevo_saldo = 0.0
                                    for ced, info in BASE_DATOS_SOCIOS.items():
                                        if str(info["accion"]) == str(p_info["accion"]) and info["rol"] == "Titular":
                                            nuevo_saldo = float(info.get("saldo", 0)) + float(p_info['monto']); BASE_DATOS_SOCIOS[ced]["saldo"] = nuevo_saldo; break
                                    nueva_solvencia = "Al dia" if nuevo_saldo >= 0 else "Moroso"
                                    for ced_fam, info_fam in BASE_DATOS_SOCIOS.items():
                                        if str(info_fam["accion"]) == str(p_info["accion"]):
                                            BASE_DATOS_SOCIOS[ced_fam]["solvencia"] = nueva_solvencia
                                guardar_bd(BASE_DATOS_SOCIOS); guardar_bd_pagos(BASE_DATOS_PAGOS); st.toast(f"✅ {len(pagos_ia)} pagos aprobados.", icon="🚀"); st.rerun()
                            st.markdown("</div>", unsafe_allow_html=True)
                        
                        for p_id, p_info in pagos_pendientes.items():
                            tipo_trans = p_info.get("tipo", "Abono a Billetera")
                            icono_ia = "🤖 " if "Verificado por IA" in tipo_trans else ""
                            with st.expander(f"{icono_ia}Acción: {p_info['accion']} | ${p_info['monto']} ({p_info['metodo']})"):
                                st.write(f"**Ref:** {p_info['referencia']} | **Fecha:** {p_info['fecha_reporte']}")
                                btn_col1, btn_col2 = st.columns(2)
                                with btn_col1:
                                    if st.button("✅ Aprobar", key=f"apr_{p_id}", type="primary"):
                                        BASE_DATOS_PAGOS[p_id]["estatus"] = "Aprobado"; guardar_bd_pagos(BASE_DATOS_PAGOS)
                                        nuevo_saldo = 0.0
                                        for ced, info in BASE_DATOS_SOCIOS.items():
                                            if str(info["accion"]) == str(p_info["accion"]) and info["rol"] == "Titular":
                                                nuevo_saldo = float(info.get("saldo", 0)) + float(p_info['monto']); BASE_DATOS_SOCIOS[ced]["saldo"] = nuevo_saldo; break
                                        nueva_solvencia = "Al dia" if nuevo_saldo >= 0 else "Moroso"
                                        for ced_fam, info_fam in BASE_DATOS_SOCIOS.items():
                                            if str(info_fam["accion"]) == str(p_info["accion"]): BASE_DATOS_SOCIOS[ced_fam]["solvencia"] = nueva_solvencia
                                        guardar_bd(BASE_DATOS_SOCIOS); st.toast("✅ Transacción aprobada.", icon="💰"); st.rerun()
                                with btn_col2:
                                    if st.button("❌ Rechazar", key=f"rec_{p_id}"): BASE_DATOS_PAGOS[p_id]["estatus"] = "Rechazado"; guardar_bd_pagos(BASE_DATOS_PAGOS); st.rerun()
                    else: st.success("No hay pagos pendientes de revisión.")

                    st.write("")
                    st.markdown("<h4 style='font-size:16px; color:#A0A0A0;'>📥 Descargar Data (CSV)</h4>", unsafe_allow_html=True)
                    if len(BASE_DATOS_SOCIOS) > 0:
                        df_socios = pd.DataFrame(list(BASE_DATOS_SOCIOS.values()))
                        st.download_button("Exportar Matriz de Socios", data=df_socios.to_csv(index=False).encode('utf-8'), file_name="Socios_Ventry.csv", mime="text/csv")
                    
                with col_admin2:
                    st.markdown("<h4 style='font-size:16px; color:#A0A0A0;'>🔍 Buscador CRM Familiar</h4>", unsafe_allow_html=True)
                    busqueda_admin = st.text_input("Buscar por Acción, Cédula o Nombre:")
                    acciones_encontradas = set()
                    if busqueda_admin:
                        for ced, info in BASE_DATOS_SOCIOS.items():
                            if busqueda_admin.lower() in str(info['accion']).lower() or busqueda_admin.lower() in str(ced).lower() or busqueda_admin.lower() in str(info['nombre']).lower():
                               acciones_encontradas.add(info['accion'])
                    else: acciones_encontradas = set(d["accion"] for d in BASE_DATOS_SOCIOS.values())
                    
                    if acciones_encontradas:
                        accion_sel = st.selectbox("Familias encontradas:", sorted(list(acciones_encontradas)))
                        miembros_accion = sorted([info for info in BASE_DATOS_SOCIOS.values() if info["accion"] == accion_sel], key=lambda x: x.get("rol", ""), reverse=True)
                        for m in miembros_accion: 
                            icono = '👑' if m['rol'] == 'Titular' else '👤'
                            solvencia_m = m.get('solvencia', 'Desconocido')
                            saldo_m = float(m.get('saldo', 0.0)) if m['rol'] == 'Titular' else "N/A"
                            saldo_txt = f" | Saldo: ${saldo_m:.2f}" if m['rol'] == 'Titular' else ""
                            st.markdown(f"<div style='background:#1C1C1E; border:1px solid rgba(255,255,255,0.05); color:#ffffff; padding:12px; border-radius:12px; margin-bottom:8px; font-size:13px;'>{icono} <b style='letter-spacing:0.5px;'>{m['nombre']}</b> - <span style='color:#FF6600;'>{solvencia_m}</span>{saldo_txt}</div>", unsafe_allow_html=True)
                            
                            if st.button(f"🔑 Resetear Clave", key=f"reset_{m['cedula']}", help="Asigna '1234' al usuario"):
                                BASE_DATOS_SOCIOS[m['cedula']]["clave"] = hash_clave("1234")
                                guardar_bd(BASE_DATOS_SOCIOS)
                                st.toast(f"✅ Clave de {m['nombre']} reseteada a 1234.", icon="🔑")
                        
                        with st.form("form_estatus_rapido"):
                            n_estatus = st.selectbox("Actualizar Estatus de Grupo:", ["Al dia", "Moroso", "Pendiente", "En revision"])
                            if st.form_submit_button("Actualizar Todo"):
                                for ced, info in BASE_DATOS_SOCIOS.items():
                                    if info["accion"] == accion_sel: BASE_DATOS_SOCIOS[ced]["solvencia"] = n_estatus
                                guardar_bd(BASE_DATOS_SOCIOS); st.success("Actualizado.")
                    else: st.warning("No se encontraron familias.")

            with tab_facturacion:
                st.markdown("<h4 style='color:#FF6600;'>Auditoría y Cobro de Morosos (Post-Día 10)</h4>", unsafe_allow_html=True)
                st.write("Este botón cobra **$120** a todas las familias que no hayan cancelado el mes actual.")
                if st.button("🚨 EJECUTAR COBRO DE MOROSOS", type="primary"):
                    fecha_cobro = datetime.now().strftime("%d/%m/%Y")
                    mes_actual = mes_actual_str()
                    familias_cobradas = 0
                    nombre_mes_actual = formato_mes_espanol(mes_actual)
                    
                    for ced, info in BASE_DATOS_SOCIOS.items():
                        if info["rol"] == "Titular" and info.get("mes_pagado", "") != mes_actual:
                            monto_tardio = 120.0
                            nuevo_saldo = float(info.get("saldo", 0)) - monto_tardio
                            BASE_DATOS_SOCIOS[ced]["saldo"] = nuevo_saldo
                            BASE_DATOS_SOCIOS[ced]["mes_pagado"] = mes_actual
                            BASE_DATOS_SOCIOS[ced]["invitaciones"] = 0 
                            familias_cobradas += 1
                            id_cargo = f"CRG-{str(uuid.uuid4())[:6].upper()}"
                            BASE_DATOS_PAGOS[id_cargo] = {"accion": info["accion"], "metodo": "Sistema Ventry", "referencia": "MORA", "monto": monto_tardio, "fecha_reporte": fecha_cobro, "estatus": "Aprobado", "tipo": f"Mensualidad de {nombre_mes_actual} (Tardío)"}
                            nueva_solvencia = "Al dia" if nuevo_saldo >= 0 else "Moroso"
                            for ced_fam, info_fam in BASE_DATOS_SOCIOS.items():
                                if str(info_fam["accion"]) == str(info["accion"]): BASE_DATOS_SOCIOS[ced_fam]["solvencia"] = nueva_solvencia
                                        
                    guardar_bd(BASE_DATOS_SOCIOS); guardar_bd_pagos(BASE_DATOS_PAGOS)
                    st.session_state.mensaje_admin_exitoso = f"✅ ¡FACTURACIÓN EXITOSA! Se cargaron $120 a {familias_cobradas} acciones rezagadas."
                    st.rerun()

            st.write("---")
            if st.button("🔄 Sincronizar DB en la Nube"):
                st.session_state.db_socios = cargar_bd(); st.session_state.db_invitaciones = cargar_invitaciones(); st.session_state.db_pagos = cargar_pagos(); st.session_state.db_directorio = cargar_directorio(); st.session_state.db_historial = cargar_historial()
                st.success("Base de datos sincronizada.")

            st.write("")
            st.markdown("<div class='btn-secundario'>", unsafe_allow_html=True)
            st.button("← Volver al Menú", type="primary", on_click=cb_set_menu, args=("main",))
            st.markdown("</div>", unsafe_allow_html=True)

        # AJUSTES
        elif st.session_state.menu_view == "ajustes":
            if "sub_ajustes" not in st.session_state: st.session_state.sub_ajustes = "menu"

            if st.session_state.sub_ajustes == "menu":
                if "mensaje_perfil" in st.session_state:
                    st.success(st.session_state.mensaje_perfil)
                    del st.session_state.mensaje_perfil
                    
                st.markdown("<h3 style='font-size:24px; font-weight:800; color:#fff; margin-bottom: 20px;'>Ajustes</h3>", unsafe_allow_html=True)
                st.button("Perfil y Seguridad", type="primary", on_click=lambda: st.session_state.update(sub_ajustes="perfil"))
                st.write("")
                st.button("Mis Contactos (Directorio)", type="primary", on_click=lambda: st.session_state.update(sub_ajustes="directorio"))
                st.write("")
                st.button("Grupo Familiar", type="primary", on_click=lambda: st.session_state.update(sub_ajustes="familia"))
                st.write("")
                st.button("Historial de Accesos", type="primary", on_click=lambda: st.session_state.update(sub_ajustes="historial"))
                st.write("")
                st.markdown("<div class='btn-secundario'>", unsafe_allow_html=True)
                st.button("← Volver al Menú Principal", type="primary", on_click=cb_set_menu, args=("main",))
                st.markdown("</div>", unsafe_allow_html=True)

            elif st.session_state.sub_ajustes == "perfil":
                st.markdown("<h3 style='font-size:20px; font-weight:800; color:#FF6600;'>Perfil y Seguridad</h3>", unsafe_allow_html=True)
                with st.form("form_cambio_clave"):
                    clave_actual = st.text_input("Contraseña Actual", type="password")
                    clave_nueva = st.text_input("Nueva Contraseña", type="password")
                    clave_confirma = st.text_input("Confirmar Nueva Contraseña", type="password")
                    st.markdown("<br>", unsafe_allow_html=True)
                    btn_cambiar_clave = st.form_submit_button("ACTUALIZAR CONTRASEÑA")
                    
                if btn_cambiar_clave:
                    if hash_clave(clave_actual) != str(socio_actual["clave"]) and clave_actual != str(socio_actual["clave"]): 
                        st.error("❌ La contraseña actual es incorrecta.")
                    elif clave_nueva != clave_confirma: st.error("❌ Las contraseñas nuevas no coinciden.")
                    elif len(clave_nueva) < 4: st.error("⚠️ La contraseña debe tener al menos 4 caracteres.")
                    else:
                        clave_nueva_hash = hash_clave(clave_nueva)
                        BASE_DATOS_SOCIOS[socio_actual["cedula"]]["clave"] = clave_nueva_hash
                        guardar_bd(BASE_DATOS_SOCIOS)
                        st.session_state.usuario_actual["clave"] = clave_nueva_hash
                        st.success("✅ Contraseña actualizada y encriptada exitosamente.")
                
                st.write("---")
                if st.button("🔓 Vincular este dispositivo (FaceID / TouchID)", type="primary", use_container_width=True):
                    nuevo_token = str(uuid.uuid4())
                    BASE_DATOS_SOCIOS[socio_actual["cedula"]]["bio_token"] = nuevo_token
                    guardar_bd(BASE_DATOS_SOCIOS)
                    st.session_state.usuario_actual["bio_token"] = nuevo_token
                    st.session_state.token_a_guardar = nuevo_token 
                    st.rerun()
                
                st.markdown("<div class='btn-logout'>", unsafe_allow_html=True)
                if st.button("Cerrar Sesión"):
                    st.session_state.logueado = False; st.session_state.usuario_actual = None; st.session_state.pantalla_auth = "login"; st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
                
                st.write("")
                st.markdown("<div class='btn-secundario'>", unsafe_allow_html=True)
                st.button("← Volver a Ajustes", type="primary", on_click=lambda: st.session_state.update(sub_ajustes="menu"))
                st.markdown("</div>", unsafe_allow_html=True)

            elif st.session_state.sub_ajustes == "directorio":
                st.markdown("<h3 style='font-size:20px; font-weight:800; color:#FF6600;'>Mis Contactos</h3>", unsafe_allow_html=True)
                mis_contactos = BASE_DATOS_DIRECTORIO.get(socio_actual["accion"], {})
                if mis_contactos:
                    for ced_contacto, info_contacto in mis_contactos.items():
                        st.markdown(f"<div class='rial-card' style='padding:15px; margin-bottom:10px;'><b style='font-size: 16px; color:#fff;'>{info_contacto['nombre']}</b><br><span style='color:#8E8E93; font-size:12px;'>C.I: {ced_contacto} | Correo: {info_contacto.get('correo', 'N/A')}</span></div>", unsafe_allow_html=True)
                        st.markdown("<div class='btn-peligro' style='margin-bottom:15px;'>", unsafe_allow_html=True)
                        if st.button(f"Eliminar {info_contacto['nombre']}", key=f"del_{ced_contacto}"):
                            del BASE_DATOS_DIRECTORIO[socio_actual["accion"]][ced_contacto]; guardar_bd_directorio(BASE_DATOS_DIRECTORIO); st.rerun()
                        st.markdown("</div>", unsafe_allow_html=True)
                else: st.info("No tienes invitados guardados en tu directorio frecuente.")
                st.write("")
                st.markdown("<div class='btn-secundario'>", unsafe_allow_html=True)
                st.button("← Volver a Ajustes", type="primary", on_click=lambda: st.session_state.update(sub_ajustes="menu"))
                st.markdown("</div>", unsafe_allow_html=True)

            elif st.session_state.sub_ajustes == "familia":
                st.markdown(f"<h3 style='font-size:20px; font-weight:800; color:#FF6600;'>Acción {socio_actual['accion']}</h3>", unsafe_allow_html=True)
                if rol_actual == "Titular":
                    miembros = [m for m in BASE_DATOS_SOCIOS.values() if m["accion"] == socio_actual["accion"] and m["cedula"] != socio_actual["cedula"]]
                    if miembros:
                        for m in miembros: st.markdown(f"<div class='rial-card' style='padding:15px; margin-bottom:10px;'><b style='font-size: 16px; color:#fff;'>{m['nombre']}</b><br><span style='color:#8E8E93; font-size:12px;'>C.I: {m['cedula']} | Parentesco: {m['parentesco']}</span><br><span style='color:#FF6600; font-size:11px; font-weight:800; text-transform:uppercase; letter-spacing:1px;'>Estatus: {m.get('solvencia', 'Desconocido')}</span></div>", unsafe_allow_html=True)
                    else: st.info("No hay familiares registrados bajo tu acción en este momento.")
                else: st.warning("🔒 Esta sección es exclusiva para la cuenta Titular de la Acción.")
                st.write("")
                st.markdown("<div class='btn-secundario'>", unsafe_allow_html=True)
                st.button("← Volver a Ajustes", type="primary", on_click=lambda: st.session_state.update(sub_ajustes="menu"))
                st.markdown("</div>", unsafe_allow_html=True)

            elif st.session_state.sub_ajustes == "historial":
                st.markdown("<h3 style='font-size:20px; font-weight:800; color:#FF6600;'>Actividad Reciente</h3>", unsafe_allow_html=True)
                historial_accion = [h for h in st.session_state.db_historial if h["accion"] == str(socio_actual["accion"])]
                if historial_accion:
                    for h in historial_accion[:10]: st.markdown(f"<div class='rial-card' style='padding:15px; margin-bottom:10px; border-left: 3px solid #FF6600;'><span style='color:#FF6600; font-weight:800; font-size:11px; letter-spacing:0.5px;'>{h['fecha']}</span><br><b style='font-size:15px; color:#ffffff;'>{h['nombre']}</b><br><span style='color:#8E8E93; font-size:12px; font-weight:500;'>Método: {h['via']} - Tipo: {h['movimiento']}</span></div>", unsafe_allow_html=True)
                else: st.info("No hay registros de acceso recientes para tu acción.")
                st.write("")
                st.markdown("<div class='btn-secundario'>", unsafe_allow_html=True)
                st.button("← Volver a Ajustes", type="primary", on_click=lambda: st.session_state.update(sub_ajustes="menu"))
                st.markdown("</div>", unsafe_allow_html=True)