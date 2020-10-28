#!/usr/bin/python3


import sys
import pandas as pd

import funciones_procesado as f

# Print execution start notice
print('Executing data processing script...\n')

# Set folders to work on
try:
    carpeta_de_informacion = sys.argv[1]
except:
    carpeta_de_informacion = ("/home/alejandro/Documentos/Universidad/"
    "MII_2/TFM/TrabajoConDatos/informacion_procesada/")
print('Information folder is set as:\n{}\n'.format(carpeta_de_informacion))
try:
    carpeta_de_datos_centrales = sys.argv[2]
except:
    carpeta_de_datos_centrales = ("/home/alejandro/Documentos/"
    "Universidad/MII_2/TFM/TrabajoConDatos/info_descargada/"
    "informacion_centrales/")
print(
    ('Unidad de Programacion data folder is set as:\n{}\n'
     .format(carpeta_de_datos_centrales))
)

# Import list of Unidades de Programación participating in BRS 
# biddings.
participantes_secundaria = f.leer_participantes_secundaria(
    carpeta_de_informacion,
)

# Read information regarding company affiliation of all Unidades
# de Programación and create dictionaries with it.
(centrales_en_empresa, empresa_de_central) = (
    f.obtener_empresa_centrales(
        participantes_secundaria,
        carpeta_de_datos_centrales
    )
)

# Import power table previously obtained.
df_potencias = f.leer_tabla_potencia(carpeta_de_informacion)

# Create table with the power margins of different combinations of
# BRS and power dispatched.
df_margenes_potencia = f.obtener_margenes_potencia(
    df_potencias,
    carpeta_de_informacion,
)

# Create table with the power margins of every company.
df_margenes_potencia_empresas = f.obtener_margenes_potencia_empresas(
    df_margenes_potencia,
    centrales_en_empresa,
    carpeta_de_informacion
)

# Create table with the ilicit MW per hour for companies and Unidades
# de Programación.
df_mw_imposibles_centrales = (
    f.obtener_mw_imposibles(df_margenes_potencia)
)
df_mw_imposibles_empresas = (
    f.obtener_mw_imposibles(df_margenes_potencia_empresas)
)

# Create table stating whether the power margin was impossible or not.
# True if impossible.
df_horas_imposibles_centrales = (
    f.obtener_horas_imposibles(df_margenes_potencia)
)
df_horas_imposibles_empresas = (
    f.obtener_horas_imposibles(df_margenes_potencia_empresas)
)

# Import electricity market information.
df_mercado = f.leer_tabla_mercado(carpeta_de_informacion)

# Compute extra profit from the MWs of dubious legality.
df_ben_extra_centrales = (
    f.obtener_beneficio_extra(df_mw_imposibles_centrales,df_mercado)
)
df_ben_extra_empresas = (
    f.obtener_beneficio_extra(df_mw_imposibles_empresas,df_mercado)
)

# Obtain the correlation between these data and some relevant market
# information.
dic_df_empresas = {
    'MW imposibles':df_mw_imposibles_empresas,
    'Horas imposibles':df_horas_imposibles_empresas,
    'Beneficios imposibles':df_ben_extra_empresas,
}
dic_df_centrales = {
    'MW imposibles':df_mw_imposibles_centrales,
    'Horas imposibles':df_horas_imposibles_centrales,
    'Beneficios imposibles':df_ben_extra_centrales,
}
df_corr_empresas = f.obtener_correlaciones(df_mercado,dic_df_empresas)
df_corr_empresas.to_csv(
    carpeta_de_informacion+'correlaciones_empresas.csv',
    sep=';'
)
df_corr_centrales = f.obtener_correlaciones(
    df_mercado,dic_df_centrales,
)
df_corr_centrales.to_csv(
    carpeta_de_informacion+'correlaciones_centrales.csv',
    sep=';'
)

print('Task completed successfully.')
