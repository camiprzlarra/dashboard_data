import streamlit as st
import os
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import utils

# Inyectar estilos premium
utils.inject_premium_css()

# Header superior principal
st.markdown("""
<div class="main-header">
    <span class="header-breadcrumb">CASEN 2024 &gt; BRECHA SALARIAL Y CRECIMIENTO</span>
</div>
""", unsafe_allow_html=True)

st.title("Análisis de Brecha Salarial y Crecimiento Histórico")
st.markdown("""
Estudio de la distancia salarial entre **Técnicos Superiores** y **Profesionales** en las distintas 
regiones de Chile, junto con el análisis de la tasa de crecimiento de la escolaridad y el ingreso.
""")

# Cargar datos de brechas para 2024
try:
    # 1. SIDEBAR - Calculadora de Brecha
    st.sidebar.markdown("### CALCULADORA DE BRECHA")
    
    # Cargar CASEN 2024 completa para la calculadora y gráficos
    df_2024 = utils.load_casen_data(2024)
    
    # Inputs de la calculadora
    calc_region_name = st.sidebar.selectbox(
        "Seleccionar Región (Calculadora):",
        options=[utils.REGION_MAP[r] for r in utils.REGIONS_NORTH_TO_SOUTH]
    )
    
    calc_edu = st.sidebar.selectbox(
        "Seleccionar Nivel Educativo:",
        options=utils.EDU_LEVELS_ORDER,
        index=4 # Universitaria (Profesional) por defecto
    )
    
    # Cálculos para la calculadora (fuera del sidebar)
    calc_region_id = [k for k, v in utils.REGION_MAP.items() if v == calc_region_name][0]
    
    # Ingreso mediano nacional de referencia (ocupados con ingreso > 0)
    df_national_ref = df_2024[(df_2024['activ'] == 1) & (df_2024['ytrabajocor'] > 0) & (df_2024['expr'] > 0)]
    national_median_income = utils.get_weighted_median(df_national_ref, 'ytrabajocor', 'expr')
    
    # Ingreso mediano de la combinación seleccionada
    df_calc_subset = df_2024[
        (df_2024['activ'] == 1) & 
        (df_2024['ytrabajocor'] > 0) & 
        (df_2024['region'] == calc_region_id) &
        (df_2024['expr'] > 0)
    ].copy()
    
    # Mapear e6a a categorías de la calculadora
    df_calc_subset['edu_mapped'] = df_calc_subset['e6a'].apply(utils.map_education)
    df_calc_combi = df_calc_subset[df_calc_subset['edu_mapped'] == calc_edu]
    
    if len(df_calc_combi) > 0:
        combi_median_income = utils.get_weighted_median(df_calc_combi, 'ytrabajocor', 'expr')
        # Distancia porcentual respecto a la mediana nacional
        dist_pct = ((combi_median_income / national_median_income) - 1) * 100
    else:
        combi_median_income = 0.0
        dist_pct = 0.0
        
    # Mostrar resultado de la calculadora en el sidebar
    sign = "+" if dist_pct >= 0 else ""
    color_calc = utils.PALETTE['teal'] if dist_pct >= 0 else utils.PALETTE['orange']
    
    st.sidebar.markdown(f"""
    <div style="background-color: rgba(245, 239, 237, 0.1); border: 1px solid rgba(255, 255, 255, 0.2); border-radius: 8px; padding: 15px; margin-top: 10px;">
        <div style="font-size: 10px; font-weight: 700; opacity: 0.8; margin-bottom: 5px; color: {utils.PALETTE['light']};">INGRESO MEDIANO ESTIMADO</div>
        <div style="font-size: 20px; font-weight: 700; color: {utils.PALETTE['white']};">${combi_median_income:,.0f}</div>
        <div style="margin-top: 8px; font-size: 11px; font-weight: 600; color: {color_calc};">
            {sign}{dist_pct:.1f}% vs Mediana Nacional (${national_median_income:,.0f})
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Renderizar indicadores dinámicos en la barra lateral
    utils.render_sidebar_indicators(df_2024)

    # 2. SECCIÓN PRINCIPAL: Gráficos de Brechas
    col_left, col_right = st.columns([1, 1])
    
    # Cargar y preparar tabla de brecha por región
    df_brechas_reg = df_2024[
        (df_2024['activ'] == 1) & 
        (df_2024['ytrabajocor'] > 0) & 
        (df_2024['e6a'].isin([12, 13])) &
        (df_2024['expr'] > 0)
    ].copy()
    
    df_brechas_reg['edu_label'] = df_brechas_reg['e6a'].map({12: "Técnico Superior", 13: "Profesional"})
    
    # Agrupar y pivotear
    table_brecha = df_brechas_reg.groupby(['region', 'edu_label'])['ytrabajocor'].median().unstack().dropna()
    table_brecha['brecha_pct'] = ((table_brecha['Profesional'] / table_brecha['Técnico Superior']) - 1) * 100
    
    # Agregar nombres de regiones
    table_brecha['region_name'] = table_brecha.index.map(utils.REGION_MAP)
    
    with col_left:
        # A. Dumbbell Chart
        with st.container(border=True):
            st.markdown("<div class='card-title'>A. Brecha de Ingresos Medianos por Región (Técnico vs Profesional)</div>", unsafe_allow_html=True)
            
            # Selector de orden del gráfico
            order_choice = st.selectbox(
                "Ordenar regiones por:",
                options=["Geográfico (Norte a Sur)", "Por tamaño de la brecha (Mayor a Menor)"]
            )
            
            # Reordenar tabla
            if "Geográfico" in order_choice:
                table_plot = table_brecha.reindex(utils.REGIONS_NORTH_TO_SOUTH)
            else:
                table_plot = table_brecha.sort_values(by='brecha_pct', ascending=True)
                
            fig_dumb = go.Figure()
            
            # Dibujar líneas de mancuerna y puntos
            for idx, r_id in enumerate(table_plot.index):
                r_name = table_plot.loc[r_id, 'region_name']
                tec_val = table_plot.loc[r_id, 'Técnico Superior']
                prof_val = table_plot.loc[r_id, 'Profesional']
                brecha_val = table_plot.loc[r_id, 'brecha_pct']
                
                # Línea de conexión
                fig_dumb.add_trace(go.Scatter(
                    x=[tec_val, prof_val],
                    y=[r_name, r_name],
                    mode='lines',
                    line=dict(color=utils.PALETTE['grey_light'], width=3),
                    showlegend=False,
                    hoverinfo='none'
                ))
                
                # Puntos
                fig_dumb.add_trace(go.Scatter(
                    x=[tec_val],
                    y=[r_name],
                    mode='markers',
                    marker=dict(color=utils.PALETTE['teal'], size=10),
                    name='Técnico Superior' if idx == 0 else "",
                    showlegend=True if idx == 0 else False,
                    hovertext=f"<b>Región:</b> {r_name}<br><b>Nivel:</b> Técnico Superior<br><b>Mediana:</b> ${tec_val:,.0f}",
                    hoverinfo='text'
                ))
                
                fig_dumb.add_trace(go.Scatter(
                    x=[prof_val],
                    y=[r_name],
                    mode='markers',
                    marker=dict(color=utils.PALETTE['orange'], size=10),
                    name='Profesional' if idx == 0 else "",
                    showlegend=True if idx == 0 else False,
                    hovertext=f"<b>Región:</b> {r_name}<br><b>Nivel:</b> Profesional<br><b>Mediana:</b> ${prof_val:,.0f}",
                    hoverinfo='text'
                ))
                
                # Etiqueta de la brecha
                fig_dumb.add_annotation(
                    x=prof_val + 25000,
                    y=r_name,
                    text=f"+{brecha_val:.0f}%",
                    showarrow=False,
                    font=dict(size=9, color=utils.PALETTE['orange_dark'], weight='bold'),
                    xanchor='left',
                    yanchor='middle'
                )
                
            fig_dumb.update_layout(
                xaxis=dict(
                    title="Ingreso mediano líquido del trabajo ($/mes)",
                    tickprefix="$",
                    tickformat=",",
                    gridcolor="rgba(15, 10, 10, 0.05)"
                ),
                yaxis=dict(
                    autorange="reversed"
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
                height=480,
                margin=dict(l=10, r=60, t=10, b=100)
            )
            
            st.plotly_chart(fig_dumb, use_container_width=True, config={'displayModeBar': False})
            
    with col_right:
        # B. Ranking de Brecha
        with st.container(border=True):
            st.markdown("<div class='card-title'>B. Ranking de Brecha Salarial Relativa por Región</div>", unsafe_allow_html=True)
            st.write("Distancia porcentual del ingreso de Profesionales respecto a Técnicos Superiores.")
            
            table_rank = table_brecha.sort_values(by='brecha_pct', ascending=True)
            
            hover_rank_text = [
                f"<b>Región:</b> {row['region_name']}<br><b>Brecha Salarial:</b> +{row['brecha_pct']:.1f}%<br>"
                f"<b>Mediana Profesional:</b> ${row['Profesional']:,.0f}<br>"
                f"<b>Mediana Técnico:</b> ${row['Técnico Superior']:,.0f}"
                for _, row in table_rank.iterrows()
            ]
            
            fig_rank = go.Figure(data=[go.Bar(
                x=table_rank['brecha_pct'],
                y=table_rank['region_name'],
                orientation='h',
                text=[f"+{v:.0f}%" for v in table_rank['brecha_pct']],
                textposition='auto',
                textfont=dict(size=10, family="Outfit, sans-serif"),
                marker=dict(
                    color=table_rank['brecha_pct'],
                    colorscale=[[0, utils.PALETTE['teal_light']], [1, utils.PALETTE['orange']]],
                    line=dict(color=utils.PALETTE['white'], width=0.5)
                ),
                hoverinfo='text',
                hovertext=hover_rank_text
            )])
            
            fig_rank.update_layout(
                xaxis=dict(
                    title="Brecha salarial (%)",
                    ticksuffix="%",
                    gridcolor="rgba(15, 10, 10, 0.05)"
                ),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(family="Outfit, sans-serif", color=utils.PALETTE['dark']),
                height=480,
                margin=dict(l=10, r=10, t=10, b=50)
            )
            
            st.plotly_chart(fig_rank, use_container_width=True, config={'displayModeBar': False})
            
    st.markdown("<div style='height: 25px;'></div>", unsafe_allow_html=True)
    
    # 2.5 SECCIÓN DE BRECHAS DE GÉNERO Y EDUCATIVAS
    st.markdown("### Análisis de Brechas de Género y Nivel Educativo")
    st.write("Examen detallado de la disparidad salarial entre hombres y mujeres a nivel nacional, junto con el retorno al capital humano.")
    
    # Calcular datos de brechas
    df_gap_data = df_2024[
        (df_2024['activ'] == 1) & 
        (df_2024['ytrabajocor'] > 0) & 
        (df_2024['expr'] > 0)
    ].copy()
    df_gap_data['edu_mapped'] = df_gap_data['e6a'].apply(utils.map_education)
    df_gap_data = df_gap_data.dropna(subset=['edu_mapped', 'sexo'])
    
    df_men = df_gap_data[df_gap_data['sexo'] == 1]
    df_women = df_gap_data[df_gap_data['sexo'] == 2]
    
    men_median = utils.get_weighted_median(df_men, 'ytrabajocor', 'expr')
    women_median = utils.get_weighted_median(df_women, 'ytrabajocor', 'expr')
    gender_gap_pct = (1 - (women_median / men_median)) * 100 if men_median > 0 else 0.0
    
    col_gap_left, col_gap_right = st.columns([1, 2])
    
    with col_gap_left:
        with st.container(border=True):
            st.markdown("<div class='card-title'>Brecha Salarial de Género Nacional</div>", unsafe_allow_html=True)
            st.write("Mediana de ingresos del trabajo mensuales ponderados.")
            
            st.markdown(f"""
            <div style="background-color: {utils.PALETTE['white']}; border: 1px solid {utils.PALETTE['grey_light']}; border-radius: 8px; padding: 15px; margin-bottom: 12px; box-shadow: 0 2px 5px rgba(0,0,0,0.02);">
                <div style="font-size: 11px; font-weight: 700; opacity: 0.65; margin-bottom: 5px; color: {utils.PALETTE['teal']};">MEDIANA HOMBRES</div>
                <div style="font-size: 22px; font-weight: 700;">${men_median:,.0f}</div>
            </div>
            
            <div style="background-color: {utils.PALETTE['white']}; border: 1px solid {utils.PALETTE['grey_light']}; border-radius: 8px; padding: 15px; margin-bottom: 12px; box-shadow: 0 2px 5px rgba(0,0,0,0.02);">
                <div style="font-size: 11px; font-weight: 700; opacity: 0.65; margin-bottom: 5px; color: {utils.PALETTE['orange']};">MEDIANA MUJERES</div>
                <div style="font-size: 22px; font-weight: 700;">${women_median:,.0f}</div>
            </div>
            
            <div style="background-color: {utils.PALETTE['white']}; border: 1px solid {utils.PALETTE['grey_light']}; border-radius: 8px; padding: 15px; margin-bottom: 12px; box-shadow: 0 2px 5px rgba(0,0,0,0.02);">
                <div style="font-size: 11px; font-weight: 700; opacity: 0.65; margin-bottom: 5px;">BRECHA DE GÉNERO (MUJERES VS HOMBRES)</div>
                <div style="font-size: 20px; font-weight: 700; color: {utils.PALETTE['orange_dark']};">
                    -{gender_gap_pct:.1f}%
                </div>
                <div style="font-size: 10px; color: {utils.PALETTE['grey_neutral']}; margin-top: 4px;">
                    Las mujeres ocupadas perciben una mediana de ingresos que es un {gender_gap_pct:.1f}% menor a la de los hombres.
                </div>
            </div>
            """, unsafe_allow_html=True)
            
    with col_gap_right:
        with st.container(border=True):
            st.markdown("<div class='card-title'>Ingreso Laboral Mediano por Nivel Educativo y Género</div>", unsafe_allow_html=True)
            
            # Calcular ingresos
            edu_gender_records = []
            for edu in utils.EDU_LEVELS_ORDER:
                for s_val, s_label in [(1, "Hombres"), (2, "Mujeres")]:
                    df_sub = df_gap_data[(df_gap_data['edu_mapped'] == edu) & (df_gap_data['sexo'] == s_val)]
                    if len(df_sub) > 0:
                        median_val = utils.get_weighted_median(df_sub, 'ytrabajocor', 'expr')
                    else:
                        median_val = np.nan
                    edu_gender_records.append({
                        "edu_level": edu,
                        "sexo": s_label,
                        "median_income": median_val
                    })
            df_edu_gender = pd.DataFrame(edu_gender_records)
            
            fig_edu_gender = go.Figure()
            
            # Hombres
            df_m_plot = df_edu_gender[df_edu_gender['sexo'] == "Hombres"]
            fig_edu_gender.add_trace(go.Bar(
                x=df_m_plot['edu_level'],
                y=df_m_plot['median_income'],
                name="Hombres",
                marker_color=utils.PALETTE['teal'],
                hovertext=[f"<b>Hombres</b><br>Nivel: {row['edu_level']}<br>Ingreso Mediano: ${row['median_income']:,.0f}" for _, row in df_m_plot.iterrows()],
                hoverinfo='text'
            ))
            
            # Mujeres
            df_w_plot = df_edu_gender[df_edu_gender['sexo'] == "Mujeres"]
            fig_edu_gender.add_trace(go.Bar(
                x=df_w_plot['edu_level'],
                y=df_w_plot['median_income'],
                name="Mujeres",
                marker_color=utils.PALETTE['orange'],
                hovertext=[f"<b>Mujeres</b><br>Nivel: {row['edu_level']}<br>Ingreso Mediano: ${row['median_income']:,.0f}" for _, row in df_w_plot.iterrows()],
                hoverinfo='text'
            ))
            
            fig_edu_gender.update_layout(
                barmode='group',
                yaxis=dict(
                    title="Ingreso mediano del trabajo ($/mes)",
                    tickprefix="$",
                    tickformat=",",
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
                height=320,
                margin=dict(l=10, r=10, t=10, b=110)
            )
            
            st.plotly_chart(fig_edu_gender, use_container_width=True, config={'displayModeBar': False})
            
    st.markdown("<div style='height: 25px;'></div>", unsafe_allow_html=True)
    
    # 3. GRÁFICO DE TASA DE CRECIMIENTO HISTÓRICO
    st.markdown("### Análisis de Crecimiento Histórico")
    
    @st.cache_data(show_spinner="Calculando tasas de crecimiento histórico...")
    def get_historical_growth():
        years = [2006, 2009, 2011, 2013, 2015, 2017, 2022, 2024]
        history = []
        for yr in years:
            filepath = os.path.join(utils.BASE_DIR, f"casen_{yr}.parquet")
            if os.path.exists(filepath):
                df = pd.read_parquet(filepath, columns=['esc', 'ytrabajocor', 'expr', 'activ'])
                
                # A. Escolaridad nacional promedio
                df_esc = df[(df['esc'] >= 0) & (df['expr'] > 0)]
                mean_esc = utils.get_weighted_mean(df_esc, 'esc', 'expr')
                
                # B. Ingreso líquido mediano nacional de trabajadores
                df_inc = df[(df['activ'] == 1) & (df['ytrabajocor'] > 0) & (df['expr'] > 0)]
                median_inc = utils.get_weighted_median(df_inc, 'ytrabajocor', 'expr')
                
                history.append({
                    "year": yr,
                    "escolaridad": mean_esc,
                    "ingreso_real": median_inc
                })
        df_hist = pd.DataFrame(history)
        
        df_hist['crec_escolaridad'] = df_hist['escolaridad'].pct_change() * 100
        df_hist['crec_ingreso'] = df_hist['ingreso_real'].pct_change() * 100
        
        return df_hist
        
    df_growth = get_historical_growth()
    df_growth_plot = df_growth.dropna().copy()
    
    periods = []
    yrs = df_growth['year'].tolist()
    for i in range(1, len(yrs)):
        periods.append(f"{yrs[i-1]} → {yrs[i]}")
        
    df_growth_plot['Periodo'] = periods
    
    with st.container(border=True):
        st.markdown("<div class='card-title'>Tasa de Crecimiento Histórico de Escolaridad e Ingresos Medianos (2006–2024)</div>", unsafe_allow_html=True)
        st.write("Este gráfico visualiza la variación porcentual de la escolaridad promedio nacional y el ingreso laboral mediano real con respecto al año de medición inmediatamente anterior de la encuesta CASEN.")
        
        metric_choice = st.radio(
            "Seleccionar indicador de crecimiento:",
            options=["Ingreso Laboral Mediano", "Escolaridad Promedio Nacional"],
            horizontal=True
        )
        
        fig_growth = go.Figure()
        
        if "Ingreso" in metric_choice:
            y_vals = df_growth_plot['crec_ingreso']
            color_growth = utils.PALETTE['orange']
            name_growth = "Crecimiento del Ingreso (%)"
            hover_growth_text = [
                f"<b>Período:</b> {p}<br><b>Crecimiento Ingreso:</b> {y_vals.iloc[idx]:.2f}%<br>"
                f"<b>Ingreso Final:</b> ${df_growth_plot.iloc[idx]['ingreso_real']:,.0f}"
                for idx, p in enumerate(periods)
            ]
        else:
            y_vals = df_growth_plot['crec_escolaridad']
            color_growth = utils.PALETTE['teal']
            name_growth = "Crecimiento de Escolaridad (%)"
            hover_growth_text = [
                f"<b>Período:</b> {p}<br><b>Crecimiento Escolaridad:</b> {y_vals.iloc[idx]:.2f}%<br>"
                f"<b>Escolaridad Final:</b> {df_growth_plot.iloc[idx]['escolaridad']:.2f} años"
                for idx, p in enumerate(periods)
            ]
            
        fig_growth.add_trace(go.Bar(
            x=df_growth_plot['Periodo'],
            y=y_vals,
            marker=dict(color=color_growth, line=dict(color=utils.PALETTE['white'], width=0.5)),
            hoverinfo='text',
            hovertext=hover_growth_text,
            name=name_growth
        ))
        
        for idx, val in enumerate(y_vals):
            sign_bar = "+" if val >= 0 else ""
            fig_growth.add_annotation(
                x=df_growth_plot['Periodo'].iloc[idx],
                y=val + (0.5 if val >= 0 else -1.2),
                text=f"{sign_bar}{val:.1f}%",
                showarrow=False,
                font=dict(size=10, color=utils.PALETTE['dark'], weight='bold'),
                xanchor='center',
                yanchor='bottom' if val >= 0 else 'top'
            )
            
        fig_growth.add_hline(y=0, line_dash="dash", line_color=utils.PALETTE['grey_neutral'], line_width=1)
        
        fig_growth.update_layout(
            yaxis=dict(
                title="Tasa de variación porcentual (%)",
                ticksuffix="%",
                gridcolor="rgba(15, 10, 10, 0.05)"
            ),
            xaxis=dict(
                title="Período entre mediciones CASEN"
            ),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(family="Outfit, sans-serif", color=utils.PALETTE['dark']),
            height=380,
            margin=dict(l=10, r=10, t=10, b=10)
        )
        
        st.plotly_chart(fig_growth, use_container_width=True, config={'displayModeBar': False})

except Exception as e:
    st.error(f"Error procesando los datos de brecha salarial o crecimiento: {e}")
