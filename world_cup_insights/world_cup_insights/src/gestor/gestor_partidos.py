"""
Módulo de consultas: expone métodos de solo lectura sobre el DataFrame de partidos.
"""
import pandas as pd


class GestorPartidos:
    """
    Expone métodos de solo lectura para consultar el DataFrame de partidos
    de la Copa Mundial (por id, equipo, año, sede, etc.).
    """

    def __init__(self, df: pd.DataFrame):
        self.df = df.reset_index(drop=True)
        self.df["id_partido"] = self.df.index

    def get_partido(self, id_partido: int) -> pd.Series:
        """Retorna un partido específico por su id (índice)."""
        return self.df.loc[self.df["id_partido"] == id_partido].squeeze()

    def get_por_equipo(self, equipo: str) -> pd.DataFrame:
        """Retorna todos los partidos donde un equipo jugó como local o visitante."""
        return self.df[
            (self.df["home_team"] == equipo) | (self.df["away_team"] == equipo)
        ]

    def get_por_anio(self, anio: int) -> pd.DataFrame:
        """Retorna todos los partidos de un año/edición específica."""
        return self.df[pd.to_datetime(self.df["date"]).dt.year == anio]

    def get_por_sede(self, pais: str) -> pd.DataFrame:
        """Retorna todos los partidos jugados en un país sede."""
        return self.df[self.df["country"] == pais]

    def ventaja_local(self) -> dict:
        #Calcula el porcentaje de victorias locales, visitantes y empates,
        #para medir si existe 'ventaja de local' en el Mundial (recordando que
        #muchos partidos son en cancha neutral).
        total = len(self.df)
        locales = (self.df["home_score"] > self.df["away_score"]).sum()
        visitantes = (self.df["home_score"] < self.df["away_score"]).sum()
        empates = (self.df["home_score"] == self.df["away_score"]).sum()
        return {
            "victorias_local_pct": round(locales / total * 100, 2),
            "victorias_visitante_pct": round(visitantes / total * 100, 2),
            "empates_pct": round(empates / total * 100, 2),
        }

    def get_goleadas(self, diferencia_minima: int = 4) -> pd.DataFrame:
        #Retorna partidos con una diferencia de goles mayor o igual al umbral.#
        dif = (self.df["home_score"] - self.df["away_score"]).abs()
        return self.df[dif >= diferencia_minima]

    def get_equipos_unicos(self) -> list:
        #Retorna la lista de todas las selecciones que han jugado un Mundial.#
        equipos = set(self.df["home_team"]) | set(self.df["away_team"])
        return sorted(equipos)

    def get_ediciones(self) -> list:
        #Retorna la lista de años/ediciones de Mundiales disponibles en el dataset.#
        return sorted(pd.to_datetime(self.df["date"]).dt.year.unique().tolist())

    def tabla_estadisticas_equipos(self) -> pd.DataFrame:
       # Retorna, para cada selección, sus estadísticas históricas en Copas
        #Mundiales: partidos jugados, goles a favor, goles en contra,
        #diferencia de goles, victorias, empates y derrotas.
        equipos = self.get_equipos_unicos()
        filas = []

        for equipo in equipos:
            como_local = self.df[self.df["home_team"] == equipo]
            como_visita = self.df[self.df["away_team"] == equipo]

            goles_favor = como_local["home_score"].sum() + como_visita["away_score"].sum()
            goles_contra = como_local["away_score"].sum() + como_visita["home_score"].sum()

            victorias = (
                (como_local["home_score"] > como_local["away_score"]).sum()
                + (como_visita["away_score"] > como_visita["home_score"]).sum()
            )
            empates = (
                (como_local["home_score"] == como_local["away_score"]).sum()
                + (como_visita["away_score"] == como_visita["home_score"]).sum()
            )
            partidos_jugados = len(como_local) + len(como_visita)
            derrotas = partidos_jugados - victorias - empates

            filas.append({
                "equipo": equipo,
                "partidos_jugados": partidos_jugados,
                "goles_a_favor": int(goles_favor),
                "goles_en_contra": int(goles_contra),
                "diferencia_goles": int(goles_favor - goles_contra),
                "victorias": int(victorias),
                "empates": int(empates),
                "derrotas": int(derrotas),
            })

        return pd.DataFrame(filas).sort_values("goles_a_favor", ascending=False).reset_index(drop=True)

    def estadisticas_de_equipo(self, equipo: str) -> dict:
        #Retorna las estadísticas históricas de una selección específica.#
        tabla = self.tabla_estadisticas_equipos()
        fila = tabla[tabla["equipo"] == equipo]
        if fila.empty:
            return {}
        return fila.iloc[0].to_dict()
