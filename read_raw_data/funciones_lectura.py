import pandas as pd
import numpy as np
import sys
import fnmatch
import os
idx = pd.IndexSlice

from funciones_auxiliares import print_progress


def obtener_ofertantes_secundaria(carpeta,files_list):
    """Process raw data to obtain and return the list 
    of all BRS bidders.
    
    Keyword arguments:
    carpeta -- path to the documents with raw data (I90DIA)
    files_list -- list of raw data documents relevant for the study
    """
    ofertantes_totales = set()
    # Progress bar
    l=len(files_list)
    print_progress(
        0, l, prefix='Creating BRS bidders list:', 
        suffix='Complete',
    )

    for i, file in enumerate(files_list):
        name = carpeta + file
        df_temporal = pd.read_excel(
            io=name,
            sheet_name=13,
            skiprows=2,
            header=0,
            usecols=['Unidad de Programación'],
        )
        ofertantes_dia = (
            set(df_temporal['Unidad de Programación'].unique()))
        ofertantes_totales = ofertantes_totales.union(ofertantes_dia)
        print_progress(
            i+1, l, prefix='Creating BRS bidders list:',
            suffix='Complete',
        )

    ofertantes_totales = list(ofertantes_totales)
    ofertantes_totales.sort()
    return ofertantes_totales


def obtener_pvp(participantes_secundaria, carpeta, files_list):
    """Obtain 'Programa Viable Provisional' power planning for the
    period covered in the files for all power units in the list passed.

    Kayword arguments:
    participantes_secundaria -- list of power units to get data from
    carpeta -- path to the documents with raw data (I90DIA)
    files_list -- list of raw data documents relevant for the study
    """
    lista_dataframes_temporales = []
    # Progress bar
    l=len(files_list)
    print_progress(0, l, prefix='Importing PVP power:', 
        suffix='Complete')

    for i, file in enumerate(files_list):
        name = carpeta + file
        df_temporal = pd.read_excel(
            io=name,
            sheet_name=1,
            skiprows=3,
            header=0)
        df_temporal = (
            df_temporal.loc[df_temporal['Unidad de Programación']
                            .isin(participantes_secundaria)])
        df_temporal = (df_temporal.set_index(['Unidad de Programación'])
                       .drop(columns=['Tipo Oferta', 'Hora', 'Total'])
                       .fillna(0).transpose())
        string_fecha = file[7:15]
        string_fecha_completa = (
            string_fecha[:4] + '-' 
            + string_fecha[4:6] + '-' 
            + string_fecha[6:])
        df_temporal.set_index(
            pd.date_range(
                start=string_fecha_completa,
                end=string_fecha_completa+' 23:00',
                freq='H',tz='Europe/Madrid'),
            inplace=True)
        lista_dataframes_temporales.append(df_temporal)
        print_progress(i+1, l, prefix='Importing PVP power:',
            suffix='Complete')


    df_potencia_pvp = pd.concat(
        lista_dataframes_temporales, axis=0, join='outer', sort=False)
    df_potencia_pvp.fillna(0, inplace=True)

    return df_potencia_pvp


