#!/usr/bin/python3


import pandas as pd
import fnmatch
import os

import funciones_lectura as f


# Path to the folders that are going to be used. The raw power data 
# folder contains the I90DIA files. The information folder is the 
# destination for processed information. The raw market data folder
# contains data about the electricity market.
carpeta_de_datos_potencia = ("/home/alejandro/Documentos/Universidad/"
    "MII_2/TFM/TrabajoConDatos/I90DIA/2014_2018/")
carpeta_de_datos_mercado = ("/home/alejandro/Documentos/"
    "Universidad/MII_2/TFM/TrabajoConDatos/info_descargada/"
    "informacion_mercado/")
carpeta_de_informacion = ("/home/alejandro/Documentos/Universidad/"
    "MII_2/TFM/TrabajoConDatos/informacion_procesada/")

# List of files to process (I90DIA).
files_list = (
    sorted(fnmatch.filter(os.listdir(carpeta_de_datos_potencia),'I90DIA*.xls')))


# Obtain first and last date of the raw data
start_date = (
    files_list[0][7:11] + '-' 
    + files_list[0][11:13] + '-' 
    + files_list[0][13:15]
)
end_date = (
    files_list[-1][7:11] + '-' 
    + files_list[-1][11:13] + '-' 
    + files_list[-1][13:15]
)

# Get list of 'unidades de programación' that participated in the
# 'Banda de Resolución Secundaria' bidding in the period of the data.
participantes_secundaria = f.obtener_ofertantes_secundaria(
    carpeta_de_datos_potencia,files_list
)
pd.Series(participantes_secundaria).to_csv(
    carpeta_de_informacion+'participantes_secundaria.csv',
    sep=';', header=['Unidad de programación'],
)

# Import all relevant data concerning the bidders from the I90DIA
# files.
print('Reading raw data:')
df_pvp = f.obtener_pvp(
    participantes_secundaria=participantes_secundaria,
    carpeta=carpeta_de_datos_potencia,
    files_list=files_list,
)
(df_brs_ofertada_subir, 
df_brs_ofertada_bajar, 
df_brs_ofertas_detalladas) = (
    f.obtener_brs_ofertada(
        carpeta=carpeta_de_datos_potencia,
        files_list=files_list,
))
df_brs_casada_subir, df_brs_casada_bajar = f.obtener_brs_casada(
    carpeta=carpeta_de_datos_potencia,
    files_list=files_list,
)
df_p48 = f.obtener_p48(
    participantes_secundaria=participantes_secundaria,
    carpeta=carpeta_de_datos_potencia,
    files_list=files_list,
)
df_pot_max, df_pot_hab = f.obtener_pot_max(
    start_date=start_date,
    end_date=end_date,
    participantes_secundaria=participantes_secundaria,
)
print('Todos los datos han sido importados con éxito')

# Create a dataframe with all the information.
print('Juntando toda la información en un único dataframe.')
dict_dataframes = {
    'PVP':df_pvp,
    'BRS_of_sub':df_brs_ofertada_subir,
    'BRS_of_baj':df_brs_ofertada_bajar,
    'BRS_cas_sub':df_brs_casada_subir,
    'BRS_cas_baj':df_brs_casada_bajar,
    'P48':df_p48,
    'pot_max':df_pot_max,
    'pot_hab':df_pot_hab,
}
df_potencias = f.crear_tabla_ofertantes(dict_dataframes)

# Store the dataframe with all power information in a csv table.
df_potencias.to_csv(
    path_or_buf=(carpeta_de_informacion+'tabla_potencia_agregada.csv'),
    sep=';',
)
print('La información de potencia se ha guardado en un archivo CSV.')

# Import data concerning the electricity market and store them
# in a csv file.
df_mercado = f.obtener_datos_mercado(carpeta_de_datos_mercado)
df_mercado.to_csv(
    path_or_buf=(carpeta_de_informacion+'tabla_datos_mercado.csv'),
    sep=';',
)
print('La información del mercado se ha guardado en un archivo CSV.')


print('El programa ha concluido con éxito.')