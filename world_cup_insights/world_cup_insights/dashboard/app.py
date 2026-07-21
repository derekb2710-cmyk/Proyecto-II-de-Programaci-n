"""
Dashboard interactivo de World Cup Insights (Streamlit).
Ejecutar con: streamlit run dashboard/app.py
"""
import sys
import os
import streamlit as st
import pandas as pd

# Permite importar las clases desde src/
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from ingesta.cargador_datos import CargadorDatos
from gestor.gestor_partidos import GestorPartidos
from eda.procesador_eda import ProcesadorEDA
from visualizacion.visualizador import Visualizador

st.set_page_config(page_title="World Cup Insights", page_icon="⚽", layout="wide")

RUTA_RAW = "data/raw/partidos-mundial.csv"
RUTA_PROCESSED = "data/processed/partidos-mundial-procesado.csv"


@st.cache_data
def cargar_datos():
    """Descarga (si hace falta) y devuelve el dataset ya procesado."""
    if not os.path.exists(RUTA_RAW):
        cargador = CargadorDatos(ruta_raw=RUTA_RAW, ruta_processed=RUTA_PROCESSED)
        df_mundial = cargador.ejecutar_pipeline_completo()
    else:
        df_mundial = pd.read_csv(RUTA_RAW)

    eda = ProcesadorEDA(df_mundial)
    df_procesado = eda.ejecutar_pipeline_completo()
    return df_procesado, eda


st.title("⚽ World Cup Insights")
st.markdown("Dashboard interactivo — Copa Mundial de la FIFA 1930-2026")

with st.spinner("Cargando datos..."):
    df, eda = cargar_datos()

gestor = GestorPartidos(df)
viz = Visualizador(df)

# Sidebar: filtros
st.sidebar.header("Filtros")
ediciones = ["Todas"] + gestor.get_ediciones()
edicion_sel = st.sidebar.selectbox("Edición del Mundial", ediciones)

equipos = ["Todos"] + gestor.get_equipos_unicos()
equipo_sel = st.sidebar.selectbox("Selección", equipos)

df_filtrado = df.copy()
if edicion_sel != "Todas":
    df_filtrado = df_filtrado[df_filtrado["anio"] == edicion_sel]
if equipo_sel != "Todos":
    df_filtrado = df_filtrado[
        (df_filtrado["home_team"] == equipo_sel) | (df_filtrado["away_team"] == equipo_sel)
    ]

#  KPIs
if equipo_sel != "Todos":
    goles_favor_sel = (
        df_filtrado.loc[df_filtrado["home_team"] == equipo_sel, "home_score"].sum()
        + df_filtrado.loc[df_filtrado["away_team"] == equipo_sel, "away_score"].sum()
    )
    goles_contra_sel = (
        df_filtrado.loc[df_filtrado["home_team"] == equipo_sel, "away_score"].sum()
        + df_filtrado.loc[df_filtrado["away_team"] == equipo_sel, "home_score"].sum()
    )

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Partidos totales", len(df_filtrado))
    col2.metric(f"Goles a favor de {equipo_sel}", int(goles_favor_sel))
    col3.metric(f"Goles en contra de {equipo_sel}", int(goles_contra_sel))
    col4.metric("Goles totales del partido (combinado)", int(df_filtrado["total_goles"].sum()))
    col5.metric("Promedio goles/partido", round(df_filtrado["total_goles"].mean(), 2))
else:
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Partidos totales", len(df_filtrado))
    col2.metric("Goles totales (combinado, ambos equipos)", int(df_filtrado["total_goles"].sum()))
    col3.metric("Promedio goles/partido", round(df_filtrado["total_goles"].mean(), 2))
    ventaja = gestor.ventaja_local()
    col4.metric("% Victorias local", f"{ventaja['victorias_local_pct']}%")

st.divider()

# Tabs de visualización
tab1, tab2, tab3, tab5, tab4 = st.tabs(
    ["Tendencias", "Equipos", "Correlaciones", "Anfitrión", "Datos crudos"]
)

with tab1:
    st.plotly_chart(viz.evolucion_goles_por_edicion(), width='stretch')
    st.plotly_chart(viz.ranking_goles_por_edicion(top_n=10), width='stretch')
    st.plotly_chart(viz.histograma_goles_totales(), width='stretch')

with tab2:
    st.plotly_chart(viz.top_equipos_goleadores(top_n=15), width='stretch')
    st.plotly_chart(viz.distribucion_resultados(), width='stretch')

    st.divider()
    st.subheader("Estadísticas por selección")
    st.caption(
        "goles_a_favor = goles que anotó esa selección. "
        "goles_en_contra = goles que le anotaron a ella. "
        "No confundir con 'total_goles' de un partido, que suma ambos equipos."
    )

    tabla_equipos = gestor.tabla_estadisticas_equipos()

    equipo_detalle = st.selectbox(
        "Consultar una selección específica", tabla_equipos["equipo"]
    )
    stats = gestor.estadisticas_de_equipo(equipo_detalle)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Partidos jugados", stats["partidos_jugados"])
    c2.metric("Goles a favor", stats["goles_a_favor"])
    c3.metric("Goles en contra", stats["goles_en_contra"])
    c4.metric("Diferencia de goles", stats["diferencia_goles"])
    c5, c6, c7 = st.columns(3)
    c5.metric("Victorias", stats["victorias"])
    c6.metric("Empates", stats["empates"])
    c7.metric("Derrotas", stats["derrotas"])

    st.markdown("**Tabla completa de todas las selecciones**")
    st.dataframe(tabla_equipos, width='stretch')

with tab3:
    matriz = eda.matriz_correlacion()
    st.plotly_chart(viz.heatmap_correlacion(matriz), width='stretch')
    st.plotly_chart(viz.dispersión_goles_local_visitante(), width='stretch')

with tab5:
    detalle_anfitriones = eda.anfitrion_llega_semifinales()
    probabilidad = eda.probabilidad_anfitrion_semifinales()

    col_a, col_b = st.columns([1, 2])
    with col_a:
        st.plotly_chart(viz.probabilidad_anfitrion_gauge(probabilidad), width='stretch')
    with col_b:
        st.plotly_chart(viz.anfitrion_en_semifinales(detalle_anfitriones), width='stretch')

    st.caption(
        "Nota: el dataset no incluye la ronda oficial de cada partido, por lo que "
        "'llegar a semifinales' se estima tomando los partidos jugados en las "
        "últimas 3 fechas distintas de cada edición (semifinales, tercer/cuarto "
        "puesto y final)."
    )
    st.dataframe(detalle_anfitriones, width='stretch')

with tab4:
    st.dataframe(df_filtrado, width='stretch')