def obtener_brs_ofertada(carpeta, files_list):
    """Obtain 'Banda de Regulación Secundaria' biddings for the
    period covered in the files for all power units involved and
    return a tuple of 2 dataframes: (biddings to increase power,
    biddings to decrease power).

    Keyword arguments:
    carpeta -- path to the documents with raw data (I90DIA)
    files_list -- list of raw data documents relevant for the study
    """
    lista_dataframes_temporales_subir = []
    lista_dataframes_temporales_bajar = []
    lista_dataframes_temporales_detalle = []
    df_potencia_brs_subir = pd.DataFrame()
    df_potencia_brs_bajar = pd.DataFrame()
    df_ofertas_detallado = pd.DataFrame()
    # Progress bar
    l=len(files_list)
    print_progress(0, l, prefix='Importing BRS biddings:', 
        suffix='Complete')

    columns_to_drop = [('€/MWh.' + str(num)) for num in range(1,25)]
    columns_to_drop.extend(['€/MWh', 'Bloque', 'Nº Oferta',
                            'Tipo Oferta', 'Indicadores', 'Total MW',
                            'PMP €/MWh', 'Divisibilad'])

    for i, file in enumerate(files_list):
        name = carpeta + file
        df_temporal = pd.read_excel(
            io=name,
            sheet_name=13,
            skiprows=1,
            header=1)
        df_temporal_ofertas = df_temporal.copy()

        df_temporal.drop(
            columns=columns_to_drop, inplace=True, errors='ignore')
        df_temporal.fillna(0, inplace=True)
        df_temporal = (
            df_temporal.groupby(by=['Sentido', 'Unidad de Programación'])
            .sum().copy())
        df_temporal_subir = df_temporal.loc['Subir']
        df_temporal_bajar = df_temporal.loc['Bajar']
        df_temporal_subir = df_temporal_subir.transpose().copy()
        df_temporal_bajar = df_temporal_bajar.transpose().copy()
        
        string_fecha = file[7:15]
        string_fecha_completa = (
            string_fecha[:4] + '-' 
            + string_fecha[4:6] + '-' 
            + string_fecha[6:])
        
        df_temporal_ofertas.drop(
            columns=['Tipo Oferta', 'Indicadores', 'Total MW', 'PMP €/MWh', 'Divisibilad'], 
            inplace=True, errors='ignore')
        df_temporal_ofertas.set_index(
            keys=['Unidad de Programación', 'Sentido', 'Nº Oferta', 'Bloque'],
            drop=True, inplace=True
        )
        df_temporal_ofertas.columns=pd.MultiIndex.from_product(
            iterables=[
                pd.date_range(
                    start=string_fecha_completa,
                    end=string_fecha_completa+' 23:00',
                    freq='H',tz='Europe/Madrid'
                ),
                ['MW','€/MWh']],
            names=['Hora', 'Dato'])
        df_temporal_ofertas = df_temporal_ofertas.stack('Hora')
        lista_dataframes_temporales_detalle.append(df_temporal_ofertas)
        
        df_temporal_subir.set_index(
            pd.date_range(
                start=string_fecha_completa,
                end=string_fecha_completa+' 23:00',
                freq='H',tz='Europe/Madrid'),
            inplace=True)
        df_temporal_bajar.set_index(
            pd.date_range(
                start=string_fecha_completa,
                end=string_fecha_completa+' 23:00',
                freq='H',tz='Europe/Madrid'),
            inplace=True)
        lista_dataframes_temporales_subir.append(df_temporal_subir)
        lista_dataframes_temporales_bajar.append(df_temporal_bajar)
        print_progress(i+1, l, prefix='Importing BRS biddings:', 
        suffix='Complete')

    df_potencia_brs_subir = pd.concat(
        lista_dataframes_temporales_subir, axis=0,
        join='outer', sort=False)
    df_potencia_brs_bajar = pd.concat(
        lista_dataframes_temporales_bajar, axis=0,
        join='outer', sort=False)
    df_ofertas_detallado = pd.concat(
        lista_dataframes_temporales_detalle, axis=0,
        join='outer', sort=False)
    
    df_potencia_brs_subir.fillna(0, inplace=True)
    df_potencia_brs_bajar.fillna(0, inplace=True)

    return (df_potencia_brs_subir,
            df_potencia_brs_bajar,
            df_ofertas_detallado)


