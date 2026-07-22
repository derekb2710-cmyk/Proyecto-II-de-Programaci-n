
import os
import requests
import pandas as pd


class CargadorDatos:
    #Se encarga de descargar el CSV público de partidos internacionales#

    URL_DEFAULT = (
        "https://raw.githubusercontent.com/martj42/"
        "international_results/master/results.csv"
    )

    def __init__(self, url=None, ruta_raw="data/raw/partidos-mundial.csv",
                 ruta_processed="data/processed/partidos-mundial-procesado.csv"):
        self.url = url or self.URL_DEFAULT
        self.ruta_raw = ruta_raw
        self.ruta_processed = ruta_processed
        self.df_crudo = None
        self.df_mundial = None

    def descargar(self) -> pd.DataFrame:
        #Descarga el CSV completo desde la URL pública.#
        respuesta = requests.get(self.url, timeout=30)
        respuesta.raise_for_status()

        ruta_temporal = "data/_temp_results.csv"
        os.makedirs(os.path.dirname(ruta_temporal), exist_ok=True)
        with open(ruta_temporal, "wb") as f:
            f.write(respuesta.content)

        self.df_crudo = pd.read_csv(ruta_temporal)
        os.remove(ruta_temporal)
        return self.df_crudo

    def filtrar_mundial(self) -> pd.DataFrame:
        #Filtra únicamente los partidos cuyo tournament sea 'FIFA World Cup'."""
        if self.df_crudo is None:
            raise ValueError("Primero debe llamar a descargar().")

        self.df_mundial = self.df_crudo[
            self.df_crudo["tournament"] == "FIFA World Cup"
        ].copy()
        return self.df_mundial

    def validar_datos(self) -> bool:
        #Valida que no existan valores nulos en columnas clave.#
        columnas_clave = ["date", "home_team", "away_team", "home_score", "away_score"]
        nulos = self.df_mundial[columnas_clave].isnull().sum().sum()
        if nulos > 0:
            print(f"Advertencia: se encontraron {nulos} valores nulos en columnas clave.")
        return nulos == 0

    def guardar_raw(self):
        #Guarda el subconjunto de la Copa Mundial en data/raw/.#
        os.makedirs(os.path.dirname(self.ruta_raw), exist_ok=True)
        self.df_mundial.to_csv(self.ruta_raw, index=False)
        print(f"Datos crudos guardados en: {self.ruta_raw}")

    def guardar_procesado(self, df_procesado: pd.DataFrame, formato="csv"):
        #Guarda el dataset ya procesado (con columnas derivadas) en data/processed/.#
        os.makedirs(os.path.dirname(self.ruta_processed), exist_ok=True)
        if formato == "csv":
            df_procesado.to_csv(self.ruta_processed, index=False)
        elif formato == "json":
            ruta_json = self.ruta_processed.replace(".csv", ".json")
            df_procesado.to_json(ruta_json, orient="records", indent=2)
        print(f"Datos procesados guardados en formato {formato}.")

    def ejecutar_pipeline_completo(self, forzar_descarga=False) -> pd.DataFrame:

        #Corre todo el flujo: descargar -> filtrar -> validar -> guardar raw.#
        if os.path.exists(self.ruta_raw) and not forzar_descarga:
            self.df_mundial = pd.read_csv(self.ruta_raw)
            print(f"Usando datos ya existentes en: {self.ruta_raw}")
            return self.df_mundial

        self.descargar()
        self.filtrar_mundial()
        self.validar_datos()
        self.guardar_raw()
        return self.df_mundial
