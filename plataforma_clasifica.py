import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Autenticación con Google
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("pgd-clasificador-a4c4118c26a8.json", scope)
client = gspread.authorize(creds)

# Abre la hoja (usa la URL o el nombre)
sheet = client.open("textos_prueba").sheet1

# Interfaz
st.title("Clasificador PGD con almacenamiento")
texto = st.text_area("Escribe tu opinión o propuesta:")

if st.button("Clasificar y guardar"):
    if texto.strip():
        clasificacion = "Opinión" if "no estoy de acuerdo" in texto.lower() else "Propuesta"
        
        # Guarda en Google Sheets (añade nueva fila)
        sheet.append_row([texto, clasificacion])
        st.success(f"Clasificado como: {clasificacion} y guardado en Google Sheets")