def obtener_brs_casada(carpeta, files_list):
    lista_casada_subir = []
    lista_casada_bajar = []
    columns_to_drop = [
        'Nm Oferta asignada', 'Tipo Oferta', 'Hora', 'Total']
    # Progress bar
    l=len(files_list)
    print_progress(0, l, prefix='Importing BRS selected biddings:', 
        suffix='Complete')
    
    for i, file in enumerate(files_list):
        name = carpeta + file
        df_temporal = pd.read_excel(
            io=name,
            sheet_name=5,
            skiprows=2,
            header=0)
        df_temporal.drop(columns=columns_to_drop, inplace=True, errors='ignore')
        df_temporal = df_temporal.groupby(by=['Sentido', 'Unidad de Programación']).sum().copy()
        df_temporal_subir = df_temporal.loc['Subir']
        df_temporal_bajar = df_temporal.loc['Bajar']
        df_temporal_subir = df_temporal_subir.transpose().copy()
        df_temporal_bajar = df_temporal_bajar.transpose().copy()

        string_fecha = file[7:15]
        string_fecha_completa = (
            string_fecha[:4] + '-'
            + string_fecha[4:6] + '-'
            + string_fecha[6:])
        df_temporal_subir.set_index(
            pd.date_range(
                start=string_fecha_completa,
                end=string_fecha_completa+' 23:00',
                freq='H',tz='Europe/Madrid'),
            inplace=True)
        df_temporal_bajar.set_index(
            pd.date_range(
                start=string_fecha_completa,
                end=string_fecha_completa+' 23:00',
                freq='H',tz='Europe/Madrid'),
            inplace=True)
        
        lista_casada_subir.append(df_temporal_subir)
        lista_casada_bajar.append(df_temporal_bajar)
        print_progress(i+1, l, prefix='Importing BRS selected biddings:', 
            suffix='Complete')

    df_potencia_brs_casada_subir = pd.concat(
        lista_casada_subir, axis=0, join='outer', sort=False)
    df_potencia_brs_casada_bajar = pd.concat(
        lista_casada_bajar, axis=0, join='outer', sort=False)
    df_potencia_brs_casada_subir.fillna(0, inplace=True)
    df_potencia_brs_casada_bajar.fillna(0, inplace=True)

    return (df_potencia_brs_casada_subir, df_potencia_brs_casada_bajar)


def obtener_p48(participantes_secundaria, carpeta, files_list):
    lista_p48 = []
    # Progress bar
    l=len(files_list)
    print_progress(0, l, prefix='Importing P48 power:', 
        suffix='Complete')

    for i, file in enumerate(files_list):
        name = carpeta + file
        df_temporal = pd.read_excel(
            io=name,
            sheet_name=2,
            skiprows=3,
            header=0)
        df_temporal = (df_temporal.loc[
            df_temporal['Unidad de Programación']
            .isin(participantes_secundaria)])
        df_temporal = (
            df_temporal.set_index(['Unidad de Programación'])
            .drop(columns=['Tipo Oferta', 'Hora', 'Total'])
            .fillna(0).copy().transpose())
        string_fecha = file[7:15]
        string_fecha_completa = (
            string_fecha[:4] + '-'
            + string_fecha[4:6] + '-'
            + string_fecha[6:])
        df_temporal.set_index(
            pd.date_range(
                start=string_fecha_completa,
                end=string_fecha_completa+' 23:00',
                freq='H',tz='Europe/Madrid'), 
            inplace=True)
        lista_p48.append(df_temporal)
        print_progress(i+1, l, prefix='Importing P48 power:', 
            suffix='Complete')

    df_p48 = pd.concat(lista_p48, axis=0, join='outer', sort=False)
    df_p48.fillna(0, inplace=True)

    return df_p48


