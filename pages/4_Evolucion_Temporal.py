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
    <span class="header-breadcrumb">CASEN HISTÓRICA &gt; EVOLUCIÓN TEMPORAL</span>
</div>
""", unsafe_allow_html=True)

st.title("Evolución Temporal y Proyecciones a 2030")
st.markdown("""
Análisis longitudinal de la escolaridad promedio por quintiles de ingresos entre **2006 y 2024**, 
junto con una **proyección prospectiva al año 2030** basada en modelos de tendencia lineal.
""")

# Cargar datos históricos
try:
    df_schooling = utils.load_historical_quintiles_data()
    
    if len(df_schooling) == 0:
        st.error("No se encontraron datos históricos de escolaridad en los archivos parquet del proyecto.")
    else:
        # Pivotear datos históricos
        pivot_df = df_schooling.pivot(index='year', columns='quintil', values='schooling_mean')
        
        # 1. CÁLCULO DE PROYECCIONES A 2030 (Regresión Lineal Simple)
        years_proj = [2024, 2026, 2028, 2030]
        projection_records = []
        
        # Ajustar una regresión por cada quintil
        slopes = {}
        intercepts = {}
        
        for q in range(1, 6):
            x = pivot_df.index.values
            y = pivot_df[q].values
            
            # Ajustar modelo lineal y = m*x + c
            slope, intercept = np.polyfit(x, y, 1)
            slopes[q] = slope
            intercepts[q] = intercept
            
            # Calcular proyecciones
            for yr in years_proj:
                y_val = slope * yr + intercept
                projection_records.append({
                    "year": yr,
                    "quintil": q,
                    "schooling_proj": y_val
                })
                
        df_proj = pd.DataFrame(projection_records)
        pivot_proj = df_proj.pivot(index='year', columns='quintil', values='schooling_proj')
        
        # 2. DIBUJAR GRÁFICO CON PLOTLY
        fig = go.Figure()
        
        # Paleta de colores e identificadores de quintiles
        quintile_colors = {
            1: utils.PALETTE['grey_light'],
            2: utils.PALETTE['teal_light'],
            3: utils.PALETTE['teal'],
            4: utils.PALETTE['olive'],
            5: utils.PALETTE['orange']
        }
        
        quintile_labels = {
            1: "Quintil 1 (20% ingresos más bajos)",
            2: "Quintil 2",
            3: "Quintil 3",
            4: "Quintil 4",
            5: "Quintil 5 (20% ingresos más altos)"
        }
        
        # A. Agregar área sombreada de desigualdad (entre Quintil 1 y Quintil 5)
        # Combinar años históricos y proyectados para crear un polígono continuo
        all_years = list(pivot_df.index) + [2026, 2028, 2030]
        
        # Obtener valores combinados (histórico + proyección) para Q1 y Q5
        q1_vals = []
        q5_vals = []
        for yr in all_years:
            if yr in pivot_df.index:
                q1_vals.append(pivot_df.loc[yr, 1])
                q5_vals.append(pivot_df.loc[yr, 5])
            else:
                q1_vals.append(pivot_proj.loc[yr, 1])
                q5_vals.append(pivot_proj.loc[yr, 5])
                
        # Agregar traza de Quintil 1 como base invisible para el sombreado
        fig.add_trace(go.Scatter(
            x=all_years,
            y=q1_vals,
            mode='lines',
            line=dict(width=0),
            hoverinfo='skip',
            showlegend=False,
            name="Q1_Base"
        ))
        
        # Agregar traza de Quintil 5 con fill 'tonexty' para rellenar el espacio
        fig.add_trace(go.Scatter(
            x=all_years,
            y=q5_vals,
            mode='lines',
            line=dict(width=0),
            fill='tonexty',
            fillcolor='rgba(217, 108, 6, 0.06)', # Naranja muy traslúcido
            hoverinfo='skip',
            showlegend=True,
            name="Área de Desigualdad Socioeconómica"
        ))
        
        # B. Agregar las trazas reales para cada quintil (Histórico y Proyección)
        for q in range(1, 6):
            color = quintile_colors[q]
            label = quintile_labels[q]
            
            # 1. Histórico (Línea sólida con marcadores)
            fig.add_trace(go.Scatter(
                x=pivot_df.index,
                y=pivot_df[q],
                mode='lines+markers',
                name=label,
                line=dict(color=color, width=2.5),
                marker=dict(size=6, symbol='circle'),
                hovertext=[f"<b>{label}</b><br><b>Año:</b> {yr}<br><b>Escolaridad:</b> {val:.2f} años" for yr, val in pivot_df[q].items()],
                hoverinfo='text'
            ))
            
            # 2. Proyección (Línea discontinua)
            fig.add_trace(go.Scatter(
                x=pivot_proj.index,
                y=pivot_proj[q],
                mode='lines',
                line=dict(color=color, width=2.2, dash='dash'),
                showlegend=False,
                hovertext=[f"<b>{label} (Proyectado)</b><br><b>Año:</b> {yr}<br><b>Escolaridad:</b> {val:.2f} años" for yr, val in pivot_proj[q].items()],
                hoverinfo='text'
            ))
            
        fig.update_layout(
            xaxis=dict(
                title="Año de medición",
                tickmode='array',
                tickvals=all_years,
                gridcolor="rgba(15, 10, 10, 0.05)"
            ),
            yaxis=dict(
                title="Años de escolaridad promedio",
                range=[4.0, 16.5],
                gridcolor="rgba(15, 10, 10, 0.05)"
            ),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(family="Outfit, sans-serif", color=utils.PALETTE['dark']),
            legend=dict(
                orientation="h",
                yanchor="top",
                y=-0.3,
                xanchor="center",
                x=0.5,
                font=dict(size=13)
            ),
            height=500,
            margin=dict(l=10, r=10, t=20, b=100)
        )
        
        with st.container(border=True):
            st.markdown("<div class='card-title'>Trayectoria Histórica y Proyección a 2030 de la Escolaridad Promedio</div>", unsafe_allow_html=True)
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            
        # 3. TABLA COMPARATIVA DE BRECHA Y PROYECCIONES
        st.markdown("### Tabla Detallada de Brecha y Proyecciones")
        
        # Calcular brechas históricas y proyectadas
        hist_gap_2006 = pivot_df.loc[2006, 5] - pivot_df.loc[2006, 1]
        hist_gap_2024 = pivot_df.loc[2024, 5] - pivot_df.loc[2024, 1]
        proj_gap_2030 = pivot_proj.loc[2030, 5] - pivot_proj.loc[2030, 1]
        
        # Crear DataFrame resumen
        summary_records = []
        for q in range(1, 6):
            summary_records.append({
                "Quintil de Ingresos": f"Quintil {q}",
                "Escolaridad 2006 (Años)": f"{pivot_df.loc[2006, q]:.2f}",
                "Escolaridad 2024 (Años)": f"{pivot_df.loc[2024, q]:.2f}",
                "Proyectado 2030 (Años)": f"{pivot_proj.loc[2030, q]:.2f}",
                "Variación Anual Estimada (Años/Año)": f"+{slopes[q]:.3f}",
                "Ecuación del Modelo Lineal": f"y = {slopes[q]:.3f}x + {intercepts[q]:.2f}"
            })
        df_summary = pd.DataFrame(summary_records)
        
        col_t1, col_t2 = st.columns([2, 1])
        
        with col_t1:
            with st.container(border=True):
                st.markdown("<div class='card-title'>Resumen Estadístico y Ecuaciones de Tendencia</div>", unsafe_allow_html=True)
                st.table(df_summary)
                
        with col_t2:
            with st.container(border=True):
                st.markdown("<div class='card-title'>Análisis de la Brecha Socioeconómica</div>", unsafe_allow_html=True)
                st.write("""
                La brecha absoluta de años de escolaridad promedio entre el Quintil 5 (ingresos altos) 
                y el Quintil 1 (ingresos bajos) muestra la siguiente tendencia histórica y proyectada:
                """)
                st.markdown(f"""
                - **Brecha en 2006:** `{hist_gap_2006:.2f} años`
                - **Brecha en 2024:** `{hist_gap_2024:.2f} años`
                - **Brecha Proyectada a 2030:** `{proj_gap_2030:.2f} años`
                """)
                
                # Explicación del modelo
                if proj_gap_2030 < hist_gap_2024:
                    st.success("📉 **Conclusión del Modelo:** Se proyecta una **disminución progresiva** en la brecha de desigualdad educativa de aquí al año 2030, debido a un ritmo de crecimiento más acelerado en la escolaridad de los quintiles más bajos.")
                else:
                    st.warning("📈 **Conclusión del Modelo:** Se proyecta una **estabilización o ampliación** de la desigualdad educativa, lo que resalta la necesidad de políticas enfocadas en la retención escolar en los quintiles vulnerables.")

        # 4. EVOLUCIÓN HISTÓRICA DEL INGRESO MEDIANO POR NIVEL EDUCATIVO
        st.markdown("<div style='height: 25px;'></div>", unsafe_allow_html=True)
        st.markdown("### Evolución Histórica del Ingreso Mediano por Nivel Educativo (2006–2024)")
        st.write("Análisis longitudinal del ingreso real líquido del trabajo de la población ocupada para los niveles de educación Básica, Media y Técnica.")
        
        try:
            df_hist_inc = utils.load_historical_education_income_data()
            if len(df_hist_inc) > 0:
                fig_inc_hist = go.Figure()
                
                # Colores
                edu_color_map = {
                    "Básica": utils.PALETTE['grey_neutral'],
                    "Media": utils.PALETTE['teal_light'],
                    "Técnica": utils.PALETTE['teal']
                }
                
                for edu in ["Básica", "Media", "Técnica"]:
                    df_sub = df_hist_inc[df_hist_inc['edu_level'] == edu]
                    if len(df_sub) > 0:
                        fig_inc_hist.add_trace(go.Scatter(
                            x=df_sub['year'],
                            y=df_sub['median_income'],
                            mode='lines+markers',
                            name=f"Educación {edu}",
                            line=dict(color=edu_color_map[edu], width=2.5),
                            marker=dict(size=6, symbol='circle'),
                            hovertext=[f"<b>Educación {edu}</b><br><b>Año:</b> {row['year']}<br><b>Ingreso Mediano:</b> ${row['median_income']:,.0f}" for _, row in df_sub.iterrows()],
                            hoverinfo='text'
                        ))
                        
                fig_inc_hist.update_layout(
                    xaxis=dict(
                        title="Año de medición",
                        tickmode='array',
                        tickvals=[2006, 2009, 2011, 2013, 2015, 2017, 2022, 2024],
                        gridcolor="rgba(15, 10, 10, 0.05)"
                    ),
                    yaxis=dict(
                        title="Ingreso mediano líquido ($/mes)",
                        tickprefix="$",
                        tickformat=",",
                        gridcolor="rgba(15, 10, 10, 0.05)"
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
                    height=450,
                    margin=dict(l=10, r=10, t=10, b=90)
                )
                
                with st.container(border=True):
                    st.markdown("<div class='card-title'>Trayectoria del Ingreso Líquido Mediano por Nivel de Instrucción</div>", unsafe_allow_html=True)
                    st.plotly_chart(fig_inc_hist, use_container_width=True, config={'displayModeBar': False})
            else:
                st.info("No hay datos de ingresos históricos disponibles.")
        except Exception as ex_inc:
            st.error(f"Error procesando ingresos históricos: {ex_inc}")

except Exception as e:
    st.error(f"Error procesando evolución temporal o proyecciones: {e}")

