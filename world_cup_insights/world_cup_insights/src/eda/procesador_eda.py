"""
Módulo de EDA: limpieza, columnas derivadas y estadística descriptiva.
"""
import pandas as pd
import numpy as np


class ProcesadorEDA:

    def __init__(self, df: pd.DataFrame):
        self.df_original = df.copy()
        self.df = df.copy()

    def limpieza_datos(self) -> pd.DataFrame:
        self.df["date"] = pd.to_datetime(self.df["date"])
        self.df["home_score"] = self.df["home_score"].fillna(0).astype(int)
        self.df["away_score"] = self.df["away_score"].fillna(0).astype(int)
        self.df["home_team"] = self.df["home_team"].str.strip()
        self.df["away_team"] = self.df["away_team"].str.strip()
        self.df["neutral"] = self.df["neutral"].astype(bool)
        self.df = self.df.drop_duplicates()
        return self.df

    def crear_columnas_derivadas(self) -> pd.DataFrame:
        self.df["anio"] = self.df["date"].dt.year
        self.df["total_goles"] = self.df["home_score"] + self.df["away_score"]
        self.df["diferencia_goles"] = self.df["home_score"] - self.df["away_score"]

        condiciones = [
            self.df["home_score"] > self.df["away_score"],
            self.df["home_score"] < self.df["away_score"],
        ]
        opciones = ["Local", "Visitante"]
        self.df["ganador"] = np.select(condiciones, opciones, default="Empate")

        # Variables numéricas adicionales (para enriquecer la matriz de correlación)
        self.df["cancha_neutral_num"] = self.df["neutral"].astype(int)
        self.df["es_pais_anfitrion"] = (
            self.df["home_team"] == self.df["country"]
        ).astype(int)
        self.df["gano_local"] = (self.df["ganador"] == "Local").astype(int)

        return self.df

    def resumen_descriptivo(self) -> pd.DataFrame:
        #Retorna estadística descriptiva (mean, std, min, max, etc.) de columnas numéricas.#
        columnas = ["home_score", "away_score", "total_goles", "diferencia_goles"]
        return self.df[columnas].describe()

    def matriz_correlacion(self, columnas=None) -> pd.DataFrame:
        #Retorna la matriz de correlación entre variables numéricas.#
        if columnas is None:
            columnas = [
                "anio",
                "home_score",
                "away_score",
                "total_goles",
                "diferencia_goles",
                "cancha_neutral_num",
                "es_pais_anfitrion",
                "gano_local",
            ]
        columnas = [c for c in columnas if c in self.df.columns]
        return self.df[columnas].corr()

    def goles_promedio_por_edicion(self) -> pd.DataFrame:
        #Promedio de goles por partido en cada edición del Mundial.#
        return self.df.groupby("anio")["total_goles"].mean().reset_index(
            name="promedio_goles"
        )

    def detectar_outliers_goles(self) -> pd.DataFrame:
        #Detecta partidos con un total de goles atípico (método IQR).#
        q1 = self.df["total_goles"].quantile(0.25)
        q3 = self.df["total_goles"].quantile(0.75)
        iqr = q3 - q1
        limite_superior = q3 + 1.5 * iqr
        return self.df[self.df["total_goles"] > limite_superior]

    def mejor_diferencia_historica(self) -> pd.DataFrame:
        #Selección con mejor diferencia de goles acumulada histórica.#
        local = self.df.groupby("home_team")["diferencia_goles"].sum()
        visitante = self.df.groupby("away_team")["diferencia_goles"].sum() * -1
        total = local.add(visitante, fill_value=0).sort_values(ascending=False)
        return total.reset_index().rename(
            columns={"index": "equipo", 0: "diferencia_goles_total"}
        )

    def anfitrion_llega_semifinales(self) -> pd.DataFrame:
        #Estima, por edición, si el país anfitrión llegó al menos a semifinales.#
        df = self.df.copy()
        df["anio"] = df["date"].dt.year if "anio" not in df.columns else df["anio"]

        filas = []
        for anio, grupo in df.groupby("anio"):
            grupo = grupo.sort_values("date")
            anfitrion = grupo["country"].mode()[0]
            fechas_finales = sorted(grupo["date"].unique())[-3:]
            partidos_finales = grupo[grupo["date"].isin(fechas_finales)]
            llego_semis = (
                anfitrion in partidos_finales["home_team"].values
                or anfitrion in partidos_finales["away_team"].values
            )
            filas.append({
                "anio": int(anio),
                "anfitrion": anfitrion,
                "llego_semifinales": bool(llego_semis),
            })

        return pd.DataFrame(filas)

    def probabilidad_anfitrion_semifinales(self) -> float:
        #Retorna el % de ediciones en que el anfitrión llegó al menos a semifinales.#
        detalle = self.anfitrion_llega_semifinales()
        return round(detalle["llego_semifinales"].mean() * 100, 2)

    def ejecutar_pipeline_completo(self) -> pd.DataFrame:
        #Corre limpieza + columnas derivadas en un solo paso.#
        self.limpieza_datos()
        self.crear_columnas_derivadas()
        return self.df
