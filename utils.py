import streamlit as st
import os
import json
import pandas as pd
import geopandas as gpd

# 1. Paleta de Colores Estandarizada y Académica (Alto Contraste)
PALETTE = {
    "dark": "#0F0A0A",          # Casi negro para textos y bordes
    "light": "#FFFFFF",         # Fondo general del dashboard (blanco puro)
    "teal": "#2292A4",          # Teal principal (para Técnico Superior, etc.)
    "olive": "#BDBF09",         # Olive principal (para Profesional)
    "orange": "#D96C06",        # Orange principal (para Postgrados)
    "white": "#FFFFFF",         # Fondo blanco puro
    "grey_light": "#D3CFCF",    # Gris claro base
    "teal_light": "#7BB4C0",    # Teal suave
    "teal_dark": "#1B5865",     # Teal oscuro
    "orange_dark": "#C25E05",   # Naranja oscuro
    "grey_neutral": "#8A9095"   # Gris medio para anotaciones
}

# Mapeo tradicional de regiones de Chile
REGION_MAP = {
    1: "Tarapacá",
    2: "Antofagasta",
    3: "Atacama",
    4: "Coquimbo",
    5: "Valparaíso",
    6: "O'Higgins",
    7: "Maule",
    8: "Bío Bío",
    9: "Araucanía",
    10: "Los Lagos",
    11: "Aysén",
    12: "Magallanes",
    13: "Metropolitana",
    14: "Los Ríos",
    15: "Arica y Parinacota",
    16: "Ñuble"
}

# Orden geográfico oficial de Norte a Sur (códigos tradicionales)
REGIONS_NORTH_TO_SOUTH = [15, 1, 2, 3, 4, 5, 13, 6, 7, 16, 8, 9, 14, 10, 11, 12]

# Categorías educativas para gráficos
EDU_LEVELS_ORDER = ["Sin educación", "Básica", "Media", "Técnica", "Universitaria", "Postgrado"]
EDU_MAP_7_ORDER = [
    "Sin educ. formal",
    "Básica incompleta",
    "Básica completa",
    "Media incompleta",
    "Media completa",
    "Superior incompleta",
    "Superior completa"
]

BASE_DIR = "."

