"""
Punto de entrada del proyecto World Cup Insights.
Corre todo el pipeline: ingesta -> EDA -> guardado de datos procesados.
"""
from ingesta.cargador_datos import CargadorDatos
from gestor.gestor_partidos import GestorPartidos
from eda.procesador_eda import ProcesadorEDA


def main():
    # 1. Ingesta
    cargador = CargadorDatos(
        ruta_raw="../data/raw/partidos-mundial.csv",
        ruta_processed="../data/processed/partidos-mundial-procesado.csv",
    )
    df_mundial = cargador.ejecutar_pipeline_completo()
    print(f"Partidos de Copa Mundial descargados: {len(df_mundial)}")

    # 2. EDA (limpieza + columnas derivadas)
    eda = ProcesadorEDA(df_mundial)
    df_procesado = eda.ejecutar_pipeline_completo()
    print("Resumen descriptivo:")
    print(eda.resumen_descriptivo())

    # 3. Persistencia del dataset procesado
    cargador.guardar_procesado(df_procesado, formato="csv")
    cargador.guardar_procesado(df_procesado, formato="json")

    # 4. Consultas de ejemplo con GestorPartidos
    gestor = GestorPartidos(df_procesado)
    print("Ventaja de local:", gestor.ventaja_local())
    print("Ediciones disponibles:", gestor.get_ediciones())


if __name__ == "__main__":
    main()
