import streamlit as st

# 1. Configuración de la página en Streamlit (debe ejecutarse una sola vez al inicio)
st.set_page_config(
    page_title="Dashboard - Vista General",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Definición de las páginas y secciones del panel
general_page = st.Page(
    page="views/informacion_general.py",
    title="Información General",
    icon="📊",
    default=True
)

radar_page = st.Page(
    page="views/radar_bienestar.py",
    title="Bienestar Multidimensional",
    icon="🕸️"
)

educacion_page = st.Page(
    page="pages/1_Composicion_Educativa.py",
    title="Composición Educativa",
    icon="🎓"
)

territorial_page = st.Page(
    page="pages/2_Analisis_Territorial.py",
    title="Análisis Territorial",
    icon="🗺️"
)

brecha_page = st.Page(
    page="pages/3_Brecha_Salarial.py",
    title="Brecha Salarial",
    icon="⚖️"
)

temporal_page = st.Page(
    page="pages/4_Evolucion_Temporal.py",
    title="Evolución Temporal",
    icon="📈"
)

# 3. Configuración y ejecución de la navegación
pg = st.navigation({
    "General": [general_page, radar_page],
    "Secciones de Análisis": [educacion_page, territorial_page, brecha_page, temporal_page]
})

pg.run()