# 2. Inyección de CSS Personalizado (Aesthetic Upgrade)
def inject_premium_css():
    st.markdown(f"""
    <style>
        /* Importación de tipografía premium desde Google Fonts */
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');
        
        /* Tipografía global */
        html, body, [class*="css"], .stMarkdown, .stText, .stButton, .stSelectbox, .stRadio, .stSlider {{
            font-family: 'Outfit', sans-serif !important;
            color: {PALETTE['dark']} !important;
        }}
        
        /* Fondo del área principal */
        .stApp {{
            background-color: {PALETTE['light']} !important;
        }}
        
        /* Barra lateral (Sidebar) */
        section[data-testid="stSidebar"] {{
            background-color: {PALETTE['dark']} !important;
            border-right: 1px solid {PALETTE['dark']} !important;
        }}
        
        /* Textos de la barra lateral */
        section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
        section[data-testid="stSidebar"] span,
        section[data-testid="stSidebar"] label,
        section[data-testid="stSidebar"] h1,
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h3 {{
            color: {PALETTE['light']} !important;
        }}
        
        /* Subtítulos de sección en sidebar */
        section[data-testid="stSidebar"] h3 {{
            border-bottom: 1px solid rgba(245, 239, 237, 0.15);
            padding-bottom: 8px;
            margin-top: 15px;
            letter-spacing: 0.8px;
        }}
        
        /* Contenedores con estilo de tarjeta (cards) */
        div[data-testid="stVerticalBlockBorderWrapper"] {{
            background-color: {PALETTE['white']} !important;
            border: 1px solid {PALETTE['grey_light']} !important;
            border-radius: 12px !important;
            padding: 20px !important;
            box-shadow: 0 4px 12px rgba(15, 10, 10, 0.03) !important;
            margin-bottom: 16px !important;
            transition: transform 0.2s ease, box-shadow 0.2s ease !important;
        }}
        
        div[data-testid="stVerticalBlockBorderWrapper"]:hover {{
            box-shadow: 0 8px 18px rgba(15, 10, 10, 0.06) !important;
        }}
        
        /* Quitar padding de columnas en Streamlit */
        div[data-testid="column"] {{
            padding: 0px 8px !important;
        }}
        
        /* Header superior */
        .main-header {{
            margin-top: -30px;
            margin-bottom: 25px;
            border-bottom: 2px solid {PALETTE['grey_light']};
            padding-bottom: 12px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}
        .header-breadcrumb {{
            font-size: 13px;
            font-weight: 700;
            color: {PALETTE['teal']};
            letter-spacing: 1.2px;
        }}
        
        /* Tarjetas de KPI (Custom HTML con animaciones) */
        .kpi-card {{
            background-color: {PALETTE['white']};
            border: 1px solid {PALETTE['grey_light']};
            border-radius: 10px;
            padding: 18px;
            box-shadow: 0 4px 10px rgba(15, 10, 10, 0.03);
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            min-height: 110px;
            margin-bottom: 12px;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            border-left: 5px solid {PALETTE['grey_light']};
        }}
        .kpi-card.teal {{ border-left-color: {PALETTE['teal']}; }}
        .kpi-card.olive {{ border-left-color: {PALETTE['olive']}; }}
        .kpi-card.orange {{ border-left-color: {PALETTE['orange']}; }}
        
        .kpi-card:hover {{
            transform: translateY(-3px);
            box-shadow: 0 10px 20px rgba(15, 10, 10, 0.07);
        }}
        .kpi-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        }}
        .kpi-title {{
            font-size: 11px;
            font-weight: 700;
            color: {PALETTE['dark']};
            opacity: 0.65;
            letter-spacing: 0.6px;
        }}
        .kpi-icon {{
            font-size: 16px;
        }}
        .kpi-value {{
            font-size: 24px;
            font-weight: 700;
            color: {PALETTE['dark']};
            margin-bottom: 4px;
        }}
        .kpi-footer {{
            font-size: 11px;
            font-weight: 600;
        }}
        
        /* Título de gráficos en tarjetas */
        .card-title {{
            font-size: 15px;
            font-weight: 700;
            color: {PALETTE['dark']};
            margin-bottom: 16px;
            border-left: 4px solid {PALETTE['teal']};
            padding-left: 8px;
            line-height: 1.2;
        }}
        
        /* Tooltips y selects premium */
        div[data-baseweb="select"] {{
            border-radius: 8px !important;
        }}
    </style>
    """, unsafe_allow_html=True)

# 3. Funciones de Carga de Datos Cacheada
@st.cache_data(show_spinner="Cargando datos históricos de la encuesta CASEN...")
def load_historical_quintiles_data():
    """Carga y procesar escolaridad por quintiles de todos los años disponibles."""
    years = [2006, 2009, 2011, 2013, 2015, 2017, 2022, 2024]
    schooling_data = []
    
    for yr in years:
        filepath = os.path.join(BASE_DIR, f"casen_{yr}.parquet")
        if os.path.exists(filepath):
            try:
                # Carga optimizada seleccionando solo columnas necesarias
                df = pd.read_parquet(filepath, columns=['esc', 'qaut', 'expr'])
                df = df.dropna(subset=['esc', 'qaut', 'expr'])
                df = df[(df['esc'] >= 0) & (df['qaut'] >= 1) & (df['qaut'] <= 5) & (df['expr'] > 0)]
                
                # Calcular promedio ponderado por quintil
                for q in range(1, 6):
                    df_q = df[df['qaut'] == q]
                    w_mean = (df_q['esc'] * df_q['expr']).sum() / df_q['expr'].sum()
                    schooling_data.append({
                        'year': yr,
                        'quintil': q,
                        'schooling_mean': w_mean
                    })
            except Exception as e:
                print(f"Error procesando quintiles de CASEN {yr}: {e}")
                
    return pd.DataFrame(schooling_data)