def obtener_pot_max(start_date, end_date, participantes_secundaria):
    uf_file = ('/home/alejandro/Documentos/Universidad/MII_2/TFM/'
        'TrabajoConDatos/info_descargada/informacion_centrales/'
        'unidades_fisicas.csv')
    df_uf = pd.read_csv(
        uf_file,
        header=0,
        sep=';',
    )
    df_uf = (df_uf.loc[
        df_uf['Vinculación con UP']
        .isin(participantes_secundaria)
        ]
    )
    df_uf['Potencia máxima MW'] = (
        df_uf['Potencia máxima MW'].apply(
            lambda x: float(str(x).replace(',','.'))
        )
    )
    df_pot_max = pd.DataFrame(
        index=pd.date_range(
            start=start_date,
            end=end_date+' 23:00',
            freq='H',tz='Europe/Madrid',
        ),
        columns=participantes_secundaria,
    )
    df_pot_hab = df_pot_max.copy()
    for up in participantes_secundaria:
        try:
            df_pot_max.loc[:,up] = (
                df_uf.groupby(['Vinculación con UP']).sum()
                .loc[up,'Potencia máxima MW']
            )
        except KeyError:
            df_pot_max.loc[:,up] = np.nan
            pass
            print(
                ("No existen datos para la unidad de producción {}"
                .format(up))
            )
    df_uf = (df_uf.loc[
        ~df_uf['Tipo de producción'].isin(['Hidráulica no UGH'])
        ]
    )
    for up in participantes_secundaria:
        try:
            df_pot_hab.loc[:,up] = (
                df_uf.groupby(['Vinculación con UP']).sum()
                .loc[up,'Potencia máxima MW']
            )
        except KeyError:
            if np.isnan(df_pot_max.loc[df_pot_max.index[0],up]):
                df_pot_hab.loc[:,up] = np.nan
            else:
                df_pot_hab.loc[:,up] = 0
                print(
                ("La unidad de producción {} solamente "
                 "tiene unidades físicas 'Hidráulica no UGH', "
                 "por lo que su potencia habilitada " 
                 "es 0.".format(up))
            )
            pass
    
    return df_pot_max, df_pot_hab


def crear_tabla_ofertantes(dataframes):
    """Merge all dataframes passe in a multiindex column dataframe
    and return it.

    Dataframes:
    first element of the pair -- dataframe
    second element of the pair -- name of the data
    """
    lista_dataframes = []
    for name, df in dataframes.items():
        df_aux = pd.DataFrame(df.stack())
        df_aux.loc[:,'tipo_de_dato'] = name
        df_aux.set_index('tipo_de_dato',append=True,inplace=True)
        lista_dataframes.append(df_aux)
    df_final = pd.concat(lista_dataframes)
    df_final = (
        df_final.swaplevel().unstack(2).droplevel(0,axis=1).unstack()
    )
    df_final.columns.rename(
        ['Unidad de Programación', 'Tipo de dato'],
        inplace=True,
    )
    return df_final


def obtener_datos_mercado(carpeta_de_datos_mercado):
    """Import data from the electricity market. Scan all csv files
    in the folder passed. All must have the same structure provided
    by REE. Returns a dataframe with a datetime index and the
    data in the columns.

    Keyword arguments:
    carpeta_de_datos_mercado -- Path to the folder with the
        desired files
    """
    files_list_mercado = (
        sorted(fnmatch.filter(
            os.listdir(carpeta_de_datos_mercado),
            '*.csv')
        )
    )
    lista_info_mercado = []
    start_date = []
    end_date = []

    for file in files_list_mercado:
        df_temporal = pd.read_csv(
            carpeta_de_datos_mercado+file, 
            sep=';'
        )
        start_date.append(pd.to_datetime(df_temporal.loc[df_temporal.index[0],'datetime'],))
        end_date.append(pd.to_datetime(df_temporal.loc[df_temporal.index[-1],'datetime'],))
        name = df_temporal.loc[0,'name']
        df_temporal = df_temporal.loc[:,['datetime', 'value']]
        df_temporal.set_index(['datetime'], inplace=True)
        df_temporal.rename(
            columns={'value': name},
            inplace=True
        )
        lista_info_mercado.append(df_temporal)
    
    df_mercado_secundaria = pd.concat(lista_info_mercado,axis=1,sort=True)
    df_mercado_secundaria.fillna(0, inplace=True,)
    df_mercado_secundaria.index=pd.date_range(
        start=sorted(start_date)[0].strftime('%Y-%m-%d %H:%M:%S'),
        end=sorted(end_date)[-1].strftime('%Y-%m-%d %H:%M:%S'),
        freq='H',tz='Europe/Madrid',
    )

    return df_mercado_secundaria



