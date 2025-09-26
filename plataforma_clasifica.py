import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json

# Definición del Scope (como lo tienes)
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive", "https://docs.google.com/spreadsheets/d"]

# 🔒 NUEVA FORMA SEGURA DE CARGAR CREDENCIALES
# st.secrets["gcp_service_account"] devuelve el diccionario TOML (o JSON)
creds_dict = st.secrets["gcp_service_account"]

# Crea el objeto ServiceAccountCredentials usando el diccionario (no el nombre del archivo)
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)

# Autorizar gspread
client = gspread.authorize(creds)

# Abre la hoja de cálculo por su clave (ID)
SPREADSHEET_KEY = "1xwNlCNsIaUkW5t5W2ewLifbhRq86k79boUaL4f3DG9g"
spreadsheet = client.open_by_key(SPREADSHEET_KEY)
sheet = spreadsheet.sheet1

st.title("Clasificador PGD con almacenamiento")
# ...

texto = st.text_area("Escribe tu opinión o propuesta:")

if st.button("Clasificar y guardar"):
    if texto.strip():
        clasificacion = "Opinión" if "no estoy de acuerdo" in texto.lower() else "Propuesta"
        
        # Guarda en Google Sheets (añade nueva fila)
        sheet.append_row([texto, clasificacion])
        st.success(f"Clasificado como: {clasificacion} y guardado en Google Sheets")