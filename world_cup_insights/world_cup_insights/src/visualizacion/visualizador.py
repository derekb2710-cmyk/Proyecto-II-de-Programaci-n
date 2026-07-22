
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd


class Visualizador:
    #Crea gráficos (líneas, barras, heatmaps, dispersión)
    COLOR_PRIMARIO = "#FFC300"
    COLOR_SECUNDARIO = "#1E7A46"
    COLOR_TERCIARIO = "#0B1F13"
    PALETA_CATEGORICA = ["#FFC300", "#1E7A46", "#4FC3F7", "#E63946"]

    def __init__(self, df: pd.DataFrame):
        self.df = df

    def evolucion_goles_por_edicion(self) -> go.Figure:
        # qué Mundial se metieron más goles por partido#
        promedio = self.df.groupby("anio")["total_goles"].mean().reset_index()
        fig = px.line(
            promedio, x="anio", y="total_goles", markers=True,
            title="Promedio de goles por partido en cada edición del Mundial",
            labels={"anio": "Año", "total_goles": "Promedio de goles por partido"},
            color_discrete_sequence=[self.COLOR_PRIMARIO],
        )
        return fig

    def distribucion_resultados(self) -> go.Figure:
        #calcula victorias, derrotas y empates#
        conteo = self.df["ganador"].value_counts().reset_index()
        conteo.columns = ["resultado", "cantidad"]
        fig = px.bar(
            conteo, x="resultado", y="cantidad", color="resultado",
            title="Distribución de resultados: Local vs Visitante vs Empate",
            color_discrete_sequence=self.PALETA_CATEGORICA,
        )
        return fig

    def top_equipos_goleadores(self, top_n=10) -> go.Figure:
        #qué selección tiene la mejor diferencia de goles histórica#
        local = self.df.groupby("home_team")["diferencia_goles"].sum()
        visitante = self.df.groupby("away_team")["diferencia_goles"].sum() * -1
        total = local.add(visitante, fill_value=0).sort_values(ascending=False).head(top_n)
        fig = px.bar(
            x=total.values, y=total.index, orientation="h",
            title=f"Top {top_n} selecciones con mejor diferencia de goles histórica",
            labels={"x": "Diferencia de goles acumulada", "y": "Selección"},
            color_discrete_sequence=[self.COLOR_SECUNDARIO],
        )
        fig.update_yaxes(categoryorder="total ascending")
        return fig

    def heatmap_correlacion(self, matriz_corr: pd.DataFrame) -> go.Figure:
        #Heatmap de correlación entre variables numéricas del partido.#
        fig = px.imshow(
            matriz_corr, text_auto=".2f", color_continuous_scale="RdBu_r",
            title="Matriz de correlación entre variables del partido",
        )
        return fig

    def dispersión_goles_local_visitante(self) -> go.Figure:
        #Scatter: relación entre goles del local y del visitante por partido.#
        fig = px.scatter(
            self.df, x="home_score", y="away_score", color="ganador",
            hover_data=["home_team", "away_team", "anio"],
            title="Goles del equipo local vs. goles del equipo visitante",
            color_discrete_sequence=self.PALETA_CATEGORICA,
        )
        return fig

    def ventaja_pais_sede(self, gestor) -> go.Figure:
        #Historia: ¿el país sede gana más partidos que el promedio?#
        stats_generales = gestor.ventaja_local()

        df_sede = self.df[self.df["home_team"] == self.df["country"]]
        ganados_sede = (df_sede["ganador"] == "Local").sum()
        total_sede = len(df_sede)
        pct_sede = round(ganados_sede / total_sede * 100, 2) if total_sede else 0

        fig = go.Figure(data=[
            go.Bar(
                x=["Victoria local (general)", "Victoria del país sede"],
                y=[stats_generales["victorias_local_pct"], pct_sede],
                marker_color=[self.COLOR_SECUNDARIO, self.COLOR_PRIMARIO],
            )
        ])
        fig.update_layout(
            title="¿El país sede tiene ventaja adicional al jugar en casa?",
            yaxis_title="% de victorias",
        )
        return fig

    def histograma_goles_totales(self) -> go.Figure:
        #Distribución del total de goles por partido.#
        fig = px.histogram(
            self.df, x="total_goles", nbins=15,
            title="Distribución del total de goles por partido en Mundiales",
            color_discrete_sequence=[self.COLOR_PRIMARIO],
        )
        return fig

    def ranking_goles_por_edicion(self, top_n=10) -> go.Figure:

        resumen = self.df.groupby("anio").agg(
            promedio_goles=("total_goles", "mean"),
            total_goles=("total_goles", "sum"),
            partidos=("total_goles", "count"),
        ).round(2).reset_index()

        resumen = resumen.sort_values("promedio_goles", ascending=False).head(top_n)

        fig = px.bar(
            resumen, x="promedio_goles", y="anio", orientation="h",
            hover_data={"total_goles": True, "partidos": True, "anio": False},
            title=f"Top {top_n} Mundiales con más goles por partido (promedio)",
            labels={"promedio_goles": "Promedio de goles por partido", "anio": "Año"},
            color_discrete_sequence=[self.COLOR_PRIMARIO],
        )
        fig.update_yaxes(type="category", categoryorder="total ascending")
        return fig

    def anfitrion_en_semifinales(self, detalle_anfitriones: pd.DataFrame) -> go.Figure:

        detalle = detalle_anfitriones.sort_values("anio").copy()
        detalle["resultado"] = detalle["llego_semifinales"].map(
            {True: "Llegó a semifinales", False: "No llegó a semifinales"}
        )
        detalle["altura"] = 1

        fig = px.bar(
            detalle, x="anio", y="altura", color="resultado",
            hover_data={"anfitrion": True, "altura": False},
            title="¿El país anfitrión llega al menos a semifinales en su propio Mundial?",
            labels={"anio": "Año"},
            color_discrete_map={
                "Llegó a semifinales": self.COLOR_PRIMARIO,
                "No llegó a semifinales": self.COLOR_TERCIARIO,
            },
        )
        fig.update_yaxes(visible=False, title=None)
        fig.update_layout(showlegend=True, legend_title_text="")
        return fig

    def probabilidad_anfitrion_gauge(self, probabilidad: float) -> go.Figure:
        #Indicador tipo velocímetro con la probabilidad histórica del anfitrión.#
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=probabilidad,
            number={"suffix": "%"},
            title={"text": "Probabilidad histórica: anfitrión llega a semifinales"},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": self.COLOR_PRIMARIO},
                "steps": [
                    {"range": [0, 33], "color": "#3A3A3A"},
                    {"range": [33, 66], "color": "#5A5A3A"},
                    {"range": [66, 100], "color": self.COLOR_SECUNDARIO},
                ],
            },
        ))
        return fig