@st.cache_data(show_spinner="Cargando datos de la encuesta CASEN seleccionada...")
def load_casen_data(year):
    """Carga los microdatos CASEN para un año específico de forma robusta e inteligente."""
    filepath = os.path.join(BASE_DIR, f"casen_{year}.parquet")
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"No se encontró el archivo casen_{year}.parquet")
        
    # Inspeccionar columnas existentes en el parquet para evitar KeyErrors
    import pyarrow.parquet as pq
    cols_in_file = pq.read_schema(filepath).names
    
    # Columnas prioritarias a cargar
    cols_to_load = []
    
    # Mapeo de variables clave
    key_vars = ['esc', 'e6a', 'ytrabajocor', 'expr', 'region', 'area', 'sexo', 'edad', 'pobreza', 'educc', 'qaut', 'dau', 'activ', 'e1', 'e3', 'e9depen']
    for v in key_vars:
        if v in cols_in_file:
            cols_to_load.append(v)
            
    # Dimensiones de bienestar multidimensional (solo presentes en CASEN >= 2015)
    welfare_dims = [
        'hh_d_acc', 'hh_d_ali', 'hh_d_contprev', 'hh_d_dpf',
        'hh_d_defcuali', 'hh_d_defcuanti', 'hh_d_accesi', 'hh_d_medio',
        'hh_d_actsub', 'hh_d_inf', 'hh_d_jub', 'hh_d_cui',
        'hh_d_seg', 'hh_d_asis', 'hh_d_rez', 'hh_d_ape'
    ]
    for d in welfare_dims:
        if d in cols_in_file:
            cols_to_load.append(d)
            
    df = pd.read_parquet(filepath, columns=cols_to_load)
    
    # Estandarización de nombres de columnas si es necesario
    # Por ejemplo, si en años antiguos la columna 'area' no está pero sí 'zona'
    if 'zona' in cols_in_file and 'area' not in df.columns:
        df = df.rename(columns={'zona': 'area'})
        
    return df

@st.cache_data(show_spinner="Cargando mapas y análisis territorial precalculado...")
def load_comunas_lisa_data():
    """Carga el GeoJSON precalculado de comunas con su escolaridad y clústeres LISA."""
    geojson_path = os.path.join(BASE_DIR, "Censo", "comunas_lisa_precalculado.geojson")
    stats_path = os.path.join(BASE_DIR, "Censo", "moran_stats.json")
    
    if not os.path.exists(geojson_path):
        raise FileNotFoundError(
            "El archivo comunas_lisa_precalculado.geojson no existe. "
            "Asegúrate de ejecutar 'preprocesar_datos.py' antes para generarlo."
        )
        
    gdf = gpd.read_file(geojson_path)
    
    # Cargar estadísticas globales
    moran_stats = {"moran_i": 0.0, "moran_p": 1.0, "national_mean": 0.0}
    if os.path.exists(stats_path):
        with open(stats_path, 'r', encoding='utf-8') as f:
            moran_stats = json.load(f)
            
    return gdf, moran_stats

def get_weighted_mean(df, val_col, weight_col):
    """Calcula el promedio ponderado de una columna."""
    df_clean = df.dropna(subset=[val_col, weight_col])
    if len(df_clean) == 0:
        return 0.0
    return (df_clean[val_col] * df_clean[weight_col]).sum() / df_clean[weight_col].sum()

def get_weighted_median(df, val_col, weight_col):
    """Calcula la mediana ponderada de una columna."""
    df_clean = df.dropna(subset=[val_col, weight_col])
    if len(df_clean) == 0:
        return 0.0
    df_sorted = df_clean.sort_values(by=val_col)
    cumsum = df_sorted[weight_col].cumsum()
    cutoff = df_sorted[weight_col].sum() / 2.0
    idx = cumsum.searchsorted(cutoff)
    if idx >= len(df_sorted):
        idx = len(df_sorted) - 1
    return float(df_sorted.iloc[idx][val_col])

