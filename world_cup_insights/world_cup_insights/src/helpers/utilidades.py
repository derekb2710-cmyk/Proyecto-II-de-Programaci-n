"""
Funciones auxiliares reutilizables para validaciones y formateo.
"""


class Utilidades:

    @staticmethod
    def formatear_porcentaje(valor: float) -> str:
        return f"{valor:.2f}%"

    @staticmethod
    def validar_columnas(df, columnas_requeridas: list) -> bool:
        #Verifica que el DataFrame contenga todas las columnas requeridas.#
        faltantes = [c for c in columnas_requeridas if c not in df.columns]
        if faltantes:
            print(f"Faltan columnas: {faltantes}")
            return False
        return True

    @staticmethod
    def normalizar_nombre_equipo(nombre: str) -> str:
        return nombre.strip().title()
