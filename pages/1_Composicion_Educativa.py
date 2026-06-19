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
    <span class="header-breadcrumb">CASEN 2024 &gt; COMPOSICIÓN EDUCATIVA</span>
</div>
""", unsafe_allow_html=True)

st.title("Composición Educativa y Distribución del Ingreso")
st.markdown("""
Esta sección analiza cómo se distribuyen los diferentes niveles educativos de la población ocupada 
a lo largo de los distintos **deciles y quintiles de ingresos autónomos**, así como su composición demográfica general.
""")

# 1. Filtros Dinámicos en el Sidebar
st.sidebar.markdown("### FILTROS DE COMPOSICIÓN")

# Filtro de Región
region_options = ["Todas las Regiones"] + [utils.REGION_MAP[r] for r in utils.REGIONS_NORTH_TO_SOUTH]
selected_region_name = st.sidebar.selectbox("Región:", options=region_options)

# Filtro de Zona (Urbano/Rural)
selected_zona = st.sidebar.radio("Zona:", options=["Todas", "Urbano", "Rural"], index=0)

# Filtro de Sexo
selected_sexo = st.sidebar.radio("Sexo:", options=["Todos", "Hombre", "Mujer"], index=0)

# Filtro de Rango de Edad
age_range = st.sidebar.slider("Rango de Edad (Años):", min_value=15, max_value=100, value=(15, 80))

# Cargar datos de CASEN 2024
try:
    df_raw = utils.load_casen_data(2024)
    
    # Filtrar solo población ocupada con ingresos válidos y educación/deciles válidos
    df_filtered = df_raw[
        (df_raw['activ'] == 1) & 
        (df_raw['ytrabajocor'] > 0) & 
        (df_raw['dau'].notna()) & 
        (df_raw['qaut'].notna()) & 
        (df_raw['e6a'].notna()) &
        (df_raw['expr'] > 0)
    ].copy()
    
    # Aplicar filtros dinámicos
    if selected_region_name != "Todas las Regiones":
        region_id = [k for k, v in utils.REGION_MAP.items() if v == selected_region_name][0]
        df_filtered = df_filtered[df_filtered['region'] == region_id]
        
    if selected_zona == "Urbano":
        df_filtered = df_filtered[df_filtered['area'] == 1]
    elif selected_zona == "Rural":
        df_filtered = df_filtered[df_filtered['area'] == 2]
        
    if selected_sexo == "Hombre":
        df_filtered = df_filtered[df_filtered['sexo'] == 1]
    elif selected_sexo == "Mujer":
        df_filtered = df_filtered[df_filtered['sexo'] == 2]
        
    df_filtered = df_filtered[
        (df_filtered['edad'] >= age_range[0]) & 
        (df_filtered['edad'] <= age_range[1])
    ]
    
    if len(df_filtered) == 0:
        st.warning("⚠️ **Sin Datos:** No hay observaciones que cumplan con la combinación de filtros seleccionada. Por favor ajusta los parámetros en el panel lateral.")
    else:
        # Renderizar indicadores dinámicos en la barra lateral
        utils.render_sidebar_indicators(df_filtered)
        
        # Recodificación de educación a 5 categorías principales
        conditions = [
            df_filtered["e6a"].isin([1, 2, 3, 4, 5, 6, 7]),
            df_filtered["e6a"].isin([8, 9, 10, 11]),
            df_filtered["e6a"] == 12,
            df_filtered["e6a"] == 13,
            df_filtered["e6a"].isin([14, 15]),
        ]
        edu_labels = ["1. Básica o inf.", "2. Educación media", "3. Técnico superior", "4. Profesional", "5. Postgrados"]
        df_filtered["edu_cat_5"] = np.select(conditions, edu_labels, default="Sin clasificar")
        df_filtered = df_filtered[df_filtered["edu_cat_5"] != "Sin clasificar"]
        
        # Botón de alternancia (deciles vs quintiles)
        agg_mode = st.radio(
            "Seleccionar nivel de agregación socioeconómica:",
            options=["Deciles de Ingreso", "Quintiles de Ingreso"],
            horizontal=True
        )
        
        if agg_mode == "Deciles de Ingreso":
            group_col = 'dau'
            group_labels = [f"Decil {i}" for i in range(1, 11)]
            group_keys = list(range(1, 11))
            chart_title = "A. Composición Educativa por Decil de Ingresos (Población Ocupada)"
        else:
            group_col = 'qaut'
            group_labels = [f"Quintil {i}" for i in range(1, 6)]
            group_keys = list(range(1, 6))
            chart_title = "A. Composición Educativa por Quintil de Ingresos (Población Ocupada)"
            
        # 2. STACKED BAR CHART HORIZONTAL
        grouped_counts = df_filtered.groupby([group_col, 'edu_cat_5'])['expr'].sum().unstack(fill_value=0)
        grouped_counts = grouped_counts.reindex(index=group_keys, columns=edu_labels, fill_value=0)
        
        row_totals = grouped_counts.sum(axis=1)
        grouped_pct = grouped_counts.div(row_totals, axis=0) * 100
        
        segment_colors = [
            utils.PALETTE['grey_light'],    # 1. Básica o inf.
            utils.PALETTE['teal_light'],    # 2. Educación media
            utils.PALETTE['teal'],          # 3. Técnico superior
            utils.PALETTE['olive'],         # 4. Profesional
            utils.PALETTE['orange']         # 5. Postgrados
        ]
        
        fig_bar = go.Figure()
        
        for i, col in enumerate(edu_labels):
            pct_vals = grouped_pct[col].values
            pop_vals = grouped_counts[col].values
            
            text_labels = [f"{v:.1f}%" if v > 7.0 else "" for v in pct_vals]
            
            hover_text = [
                f"<b>Nivel Socioeconómico:</b> {group_labels[idx]}<br>"
                f"<b>Nivel Educativo:</b> {col}<br>"
                f"<b>Proporción:</b> {pct_vals[idx]:.2f}% de la categoría<br>"
                f"<b>Población Estimada:</b> {pop_vals[idx]:,.0f} personas"
                for idx in range(len(pct_vals))
            ]
            
            fig_bar.add_trace(go.Bar(
                y=group_labels,
                x=pct_vals,
                name=col,
                orientation='h',
                marker=dict(color=segment_colors[i], line=dict(color=utils.PALETTE['white'], width=0.5)),
                text=text_labels,
                textposition='inside',
                insidetextanchor='middle',
                textfont=dict(size=10, family="Outfit, sans-serif", color=utils.PALETTE['dark']),
                hoverinfo='text',
                hovertext=hover_text
            ))
            
        fig_bar.update_layout(
            barmode='stack',
            xaxis=dict(
                title="Porcentaje (%)", 
                range=[0, 100],
                gridcolor="rgba(15, 10, 10, 0.05)"
            ),
            yaxis=dict(
                autorange="reversed",
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
            height=400,
            margin=dict(l=10, r=10, t=10, b=100)
        )
        
        with st.container(border=True):
            st.markdown(f"<div class='card-title'>{chart_title}</div>", unsafe_allow_html=True)
            st.plotly_chart(fig_bar, use_container_width=True, config={'displayModeBar': False})
            
        st.markdown("<div style='height: 25px;'></div>", unsafe_allow_html=True)
        
        # 3. NUEVAS VISUALIZACIONES DE COMPOSICIÓN EDUCATIVA
        st.markdown("### Visualizaciones de la Composición Educativa")
        
        col_new_left, col_new_right = st.columns([1, 1])
        
        with col_new_left:
            # Gráfico de Anillo General de Composición Educativa
            with st.container(border=True):
                st.markdown("<div class='card-title'>B. Distribución Educativa General de la Población Ocupada</div>", unsafe_allow_html=True)
                
                # Sumar la población ponderada por categoría educativa
                overall_counts = df_filtered.groupby('edu_cat_5')['expr'].sum()
                overall_counts = overall_counts.reindex(edu_labels, fill_value=0)
                
                fig_donut = go.Figure(data=[go.Pie(
                    labels=overall_counts.index,
                    values=overall_counts.values,
                    hole=0.6,
                    marker=dict(colors=segment_colors),
                    textinfo='percent',
                    hoverinfo='label+value+percent',
                    textfont=dict(family="Outfit, sans-serif", size=11, color=utils.PALETTE['dark'])
                )])
                
                fig_donut.update_layout(
                    showlegend=True,
                    legend=dict(
                        orientation="h",
                        yanchor="top",
                        y=-0.3,
                        xanchor="center",
                        x=0.5,
                        font=dict(size=13)
                    ),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    margin=dict(l=10, r=10, t=10, b=90),
                    height=350
                )
                
                st.plotly_chart(fig_donut, use_container_width=True, config={'displayModeBar': False})
                
        with col_new_right:
            # Gráfico de comparación demográfica dinámica
            with st.container(border=True):
                st.markdown("<div class='card-title'>C. Comparativa Demográfica por Nivel Educativo</div>", unsafe_allow_html=True)
                
                compare_option = st.selectbox(
                    "Agrupar comparación por:",
                    options=["Sexo (Hombre vs. Mujer)", "Zona (Urbano vs. Rural)"],
                    key="dem_compare_select"
                )
                
                if "Sexo" in compare_option:
                    group_dem = 'sexo'
                    dem_labels = {1: "Hombre", 2: "Mujer"}
                    dem_colors = [utils.PALETTE['teal'], utils.PALETTE['orange']]
                else:
                    group_dem = 'area'
                    dem_labels = {1: "Urbano", 2: "Rural"}
                    dem_colors = [utils.PALETTE['teal'], utils.PALETTE['olive']]
                    
                df_dem = df_filtered.copy()
                df_dem['dem_label'] = df_dem[group_dem].map(dem_labels)
                df_dem = df_dem.dropna(subset=['dem_label'])
                
                # Calcular porcentajes por cada grupo demográfico
                grouped_dem = df_dem.groupby(['dem_label', 'edu_cat_5'])['expr'].sum().unstack(fill_value=0)
                grouped_dem = grouped_dem.reindex(columns=edu_labels, fill_value=0)
                dem_totals = grouped_dem.sum(axis=1)
                grouped_dem_pct = grouped_dem.div(dem_totals, axis=0) * 100
                
                fig_compare = go.Figure()
                
                for idx, dem_name in enumerate(grouped_dem_pct.index):
                    fig_compare.add_trace(go.Bar(
                        name=dem_name,
                        x=edu_labels,
                        y=grouped_dem_pct.loc[dem_name].values,
                        marker_color=dem_colors[idx],
                        text=[f"{v:.1f}%" for v in grouped_dem_pct.loc[dem_name].values],
                        textposition='auto',
                        textfont=dict(size=9, family="Outfit, sans-serif"),
                        hoverinfo='name+x+y'
                    ))
                    
                fig_compare.update_layout(
                    barmode='group',
                    yaxis=dict(
                        title="Porcentaje (%)",
                        ticksuffix="%",
                        gridcolor="rgba(15, 10, 10, 0.05)"
                    ),
                    xaxis=dict(
                        title="Nivel Educativo",
                        tickangle=-15,
                        tickfont=dict(size=10)
                    ),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(family="Outfit, sans-serif", color=utils.PALETTE['dark']),
                    legend=dict(
                        orientation="h",
                        yanchor="top",
                        y=-0.35,
                        xanchor="center",
                        x=0.5,
                        font=dict(size=13)
                    ),
                    height=300,
                    margin=dict(l=10, r=10, t=10, b=100)
                )
                
                st.plotly_chart(fig_compare, use_container_width=True, config={'displayModeBar': False})

except Exception as e:
    st.error(f"Error cargando o procesando los datos para la composición educativa: {e}")