def map_education(val):
    """Homologa la columna 'e6a' de CASEN en 6 categorías educativas principales."""
    if pd.isna(val) or val < 1:
        return None
    val_int = int(val)
    if val_int in [1, 2, 3, 4, 5]:
        return "Sin educación"
    elif val_int in [6, 7]:
        return "Básica"
    elif val_int in [8, 9, 10, 11]:
        return "Media"
    elif val_int == 12:
        return "Técnica"
    elif val_int == 13:
        return "Universitaria"
    elif val_int in [14, 15]:
        return "Postgrado"
    return None

def render_sidebar_indicators(df):
    """Muestra indicadores demográficos y educativos rápidos en el panel lateral (sidebar) basándose en el DataFrame filtrado."""
    st.sidebar.markdown("<hr style='margin: 15px 0px; border-color: rgba(245, 239, 237, 0.15);'>", unsafe_allow_html=True)
    st.sidebar.markdown("### ESTADÍSTICAS RÁPIDAS (FILTRADO)")
    
    if df is not None and len(df) > 0:
        # A. Población Estimada (suma de expr)
        if 'expr' in df.columns:
            poblacion = df['expr'].sum()
            st.sidebar.metric(
                label="Población Estimada:",
                value=f"{poblacion:,.0f} hab",
                help="Suma ponderada de la población representada según la variable de expansión."
            )
            
        # B. Escolaridad Promedio (para mayores de 15 años con escolaridad válida)
        if 'esc' in df.columns:
            df_esc = df[(df['esc'] >= 0) & (df['expr'] > 0)]
            if len(df_esc) > 0:
                esc_mean = get_weighted_mean(df_esc, 'esc', 'expr')
                st.sidebar.metric(
                    label="Escolaridad Promedio:",
                    value=f"{esc_mean:.2f} años",
                    help="Promedio ponderado de los años de escolaridad de la población seleccionada."
                )
                
        # C. Ingreso Mediano Ocupados (ocupados con ingresos del trabajo positivos)
        if 'ytrabajocor' in df.columns and 'activ' in df.columns:
            df_workers = df[(df['activ'] == 1) & (df['ytrabajocor'] > 0) & (df['expr'] > 0)]
            if len(df_workers) > 0:
                inc_median = get_weighted_median(df_workers, 'ytrabajocor', 'expr')
                st.sidebar.metric(
                    label="Ingreso Mediano Laboral:",
                    value=f"${inc_median:,.0f}",
                    help="Mediana ponderada de ingresos líquidos de los ocupados filtrados."
                )
    else:
        st.sidebar.warning("No hay datos disponibles para calcular métricas rápidas.")

@st.cache_data(show_spinner="Cargando ingresos históricos por nivel educativo...")
def load_historical_education_income_data():
    """Calcula el ingreso mediano laboral ponderado de los niveles Básica, Media y Técnica para todos los años disponibles."""
    years = [2006, 2009, 2011, 2013, 2015, 2017, 2022, 2024]
    income_data = []
    
    for yr in years:
        filepath = os.path.join(BASE_DIR, f"casen_{yr}.parquet")
        if os.path.exists(filepath):
            try:
                df = pd.read_parquet(filepath, columns=['e6a', 'ytrabajocor', 'expr', 'activ'])
                df = df.dropna(subset=['e6a', 'ytrabajocor', 'expr', 'activ'])
                df = df[(df['activ'] == 1) & (df['ytrabajocor'] > 0) & (df['expr'] > 0)]
                
                df['edu_mapped'] = df['e6a'].apply(map_education)
                df = df.dropna(subset=['edu_mapped'])
                
                for edu in ["Básica", "Media", "Técnica"]:
                    df_edu = df[df['edu_mapped'] == edu]
                    if len(df_edu) > 0:
                        median_inc = get_weighted_median(df_edu, 'ytrabajocor', 'expr')
                        income_data.append({
                            'year': yr,
                            'edu_level': edu,
                            'median_income': median_inc
                        })
            except Exception as e:
                print(f"Error procesando ingresos históricos de CASEN {yr}: {e}")
                
    return pd.DataFrame(income_data)


