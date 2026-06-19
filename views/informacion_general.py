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
    <span class="header-breadcrumb">CASEN &gt; INFORMACIÓN GENERAL</span>
</div>
""", unsafe_allow_html=True)

# Título y descripción
st.title("Información General del Bienestar y Educación en Chile")
st.markdown("""
Esta sección presenta una vista general de los indicadores clave de la población chilena utilizando los microdatos oficiales 
de las encuestas **CASEN (2006–2024)**. Explora los KPIs nacionales y la composición demográfica de la muestra ponderada.
""")

# Sidebar - Selector de Año y Filtros Globales
st.sidebar.markdown("### CONFIGURACIÓN GLOBAL")
years = [2024, 2022, 2017, 2015, 2013, 2011, 2009, 2006]
selected_year = st.sidebar.selectbox(
    "Seleccionar Encuesta CASEN:",
    options=years,
    index=0,
    help="Actualiza los datos e indicadores del panel en tiempo real."
)

# Filtro de Región
region_options = ["Todas las Regiones"] + [utils.REGION_MAP[r] for r in utils.REGIONS_NORTH_TO_SOUTH]
selected_region_name = st.sidebar.selectbox("Región (Filtro Global):", options=region_options)

# Filtro de Zona (Urbano/Rural)
selected_zona = st.sidebar.radio("Zona (Filtro Global):", options=["Todas", "Urbano", "Rural"], index=0)

# Filtro de Sexo
selected_sexo = st.sidebar.radio("Sexo (Filtro Global):", options=["Todos", "Hombre", "Mujer"], index=0)

# Carga de datos de la CASEN seleccionada
try:
    df_raw = utils.load_casen_data(selected_year)
    df_casen = df_raw.copy()
    
    # Aplicar filtros globales dinámicos
    if selected_region_name != "Todas las Regiones":
        region_id = [k for k, v in utils.REGION_MAP.items() if v == selected_region_name][0]
        df_casen = df_casen[df_casen['region'] == region_id]
        
    if selected_zona == "Urbano":
        df_casen = df_casen[df_casen['area'] == 1]
    elif selected_zona == "Rural":
        df_casen = df_casen[df_casen['area'] == 2]
        
    if selected_sexo == "Hombre":
        df_casen = df_casen[df_casen['sexo'] == 1]
    elif selected_sexo == "Mujer":
        df_casen = df_casen[df_casen['sexo'] == 2]
        
    # Renderizar indicadores dinámicos en la barra lateral
    utils.render_sidebar_indicators(df_casen)
    
    if len(df_casen) == 0:
        st.warning("⚠️ **Sin Datos:** No hay observaciones que cumplan con la combinación de filtros seleccionada. Por favor ajusta los parámetros en el panel lateral.")
    else:
        # 1. CÁLCULO DE MÉTRICAS (KPIs Nacionales / Filtrados)
        # A. Años de escolaridad promedio nacional
        df_esc = df_casen[(df_casen['esc'] >= 0) & (df_casen['expr'] > 0)].copy()
        schooling_mean = utils.get_weighted_mean(df_esc, 'esc', 'expr')
        
        # B. % de la población con educación superior completa o incompleta
        df_sup = df_esc.copy()
        df_sup['is_superior'] = (df_sup['e6a'] >= 12).astype(float)
        superior_pct = utils.get_weighted_mean(df_sup, 'is_superior', 'expr') * 100
        
        # C. Ingreso Laboral Mediano
        df_workers_all = df_casen[
            (df_casen['activ'] == 1) & 
            (df_casen['ytrabajocor'] > 0) & 
            (df_casen['expr'] > 0)
        ].copy()
        if len(df_workers_all) > 0:
            median_labor_income = utils.get_weighted_median(df_workers_all, 'ytrabajocor', 'expr')
        else:
            median_labor_income = 0.0
            
        # D. Brecha salarial promedio/mediana Técnico vs Profesional
        df_workers_gap = df_casen[
            (df_casen['activ'] == 1) & 
            (df_casen['ytrabajocor'] > 0) & 
            (df_casen['e6a'].isin([12, 13])) &
            (df_casen['expr'] > 0)
        ].copy()
        
        if len(df_workers_gap) > 0:
            df_tec = df_workers_gap[df_workers_gap['e6a'] == 12]
            tec_median = utils.get_weighted_median(df_tec, 'ytrabajocor', 'expr') if len(df_tec) > 0 else 0
            
            df_prof = df_workers_gap[df_workers_gap['e6a'] == 13]
            prof_median = utils.get_weighted_median(df_prof, 'ytrabajocor', 'expr') if len(df_prof) > 0 else 0
            
            if tec_median > 0:
                wage_gap_pct = ((prof_median / tec_median) - 1) * 100
            else:
                wage_gap_pct = 0.0
        else:
            wage_gap_pct = 0.0
            
        # Mostrar KPIs en tarjetas estilizadas (ahora 4 columnas)
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="kpi-card teal">
                <div class="kpi-header">
                    <span class="kpi-title">ESCOLARIDAD PROMEDIO</span>
                    <span class="kpi-icon">📚</span>
                </div>
                <div class="kpi-value">{schooling_mean:.2f} años</div>
                <div class="kpi-footer" style="color: {utils.PALETTE['teal']};">
                    Población ≥ 15 años ({selected_year})
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        with col2:
            st.markdown(f"""
            <div class="kpi-card olive">
                <div class="kpi-header">
                    <span class="kpi-title">TASA EDUCACIÓN SUPERIOR</span>
                    <span class="kpi-icon">🎓</span>
                </div>
                <div class="kpi-value">{superior_pct:.1f}%</div>
                <div class="kpi-footer" style="color: {utils.PALETTE['olive']};">
                    Población con educación superior
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        with col3:
            st.markdown(f"""
            <div class="kpi-card teal">
                <div class="kpi-header">
                    <span class="kpi-title">INGRESO LABORAL MEDIANO</span>
                    <span class="kpi-icon">💵</span>
                </div>
                <div class="kpi-value">${median_labor_income:,.0f}</div>
                <div class="kpi-footer" style="color: {utils.PALETTE['teal']};">
                    Mediana de ingresos ocupados
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        with col4:
            st.markdown(f"""
            <div class="kpi-card orange">
                <div class="kpi-header">
                    <span class="kpi-title">BRECHA SALARIAL MEDIANA</span>
                    <span class="kpi-icon">💰</span>
                </div>
                <div class="kpi-value">+{wage_gap_pct:.1f}%</div>
                <div class="kpi-footer" style="color: {utils.PALETTE['orange']};">
                    Ingreso Profesional vs Técnico
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
        
        # 2. GRÁFICOS DE ANILLO (DEMOGRAFÍA)
        st.markdown("### Composición Demográfica General")
        
        # Preparar datos demográficos
        # A. Género
        df_gender = df_casen.dropna(subset=['sexo', 'expr'])
        df_gender = df_gender[df_gender['expr'] > 0]
        gender_weights = df_gender.groupby('sexo')['expr'].sum()
        gender_weights.index = gender_weights.index.map({1: "Hombres", 2: "Mujeres"})
        
        # B. Rangos Etarios
        df_age = df_casen.dropna(subset=['edad', 'expr'])
        df_age = df_age[df_age['expr'] > 0]
        bins = [-1, 14, 29, 44, 59, 120]
        labels = ["0-14 años", "15-29 años", "30-44 años", "45-59 años", "60+ años"]
        df_age['rango_etario'] = pd.cut(df_age['edad'], bins=bins, labels=labels)
        age_weights = df_age.groupby('rango_etario', observed=False)['expr'].sum()
        
        # Dibujar los gráficos de anillo en columnas
        c1, c2 = st.columns(2)
        
        with c1:
            with st.container(border=True):
                st.markdown("<div class='card-title'>Distribución de la Población por Género</div>", unsafe_allow_html=True)
                
                # textinfo='percent' para quitar las palabras dentro del anillo
                fig_gender = go.Figure(data=[go.Pie(
                    labels=gender_weights.index,
                    values=gender_weights.values,
                    hole=0.6,
                    marker=dict(colors=[utils.PALETTE['teal_light'], utils.PALETTE['orange']]),
                    textinfo='percent',
                    hoverinfo='label+value+percent',
                    textfont=dict(family="Outfit, sans-serif", size=11, color=utils.PALETTE['dark'])
                )])
                
                fig_gender.update_layout(
                    showlegend=True,
                    legend=dict(
                        orientation="h",
                        yanchor="top",
                        y=-0.25,
                        xanchor="center",
                        x=0.5,
                        font=dict(size=13) # Leyenda agrandada a 13px
                    ),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    margin=dict(l=10, r=10, t=10, b=90),
                    height=300
                )
                st.plotly_chart(fig_gender, use_container_width=True, config={'displayModeBar': False})
                
        with c2:
            with st.container(border=True):
                st.markdown("<div class='card-title'>Distribución de la Población por Rangos Etarios</div>", unsafe_allow_html=True)
                
                fig_age = go.Figure(data=[go.Pie(
                    labels=age_weights.index,
                    values=age_weights.values,
                    hole=0.6,
                    marker=dict(colors=[
                        utils.PALETTE['grey_light'],
                        utils.PALETTE['teal_light'],
                        utils.PALETTE['teal'],
                        utils.PALETTE['olive'],
                        utils.PALETTE['orange']
                    ]),
                    textinfo='percent',
                    hoverinfo='label+value+percent',
                    textfont=dict(family="Outfit, sans-serif", size=11, color=utils.PALETTE['dark'])
                )])
                
                fig_age.update_layout(
                    showlegend=True,
                    legend=dict(
                        orientation="h",
                        yanchor="top",
                        y=-0.25,
                        xanchor="center",
                        x=0.5,
                        font=dict(size=13) # Leyenda agrandada a 13px
                    ),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    margin=dict(l=10, r=10, t=10, b=90),
                    height=300
                )
                st.plotly_chart(fig_age, use_container_width=True, config={'displayModeBar': False})

        # 3. SECCIÓN: INDICADORES Y GRÁFICOS DE EDUCACIÓN
        st.markdown("<div style='height: 25px;'></div>", unsafe_allow_html=True)
        st.markdown("### Indicadores de Educación y Acceso Escolar")
        
        # Calcular Tasas Educacionales
        if 'e1' in df_casen.columns:
            df_lit = df_casen[(df_casen['edad'] >= 15) & (df_casen['e1'].isin([1, 2])) & (df_casen['expr'] > 0)].copy()
            df_lit['is_literate'] = (df_lit['e1'] == 1).astype(float)
            lit_rate = utils.get_weighted_mean(df_lit, 'is_literate', 'expr') * 100
        else:
            lit_rate = None
            
        if 'e3' in df_casen.columns:
            df_att = df_casen[(df_casen['edad'] >= 5) & (df_casen['edad'] <= 18) & (df_casen['e3'].isin([1, 2])) & (df_casen['expr'] > 0)].copy()
            df_att['is_attending'] = (df_att['e3'] == 1).astype(float)
            att_rate = utils.get_weighted_mean(df_att, 'is_attending', 'expr') * 100
        else:
            att_rate = None
            
        col_edu1, col_edu2 = st.columns(2)
        
        with col_edu1:
            if lit_rate is not None:
                st.markdown(f"""
                <div style="background-color: {utils.PALETTE['white']}; border: 1px solid {utils.PALETTE['grey_light']}; border-radius: 8px; padding: 15px; margin-bottom: 12px; box-shadow: 0 2px 5px rgba(0,0,0,0.02);">
                    <div style="font-size: 11px; font-weight: 700; opacity: 0.65; margin-bottom: 5px;">TASA DE ALFABETISMO (POBLACIÓN ≥ 15 AÑOS)</div>
                    <div style="font-size: 24px; font-weight: 700; color: {utils.PALETTE['teal']};">{lit_rate:.2f}%</div>
                    <div style="font-size: 10px; color: {utils.PALETTE['grey_neutral']}; margin-top: 4px;">Declaran saber leer y escribir.</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.info("Variable de alfabetismo (e1) no disponible en esta encuesta o filtros activos.")
                
        with col_edu2:
            if att_rate is not None:
                st.markdown(f"""
                <div style="background-color: {utils.PALETTE['white']}; border: 1px solid {utils.PALETTE['grey_light']}; border-radius: 8px; padding: 15px; margin-bottom: 12px; box-shadow: 0 2px 5px rgba(0,0,0,0.02);">
                    <div style="font-size: 11px; font-weight: 700; opacity: 0.65; margin-bottom: 5px;">TASA DE ASISTENCIA ESCOLAR (5 A 18 AÑOS)</div>
                    <div style="font-size: 24px; font-weight: 700; color: {utils.PALETTE['orange']};">{att_rate:.2f}%</div>
                    <div style="font-size: 10px; color: {utils.PALETTE['grey_neutral']}; margin-top: 4px;">Asistencia actual a un establecimiento regular de educación.</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.info("Variable de asistencia (e3) no disponible en esta encuesta o filtros activos.")
                
        c_edu_l, c_edu_r = st.columns(2)
        
        with c_edu_l:
            if 'e9depen' in df_casen.columns and 'e3' in df_casen.columns:
                with st.container(border=True):
                    st.markdown("<div class='card-title'>Dependencia Administrativa de la Matrícula Escolar (5-18 años)</div>", unsafe_allow_html=True)
                    
                    df_dep = df_casen[
                        (df_casen['edad'] >= 5) & 
                        (df_casen['edad'] <= 18) & 
                        (df_casen['e3'] == 1) & 
                        (df_casen['e9depen'].isin([1, 2, 3, 5])) & 
                        (df_casen['expr'] > 0)
                    ].copy()
                    
                    dep_mapping = {
                        1: "Municipal",
                        2: "Part. Subvencionado",
                        3: "Particular Pagado",
                        5: "SLEP (Público Local)"
                    }
                    df_dep['dep_label'] = df_dep['e9depen'].map(dep_mapping)
                    dep_weights = df_dep.groupby('dep_label')['expr'].sum()
                    
                    fig_dep = go.Figure(data=[go.Pie(
                        labels=dep_weights.index,
                        values=dep_weights.values,
                        hole=0.6,
                        marker=dict(colors=[
                            utils.PALETTE['teal'], 
                            utils.PALETTE['teal_light'], 
                            utils.PALETTE['orange'], 
                            utils.PALETTE['olive']
                        ]),
                        textinfo='percent',
                        hoverinfo='label+value+percent',
                        textfont=dict(family="Outfit, sans-serif", size=11, color=utils.PALETTE['dark'])
                    )])
                    
                    fig_dep.update_layout(
                        showlegend=True,
                        legend=dict(
                            orientation="h",
                            yanchor="top",
                            y=-0.2,
                            xanchor="center",
                            x=0.5,
                            font=dict(size=13) # Leyenda agrandada a 13px
                        ),
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        margin=dict(l=10, r=10, t=10, b=90),
                        height=300
                    )
                    st.plotly_chart(fig_dep, use_container_width=True, config={'displayModeBar': False})
            else:
                st.info("Información de dependencia escolar no disponible bajo la selección actual.")
                
        with c_edu_r:
            if 'e3' in df_casen.columns and 'qaut' in df_casen.columns:
                with st.container(border=True):
                    st.markdown("<div class='card-title'>Tasa de Asistencia Escolar por Quintil de Ingresos (5-18 años)</div>", unsafe_allow_html=True)
                    
                    df_quint = df_casen[
                        (df_casen['edad'] >= 5) & 
                        (df_casen['edad'] <= 18) & 
                        (df_casen['e3'].isin([1, 2])) & 
                        (df_casen['qaut'] >= 1) & 
                        (df_casen['qaut'] <= 5) & 
                        (df_casen['expr'] > 0)
                    ].copy()
                    df_quint['is_attending'] = (df_quint['e3'] == 1).astype(float)
                    
                    quint_rates = []
                    quint_labels = ["Quintil 1", "Quintil 2", "Quintil 3", "Quintil 4", "Quintil 5"]
                    
                    for q in range(1, 6):
                        df_sub = df_quint[df_quint['qaut'] == q]
                        if len(df_sub) > 0:
                            rate = utils.get_weighted_mean(df_sub, 'is_attending', 'expr') * 100
                        else:
                            rate = 0.0
                        quint_rates.append(rate)
                        
                    fig_quint = go.Figure(data=[go.Bar(
                        x=quint_labels,
                        y=quint_rates,
                        marker=dict(
                            color=quint_rates,
                            colorscale=[[0, utils.PALETTE['teal_light']], [1, utils.PALETTE['teal']]],
                            line=dict(color=utils.PALETTE['white'], width=0.5)
                        ),
                        text=[f"{r:.1f}%" for r in quint_rates],
                        textposition='outside',
                        textfont=dict(size=10, family="Outfit, sans-serif"),
                        hoverinfo='x+y'
                    )])
                    
                    fig_quint.update_layout(
                        yaxis=dict(
                            title="Tasa de Asistencia (%)",
                            range=[min(quint_rates) - 5 if min(quint_rates) > 5 else 0, 105],
                            ticksuffix="%",
                            gridcolor="rgba(15, 10, 10, 0.05)"
                        ),
                        xaxis=dict(
                            title="Quintil Socioeconómico de Hogar"
                        ),
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        font=dict(family="Outfit, sans-serif", color=utils.PALETTE['dark']),
                        height=300,
                        margin=dict(l=10, r=10, t=25, b=40)
                    )
                    st.plotly_chart(fig_quint, use_container_width=True, config={'displayModeBar': False})
            else:
                st.info("Información socioeconómica por quintiles no disponible en esta encuesta.")

        # 4. SECCIÓN NUEVA: INGRESOS Y DISTRIBUCIÓN ECONÓMICA
        st.markdown("<div style='height: 25px;'></div>", unsafe_allow_html=True)
        st.markdown("### Ingresos y Distribución Económica (Población Ocupada)")
        
        c_inc_l, c_inc_r = st.columns(2)
        
        with c_inc_l:
            # Gráfico de ingresos por Sexo en el inicio
            if len(df_workers_all) > 0 and 'sexo' in df_workers_all.columns:
                with st.container(border=True):
                    st.markdown("<div class='card-title'>Ingreso Laboral Mediano por Género</div>", unsafe_allow_html=True)
                    
                    # Mediana de ingresos por sexo
                    df_men = df_workers_all[df_workers_all['sexo'] == 1]
                    df_women = df_workers_all[df_workers_all['sexo'] == 2]
                    
                    gender_incomes = []
                    gender_labels = []
                    
                    if len(df_men) > 0:
                        gender_incomes.append(utils.get_weighted_median(df_men, 'ytrabajocor', 'expr'))
                        gender_labels.append("Hombres")
                    if len(df_women) > 0:
                        gender_incomes.append(utils.get_weighted_median(df_women, 'ytrabajocor', 'expr'))
                        gender_labels.append("Mujeres")
                        
                    fig_inc_gender = go.Figure(data=[go.Bar(
                        x=gender_labels,
                        y=gender_incomes,
                        marker=dict(
                            color=gender_incomes,
                            colorscale=[[0, utils.PALETTE['orange']], [1, utils.PALETTE['teal']]],
                            line=dict(color=utils.PALETTE['white'], width=0.5)
                        ),
                        text=[f"${val:,.0f}" for val in gender_incomes],
                        textposition='outside',
                        textfont=dict(size=10, family="Outfit, sans-serif"),
                        hoverinfo='x+y'
                    )])
                    
                    fig_inc_gender.update_layout(
                        yaxis=dict(
                            title="Ingreso Mediano ($/mes)",
                            tickprefix="$",
                            tickformat=",",
                            gridcolor="rgba(15, 10, 10, 0.05)"
                        ),
                        xaxis=dict(title="Género"),
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        font=dict(family="Outfit, sans-serif", color=utils.PALETTE['dark']),
                        height=300,
                        margin=dict(l=10, r=10, t=25, b=40)
                    )
                    st.plotly_chart(fig_inc_gender, use_container_width=True, config={'displayModeBar': False})
            else:
                st.info("Datos de ingresos por género no disponibles.")
                
        with c_inc_r:
            # Gráfico de ingresos por Quintil de Ingresos
            if len(df_workers_all) > 0 and 'qaut' in df_workers_all.columns:
                with st.container(border=True):
                    st.markdown("<div class='card-title'>Ingreso Laboral Mediano por Quintil de Ingresos</div>", unsafe_allow_html=True)
                    
                    q_incomes = []
                    q_labels = ["Quintil 1", "Quintil 2", "Quintil 3", "Quintil 4", "Quintil 5"]
                    
                    for q in range(1, 6):
                        df_sub = df_workers_all[df_workers_all['qaut'] == q]
                        if len(df_sub) > 0:
                            val = utils.get_weighted_median(df_sub, 'ytrabajocor', 'expr')
                        else:
                            val = 0.0
                        q_incomes.append(val)
                        
                    fig_inc_q = go.Figure(data=[go.Bar(
                        x=q_labels,
                        y=q_incomes,
                        marker=dict(
                            color=q_incomes,
                            colorscale=[[0, utils.PALETTE['teal_light']], [1, utils.PALETTE['olive']]],
                            line=dict(color=utils.PALETTE['white'], width=0.5)
                        ),
                        text=[f"${r:,.0f}" for r in q_incomes],
                        textposition='outside',
                        textfont=dict(size=10, family="Outfit, sans-serif"),
                        hoverinfo='x+y'
                    )])
                    
                    fig_inc_q.update_layout(
                        yaxis=dict(
                            title="Ingreso Mediano ($/mes)",
                            tickprefix="$",
                            tickformat=",",
                            gridcolor="rgba(15, 10, 10, 0.05)"
                        ),
                        xaxis=dict(title="Quintil de Ingresos"),
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        font=dict(family="Outfit, sans-serif", color=utils.PALETTE['dark']),
                        height=300,
                        margin=dict(l=10, r=10, t=25, b=40)
                    )
                    st.plotly_chart(fig_inc_q, use_container_width=True, config={'displayModeBar': False})
            else:
                st.info("Datos de ingresos por quintil no disponibles.")

except Exception as e:
    st.error(f"Error cargando o procesando los datos de la encuesta CASEN {selected_year}: {e}")
    st.warning("Verifica que los archivos parquet de CASEN estén presentes en el directorio del proyecto.")
