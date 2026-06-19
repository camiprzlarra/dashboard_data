import streamlit as st
import json
import numpy as np
import pandas as pd
import geopandas as gpd
import pydeck as pdk
import utils

# Inyectar estilos premium
utils.inject_premium_css()

# Header superior principal
st.markdown("""
<div class="main-header">
    <span class="header-breadcrumb">CENSO &gt; ANÁLISIS TERRITORIAL</span>
</div>
""", unsafe_allow_html=True)

st.title("Análisis Territorial y Autocorrelación Espacial")
st.markdown("""
Examen de la distribución espacial de la educación por comuna en Chile basándose en microdatos del **Censo** 
y el cálculo de la **Autocorrelación Espacial Local (LISA)**.
""")

# Cargar datos precalculados
try:
    gdf, moran_stats = utils.load_comunas_lisa_data()
    national_mean = moran_stats["national_mean"]
    
    # 1. Filtros y Configuración en el Sidebar
    st.sidebar.markdown("### FILTROS DE MAPA")
    
    # Slider de umbral de años de escolaridad
    min_esc = float(gdf['schooling_mean'].min())
    max_esc = float(gdf['schooling_mean'].max())
    
    esc_threshold = st.sidebar.slider(
        "Filtrar Rango de Escolaridad (Años):",
        min_value=round(min_esc, 1),
        max_value=round(max_esc, 1),
        value=(round(min_esc, 1), round(max_esc, 1)),
        step=0.1,
        help="Atenúa en el mapa las comunas que estén fuera de este rango."
    )
    
    st.sidebar.markdown("<hr style='margin: 15px 0px; border-color: rgba(245, 239, 237, 0.15);'>", unsafe_allow_html=True)
    st.sidebar.markdown("### DETALLE COMUNAL")
    
    # Dropdown de comuna
    comunas_list = sorted(gdf['nom_comuna'].unique())
    selected_comuna = st.sidebar.selectbox(
        "Seleccionar Comuna:",
        options=comunas_list,
        index=comunas_list.index("Santiago") if "Santiago" in comunas_list else 0
    )
    
    # Layout de 2 columnas: Mapas a la izquierda (ancho 3), Panel de detalle a la derecha (ancho 1)
    col_left, col_right = st.columns([3, 1])
    
    with col_left:
        # Fila de métricas del Moran Global en un contenedor
        st.markdown(f"""
        <div style="background-color: {utils.PALETTE['white']}; padding: 12px 18px; border: 1px solid {utils.PALETTE['grey_light']}; border-radius: 8px; margin-bottom: 15px;">
            <span style="font-weight: bold; color: {utils.PALETTE['dark']};">Autocorrelación Espacial Global:</span>
            <span style="margin-left: 10px; color: {utils.PALETTE['teal']}; font-weight: bold;">Moran's I: {moran_stats['moran_i']:.4f}</span>
            <span style="margin-left: 20px; color: {utils.PALETTE['orange']}; font-weight: bold;">p-valor: {moran_stats['moran_p']:.2e}</span>
            <span style="margin-left: 25px; font-size: 12px; color: {utils.PALETTE['grey_neutral']};">(Fuerte asociación espacial de escolaridad en Chile)</span>
        </div>
        """, unsafe_allow_html=True)
        
        # Mapear colores dinámicos para los mapas
        
        # A. Choropleth (Escolaridad Promedio)
        min_val = gdf['schooling_mean'].min()
        max_val = gdf['schooling_mean'].max()
        
        def assign_choropleth_colors(row):
            val = row['schooling_mean']
            # Si está fuera del umbral seleccionado, se le da un color gris muy transparente
            if val < esc_threshold[0] or val > esc_threshold[1]:
                return [211, 207, 207, 15] # Gris tenue translúcido
            
            # Interpolación lineal en la paleta de teales
            t = (val - min_val) / (max_val - min_val) if max_val > min_val else 0.5
            t = max(0.0, min(1.0, t))
            # De Light Teal (#E2F1F3 -> 226, 241, 243) a Dark Teal (#1B5865 -> 27, 88, 101)
            r = int(226 + t * (27 - 226))
            g = int(241 + t * (88 - 241))
            b = int(243 + t * (101 - 243))
            return [r, g, b, 200]
            
        gdf['color_choropleth'] = gdf.apply(assign_choropleth_colors, axis=1)
        
        # B. LISA Clusters (Convención cartográfica estándar)
        # HH: Rojo, LL: Azul, HL: Rosado, LH: Celeste, No Sig: Gris claro
        lisa_color_map = {
            'High-High': [225, 87, 89, 200],      # Rojo académico
            'Low-Low': [78, 121, 167, 200],       # Azul académico
            'High-Low': [255, 157, 154, 200],     # Rosado
            'Low-High': [160, 203, 232, 200],     # Celeste
            'No Significativo': [220, 220, 220, 80] # Gris suave
        }
        
        def assign_lisa_colors(row):
            val = row['schooling_mean']
            cluster = row['cluster']
            # Si está fuera del umbral seleccionado, se atenúa
            if val < esc_threshold[0] or val > esc_threshold[1]:
                return [211, 207, 207, 15]
            return lisa_color_map.get(cluster, [220, 220, 220, 80])
            
        gdf['color_lisa'] = gdf.apply(assign_lisa_colors, axis=1)
        
        # Convertir GeoDataFrame a GeoJSON para asegurar compatibilidad de arrays de color en Pydeck
        geojson_data = json.loads(gdf.to_json())
        
        # Parámetros del mapa de Pydeck (Posición inicial en Chile Central)
        view_state = pdk.ViewState(
            latitude=-33.5,
            longitude=-70.7,
            zoom=7.5,
            pitch=0,
            bearing=0
        )
        
        map1_col, map2_col = st.columns(2)
        
        # URL de estilo Basemap de CartoDB Positron (No requiere API Token)
        basemap_url = "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json"
        
        with map1_col:
            with st.container(border=True):
                st.markdown("<div class='card-title'>A. Escolaridad Promedio por Comuna</div>", unsafe_allow_html=True)
                
                layer_choro = pdk.Layer(
                    "GeoJsonLayer",
                    geojson_data,
                    pickable=True,
                    stroked=True,
                    filled=True,
                    extruded=False,
                    wireframe=True,
                    get_fill_color="properties ? properties.color_choropleth : [220, 220, 220, 100]",
                    get_line_color=[120, 120, 120, 50],
                    line_width_min_pixels=0.5
                )
                
                st.pydeck_chart(pdk.Deck(
                    layers=[layer_choro],
                    initial_view_state=view_state,
                    map_style=basemap_url,
                    tooltip={
                        "html": "<b>Comuna:</b> {nom_comuna}<br><b>Escolaridad:</b> {schooling_mean:.2f} años",
                        "style": {"color": "white", "font-family": "Outfit, sans-serif", "font-size": "12px"}
                    }
                ))
                
        with map2_col:
            with st.container(border=True):
                st.markdown("<div class='card-title'>B. Clústeres Espaciales LISA (Moran)</div>", unsafe_allow_html=True)
                
                layer_lisa = pdk.Layer(
                    "GeoJsonLayer",
                    geojson_data,
                    pickable=True,
                    stroked=True,
                    filled=True,
                    extruded=False,
                    wireframe=True,
                    get_fill_color="properties ? properties.color_lisa : [220, 220, 220, 100]",
                    get_line_color=[120, 120, 120, 50],
                    line_width_min_pixels=0.5
                )
                
                # Leyenda de mapa LISA
                st.pydeck_chart(pdk.Deck(
                    layers=[layer_lisa],
                    initial_view_state=view_state,
                    map_style=basemap_url,
                    tooltip={
                        "html": "<b>Comuna:</b> {nom_comuna}<br><b>Clúster:</b> {cluster}<br><b>Escolaridad:</b> {schooling_mean:.2f} años",
                        "style": {"color": "white", "font-family": "Outfit, sans-serif", "font-size": "12px"}
                    }
                ))
                
                # Leyenda explicativa en la parte inferior
                st.markdown("""
                <div style="display: flex; justify-content: space-around; flex-wrap: wrap; margin-top: 10px; font-size: 11px; font-weight: bold;">
                    <span><span style="color:#E15759;">■</span> High-High (Alto)</span>
                    <span><span style="color:#4E79A7;">■</span> Low-Low (Bajo)</span>
                    <span><span style="color:#A0CBE8;">■</span> Low-High (Atípico)</span>
                    <span><span style="color:#FF9D9A;">■</span> High-Low (Atípico)</span>
                    <span><span style="color:#D3D3D3;">■</span> No Significativo</span>
                </div>
                """, unsafe_allow_html=True)
                
    with col_right:
        # Panel de detalle de la comuna seleccionada
        comuna_data = gdf[gdf['nom_comuna'] == selected_comuna].iloc[0]
        
        st.markdown(f"### Comuna de {selected_comuna}")
        st.write(f"**Región:** {comuna_data['nom_region']}")
        
        st.markdown("<hr style='margin: 10px 0px; border-color: rgba(15, 10, 10, 0.08);'>", unsafe_allow_html=True)
        
        # Indicadores en bloque estético
        esc_comuna = comuna_data['schooling_mean']
        diff_national = comuna_data['diff_national_mean']
        cluster = comuna_data['cluster']
        
        # Formatear el clúster con color html
        cluster_style_map = {
            'High-High': f"background-color: #E15759; color: white;",
            'Low-Low': f"background-color: #4E79A7; color: white;",
            'High-Low': f"background-color: #FF9D9A; color: {utils.PALETTE['dark']};",
            'Low-High': f"background-color: #A0CBE8; color: {utils.PALETTE['dark']};",
            'No Significativo': f"background-color: {utils.PALETTE['grey_light']}; color: {utils.PALETTE['dark']};"
        }
        
        # Determinar flecha y color para diferencia nacional
        diff_color = utils.PALETTE['teal'] if diff_national >= 0 else utils.PALETTE['orange']
        diff_symbol = "▲" if diff_national >= 0 else "▼"
        
        st.markdown(f"""
        <div style="background-color: {utils.PALETTE['white']}; border: 1px solid {utils.PALETTE['grey_light']}; border-radius: 8px; padding: 15px; margin-bottom: 12px; box-shadow: 0 2px 5px rgba(0,0,0,0.02);">
            <div style="font-size: 11px; font-weight: 700; opacity: 0.65; margin-bottom: 5px;">ESCOLARIDAD PROMEDIO</div>
            <div style="font-size: 24px; font-weight: 700;">{esc_comuna:.2f} años</div>
        </div>
        
        <div style="background-color: {utils.PALETTE['white']}; border: 1px solid {utils.PALETTE['grey_light']}; border-radius: 8px; padding: 15px; margin-bottom: 12px; box-shadow: 0 2px 5px rgba(0,0,0,0.02);">
            <div style="font-size: 11px; font-weight: 700; opacity: 0.65; margin-bottom: 5px;">VS. PROMEDIO NACIONAL ({national_mean:.2f} años)</div>
            <div style="font-size: 18px; font-weight: 700; color: {diff_color};">
                {diff_symbol} {abs(diff_national):.2f} años
            </div>
        </div>
        
        <div style="background-color: {utils.PALETTE['white']}; border: 1px solid {utils.PALETTE['grey_light']}; border-radius: 8px; padding: 15px; margin-bottom: 12px; box-shadow: 0 2px 5px rgba(0,0,0,0.02);">
            <div style="font-size: 11px; font-weight: 700; opacity: 0.65; margin-bottom: 5px;">AUTOCORRELACIÓN ESPACIAL</div>
            <div style="display: inline-block; padding: 4px 10px; font-size: 12px; font-weight: 700; border-radius: 5px; {cluster_style_map.get(cluster, '')}">
                {cluster}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Cuadro de texto descriptivo del clúster
        cluster_desc = {
            'High-High': "La comuna pertenece a una zona de **alta escolaridad** rodeada de otras comunas que también tienen alta escolaridad (concentración de capital humano).",
            'Low-Low': "La comuna pertenece a una zona de **baja escolaridad** rodeada de otras comunas que también tienen baja escolaridad (rezago educativo concentrado).",
            'High-Low': "La comuna posee **alta escolaridad** pero se encuentra rodeada de comunas con baja escolaridad (comuna 'isla' de alto rendimiento educativo).",
            'Low-High': "La comuna posee **baja escolaridad** pero está rodeada de comunas con alta escolaridad (comuna 'isla' de rezago educativo).",
            'No Significativo': "No se observa una autocorrelación espacial estadísticamente significativa en el nivel de escolaridad de esta comuna."
        }
        st.info(cluster_desc.get(cluster, ""))

except Exception as e:
    st.error(f"Error cargando o procesando los datos espaciales: {e}")
    st.warning("Asegúrate de que 'Censo/comunas_lisa_precalculado.geojson' esté generado.")
