import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import joblib 
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
# Importante: se requiere 'display' para la función clasificar_texto, 
# pero no se usa en Streamlit. Reemplazaremos su uso.

# ==========================================================
# 1. CARGA DE MODELOS USANDO CACHE (Solo se cargan 1 vez)
# ==========================================================

@st.cache_resource
def load_all_models():
    """Carga todos los modelos y codificadores desde el disco."""
    try:
        # Cargar el modelo BERT (se descarga la primera vez)
        modelo_bert = SentenceTransformer('distiluse-base-multilingual-cased')
        
        # Cargar clasificadores y LabelEncoders
        clf_binario = joblib.load('clf_binario_tipo_texto.joblib')
        clf_ejes = joblib.load('clf_multiclase_ejes.joblib')
        le_binario = joblib.load('le_binario_tipo_texto.joblib')
        le_ejes = joblib.load('le_multiclase_ejes.joblib')
        
        return modelo_bert, clf_binario, le_binario, clf_ejes, le_ejes
    except FileNotFoundError as e:
        st.error(f"❌ Error al cargar archivos del modelo: {e}. Asegúrate de que los archivos .joblib están en el directorio correcto.")
        return None, None, None, None, None

# Cargar los recursos
modelo_bert, clf_binario, le_binario, clf_ejes, le_ejes = load_all_models()

# ==========================================================
# 2. FUNCIÓN DE CLASIFICACIÓN (Adaptada para Streamlit)
# ==========================================================

def clasificar_texto_avanzado(texto, modelo_bert, clf_binario, le_binario, clf_ejes, le_ejes, top_n=3):
    """Clasifica y devuelve un resumen del resultado para Streamlit."""
    
    # Si los modelos no se cargaron, salir
    if modelo_bert is None:
        return "Error de carga de modelos."

    # 1. Obtener embedding
    emb = modelo_bert.encode([texto])

    # 2. Predicción binaria (Opinión vs Propuesta)
    probas_bin = clf_binario.predict_proba(emb)[0]
    df_bin = pd.DataFrame({
        "tema": le_binario.inverse_transform(np.arange(len(probas_bin))),
        "probabilidad": probas_bin
    }).sort_values(by="probabilidad", ascending=False).reset_index(drop=True)

    clase_predicha = df_bin.loc[0, "tema"]
    prob_binaria = df_bin.loc[0, "probabilidad"]
    
    resumen = f"Clasificado como: **{clase_predicha.upper()}** (Probabilidad: {prob_binaria:.2f})"
    
    # 3. Si es Propuesta, predecir ejes
    if clase_predicha == "propuesta":
        probas_ejes = clf_ejes.predict_proba(emb)[0]
        top_idxs = np.argsort(probas_ejes)[::-1][:top_n]
        temas_top = le_ejes.inverse_transform(top_idxs)
        probs_top = probas_ejes[top_idxs]
        
        resumen += "\n\n**Ejes Potenciales:**\n"
        for tema, prob in zip(temas_top, probs_top):
            resumen += f"- {tema}: {prob:.2f}\n"
        
        # Usamos el eje más probable para Google Sheets
        clasificacion_final = temas_top[0]

    elif clase_predicha == "opinión":
        clasificacion_final = "Opinión" # O la etiqueta que uses en Sheets

    return clasificacion_final, resumen

# ==========================================================
# 3. LÓGICA DE LA APLICACIÓN
# ==========================================================

# ... Tu código de autenticación y gspread (st.secrets, client, etc.) va aquí ...

# Definición del Scope (ajustado a los correctos)
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

# ... (El resto de tu código de autenticación) ...
creds_dict = st.secrets["gcp_service_account"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)
# Abriendo por clave (método más robusto)
SPREADSHEET_KEY = "1xwNlCNsIaUkW5t5W2ewLifbhRq86k79boUaL4f3DG9g"
spreadsheet = client.open_by_key(SPREADSHEET_KEY)
sheet = spreadsheet.sheet1


st.title("Clasificador PGD con almacenamiento (v2.0)")
texto = st.text_area("Escribe tu opinión o propuesta:", height=150)

if st.button("Clasificar y guardar"):
    if not texto.strip():
        st.warning("Por favor, introduce texto para clasificar.")
    elif modelo_bert is None:
         st.error("No se pudo clasificar debido a errores de carga del modelo.")
    else:
        # Llamar a la función avanzada
        # clasificacion_para_sheets: Es la etiqueta final para la hoja (ej. "Ciudad segura...")
        # resumen_para_usuario: Es el texto completo con el resultado de la clasificación
        clasificacion_para_sheets, resumen_para_usuario = clasificar_texto_avanzado(
            texto=texto,
            modelo_bert=modelo_bert,
            clf_binario=clf_binario,
            le_binario=le_binario,
            clf_ejes=clf_ejes,
            le_ejes=le_ejes
        )
        
        # 4. Guarda en Google Sheets
        # Guardaremos el texto original y la clasificación final (el eje más probable o "Opinión")
        sheet.append_row([texto, clasificacion_para_sheets])
        
        st.success("✅ Guardado en Google Sheets.")
        
        # 5. Muestra los resultados al usuario
        st.markdown(resumen_para_usuario)