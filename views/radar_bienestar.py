import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import utils

# Inyectar estilos premium
utils.inject_premium_css()

# Header superior principal
st.markdown("""
<div class="main-header">
    <span class="header-breadcrumb">CASEN &gt; BIENESTAR MULTIDIMENSIONAL</span>
</div>
""", unsafe_allow_html=True)

st.title("Calidad de Vida e Indicadores de Carencia (Radar)")
st.markdown("""
Esta sección analiza la calidad de vida en Chile mediante un gráfico radial que compara la proporción de la población **no carente** en seis dimensiones fundamentales del bienestar, según el nivel educativo alcanzado.
""")

# Sidebar - Selector de Año y Comparación para Radar
st.sidebar.markdown("### CONFIGURACIÓN GLOBAL")
years = [2024, 2022, 2017, 2015, 2013, 2011, 2009, 2006]
selected_year = st.sidebar.selectbox(
    "Seleccionar Encuesta CASEN (Radar):",
    options=years,
    index=0,
    help="Actualiza los datos del gráfico radial."
)

st.sidebar.markdown("<hr style='margin: 15px 0px; border-color: rgba(245, 239, 237, 0.15);'>", unsafe_allow_html=True)

# Carga de datos de la CASEN seleccionada
try:
    df_casen = utils.load_casen_data(selected_year)
    utils.render_sidebar_indicators(df_casen)
    
    # Verificar si el año cuenta con variables de pobreza multidimensional
    welfare_cols_exist = 'educc' in df_casen.columns and 'pobreza' in df_casen.columns
    
    if welfare_cols_exist:
        st.markdown("""
        Un porcentaje más cercano al **100%** representa mejores niveles de calidad de vida (menores carencias).
        Selecciona las categorías educativas que deseas comparar en el panel lateral.
        """)
        
        st.sidebar.markdown("### FILTROS RADAR BIENESTAR")
        
        # Mapear categorías educativas
        EDU_MAP_7 = {
            0: "Sin educ. formal",
            1: "Básica incompleta",
            2: "Básica completa",
            3: "Media incompleta",
            4: "Media completa",
            5: "Superior incompleta",
            6: "Superior completa"
        }
        
        # Filtrar registros válidos
        df_welfare = df_casen[(df_casen['educc'] >= 0) & (df_casen['educc'] <= 6) & (df_casen['expr'] > 0)].copy()
        df_welfare['educc_label'] = df_welfare['educc'].map(EDU_MAP_7)
        
        # Dimensiones de bienestar (1 = No carente, 0 = Carente)
        df_welfare['ingreso_pos'] = (df_welfare['pobreza'] == 3).astype(float)
        
        # Salud
        salud_vars = ['hh_d_acc', 'hh_d_ali', 'hh_d_contprev', 'hh_d_dpf']
        salud_exist = [v for v in salud_vars if v in df_welfare.columns]
        df_welfare['salud_pos'] = 1.0 - df_welfare[salud_exist].mean(axis=1) if salud_exist else 1.0
        
        # Vivienda
        vivienda_vars = ['hh_d_defcuali', 'hh_d_defcuanti', 'hh_d_accesi', 'hh_d_medio']
        vivienda_exist = [v for v in vivienda_vars if v in df_welfare.columns]
        df_welfare['vivienda_pos'] = 1.0 - df_welfare[vivienda_exist].mean(axis=1) if vivienda_exist else 1.0
        
        # Ocupación
        ocupacion_vars = ['hh_d_actsub', 'hh_d_inf', 'hh_d_jub', 'hh_d_cui']
        ocupacion_exist = [v for v in ocupacion_vars if v in df_welfare.columns]
        df_welfare['ocupacion_pos'] = 1.0 - df_welfare[ocupacion_exist].mean(axis=1) if ocupacion_exist else 1.0
        
        # Seguridad
        df_welfare['seguridad_pos'] = 1.0 - df_welfare['hh_d_seg'] if 'hh_d_seg' in df_welfare.columns else 1.0
        
        # Educación Hijos
        educ_hijos_vars = ['hh_d_asis', 'hh_d_rez', 'hh_d_ape']
        educ_hijos_exist = [v for v in educ_hijos_vars if v in df_welfare.columns]
        df_welfare['educ_hijos_pos'] = 1.0 - df_welfare[educ_hijos_exist].mean(axis=1) if educ_hijos_exist else 1.0
        
        dims = ['ingreso_pos', 'salud_pos', 'vivienda_pos', 'ocupacion_pos', 'seguridad_pos', 'educ_hijos_pos']
        dims_labels = ['Ingreso (No pobre)', 'Salud', 'Vivienda y Entorno', 'Trabajo y Seg. Social', 'Seguridad Ciudadana', 'Educación de los Hijos']
        
        # Calcular medias ponderadas
        def compute_welfare_means(group):
            w = group['expr']
            res = {}
            for d in dims:
                valid_mask = group[d].notna() & w.notna()
                if valid_mask.sum() > 0:
                    res[d] = np.average(group.loc[valid_mask, d], weights=w.loc[valid_mask]) * 100
                else:
                    res[d] = np.nan
            return pd.Series(res)
            
        w_mean_df = df_welfare.groupby('educc_label').apply(compute_welfare_means)
        
        # Selector de categorías en sidebar
        selected_edu = st.sidebar.multiselect(
            "Categorías a Comparar:",
            options=utils.EDU_MAP_7_ORDER,
            default=["Sin educ. formal", "Media completa", "Superior completa"]
        )
        
        if selected_edu:
            fig = go.Figure()
            
            color_map = {
                "Sin educ. formal": utils.PALETTE['grey_neutral'],
                "Básica incompleta": "#A6B5B8",          
                "Básica completa": utils.PALETTE['teal_light'],
                "Media incompleta": "#499FB0",          
                "Media completa": utils.PALETTE['teal'],
                "Superior incompleta": utils.PALETTE['olive'],
                "Superior completa": utils.PALETTE['orange']
            }
            
            for edu_label in selected_edu:
                if edu_label in w_mean_df.index:
                    row = w_mean_df.loc[edu_label]
                    values = [row[d] for d in dims]
                    values += values[:1] # Cerrar bucle
                    dims_labels_closed = dims_labels + [dims_labels[0]] # Cerrar bucle angular
                    
                    fig.add_trace(go.Scatterpolar(
                        r=values,
                        theta=dims_labels_closed,
                        fill='toself',
                        name=edu_label,
                        line=dict(color=color_map.get(edu_label, utils.PALETTE['teal']), width=2),
                        fillcolor=f"rgba{tuple(int(color_map.get(edu_label, utils.PALETTE['teal'])[i:i+2], 16) for i in (1, 3, 5)) + (0.15,)}"
                    ))
                    
            fig.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[50, 100],
                        ticksuffix='%',
                        angle=0,
                        tickfont=dict(size=9, color=utils.PALETTE['dark']),
                        gridcolor="rgba(15, 10, 10, 0.1)"
                    ),
                    angularaxis=dict(
                        gridcolor="rgba(15, 10, 10, 0.1)",
                        tickfont=dict(size=10)
                    )
                ),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(family="Outfit, sans-serif", color=utils.PALETTE['dark']),
                legend=dict(
                    orientation="h",
                    yanchor="top",
                    y=-0.25,
                    xanchor="center",
                    x=0.5,
                    font=dict(size=13)
                ),
                height=520,
                margin=dict(l=80, r=80, t=20, b=100)
            )
            
            with st.container(border=True):
                st.markdown(f"<div class='card-title'>Perfil de Bienestar Multidimensional por Nivel Educativo ({selected_year})</div>", unsafe_allow_html=True)
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        else:
            st.info("Selecciona al menos un nivel educativo en el panel lateral para visualizar la comparación radial.")
            
    else:
        st.warning(f"""
        ⚠️ **Indicadores no disponibles para {selected_year}:**
        Las dimensiones oficiales de pobreza y bienestar multidimensional se incorporaron formalmente en la encuesta CASEN a partir del año **2015**. 
        Por favor, selecciona un año entre **2015 y 2024** en el panel lateral para explorar este gráfico.
        """)
        
except Exception as e:
    st.error(f"Error cargando o procesando los datos de la encuesta CASEN {selected_year}: {e}")
    st.warning("Verifica que los archivos parquet de CASEN estén presentes en el directorio del proyecto.")
