import pandas as pd

from funciones_auxiliares import print_progress


def leer_participantes_secundaria(carpeta_de_informacion):
    """Read the previously saved table with the BRS bidders
    in the study period.
    
    Keyword arguments:
    carpeta_de_informacion -- Path to the folder with the csv.
    """
    df_participantes_secundaria = pd.read_csv(
        carpeta_de_informacion+'participantes_secundaria.csv',
        sep=';',
        header=0,
        index_col=0,
    )
    participantes_secundaria = list(
        df_participantes_secundaria['Unidad de programación']
    )
    return participantes_secundaria


def leer_tabla_potencia(carpeta_de_informacion):
    print('Reading hourly power dataframe...')
    df_potencias = pd.read_csv(
        carpeta_de_informacion+'tabla_potencia_agregada.csv',
        sep=';',
        index_col=0,
        low_memory=False,
        header=[0,1],
        parse_dates=True
    )

    df_potencias.index = pd.date_range(
        start=df_potencias.index[0].strftime('%Y-%m-%d %H:%M'),
        end=df_potencias.index[-1].strftime('%Y-%m-%d %H:%M'),
        freq='H',tz='Europe/Madrid',
    )
    return df_potencias


def leer_tabla_mercado(carpeta_de_informacion):
    print('Reading hourly market data dataframe...')
    df_mercado = pd.read_csv(
        carpeta_de_informacion+'tabla_datos_mercado.csv',
        sep=';',
        index_col=0,
        low_memory=False,
        header=[0],
        parse_dates=True
    )
    df_mercado.index = pd.date_range(
        start=df_mercado.index[0].strftime('%Y-%m-%d %H:%M'),
        end=df_mercado.index[-1].strftime('%Y-%m-%d %H:%M'),
        freq='H',tz='Europe/Madrid',
    )
    return df_mercado


def obtener_empresa_centrales(participantes_secundaria,
                               carpeta_de_datos_centrales):
    """Read table with company affiliation of Unidades de Programación
    and create and return a dictionary with the companies as keys and 
    Unidades de Programación as lists assigned to these keys. Also
    return a dictionary with Unidad de Programación as key that has
    the company they belong to as value.

    Keyword arguments:
    participantes_secundaria -- List of Unidades de Programación
        participating in BRS.
    carpeta_de_datos_centrales -- path to the folder where the esios
        downloaded Unidades de Programación csv is found.
    """
    print('Reading company affiliation information...')
    df_ud_prog = pd.read_csv(
        carpeta_de_datos_centrales+'unidades_programacion.csv',
        sep=';',
        header=0,
        index_col=0,
    )
    df_ud_prog = df_ud_prog.loc[
        df_ud_prog.index.isin(participantes_secundaria),
        ['Zona de Regulación']
    ]
    empresas = df_ud_prog['Zona de Regulación'].unique()
    # Diccionario con clave Zona de Regulación y valor lista de
    # Unidades de Programación.
    centrales_en_empresa = dict()
    for empresa in empresas:
        centrales_en_empresa.setdefault(empresa,[])
        centrales_en_empresa[empresa] = list(
            df_ud_prog.loc[
                df_ud_prog['Zona de Regulación']==empresa
            ].index
        )
    # Diccionario con clave Unidad de Programación y valor su Zona de
    # Regulación.
    empresa_de_central = dict(zip(
        df_ud_prog.index,
        df_ud_prog['Zona de Regulación']
    ))

    return centrales_en_empresa, empresa_de_central


def obtener_margenes_potencia(df_potencias, carpeta_de_informacion):
    """Create the power margins for every Unidad de Programación
    , type of power planning, offered or accepted biddings and
    up or down type. Return a dataframe with the power margins
    for all combinations of values.

    Keyword arguments:
    df_potencias -- dataframe where all power information regarding
    all Unidades de Programacion is stored.
    """
    print('Obtaining power margins dataframe...')
    try:
        df_margenes_potencia = pd.read_csv(
            carpeta_de_informacion+'tabla_margenes_potencia_up.csv',
            sep=';',
            header=[0,1,2,3],
            index_col=0,
            parse_dates=True,
            low_memory=False,
        )
        df_margenes_potencia.index = pd.date_range(
            start=df_margenes_potencia.index[0].strftime('%Y-%m-%d %H:%M'),
            end=df_margenes_potencia.index[-1].strftime('%Y-%m-%d %H:%M'),
            freq='H',tz='Europe/Madrid',
        )
        print(
            'The power margins dataframe has been imported from memory. '
            'If you wish to compute it again please first erase the '
            'file "tabla_margenes_potencia_up.csv" from your '
            'information folder.'
        )
    except:
        centrales = df_potencias.columns.get_level_values(0).unique()
        planificaciones = ['P48','PVP']
        bandas = ['Casada','Ofertada']
        margenes = ['Superior','Inferior']

        df_margenes_potencia = pd.DataFrame(
            columns=pd.MultiIndex.from_product(
                [centrales,planificaciones,bandas,margenes]
            ),
            index=df_potencias.index,
        )
        dic_col = {
            'Casada':{
                'Superior':'BRS_cas_sub',
                'Inferior':'BRS_cas_baj',
            },
            'Ofertada':{
                'Superior':'BRS_of_sub',
                'Inferior':'BRS_of_baj',
            },
        }

        # Progress bar
        l=len(centrales)
        print_progress(
            0, l, prefix='Creating power margins table:', 
            suffix='Complete',
        )

        for i,central in enumerate(centrales):
            for planificacion in planificaciones:
                for banda in bandas:
                    # Calcular el margen de potencia superior.
                    df_aux = pd.DataFrame(
                        index=df_potencias.index,
                        columns=['pot_hab-BRS_sub','pot_max-planificacion-BRS_sub'],
                    )
                    df_aux.loc[:,'pot_hab-BRS_sub'] = (
                        df_potencias.loc[:,(central,'pot_hab')] 
                        - df_potencias.loc[:,(central,dic_col[banda]['Superior'])]
                    )
                    df_aux.loc[:,'pot_max-planificacion-BRS_sub'] = (
                        df_potencias.loc[:,(central,'pot_max')]
                        - df_potencias.loc[:,(central,planificacion)]
                        - df_potencias.loc[:,(central,dic_col[banda]['Superior'])]
                    )
                    df_aux = df_aux.min(axis=1)

                    df_margenes_potencia.loc[:,(central,planificacion,banda,'Superior')] = (
                        (df_potencias.loc[:,(central,planificacion)]==0)
                        * (-df_potencias.loc[:,(central,dic_col[banda]['Superior'])])
                        + (df_potencias.loc[:,(central,planificacion)]!=0)
                        * df_aux
                    )

                    # Calcular el margen de potencia inferior.
                    df_margenes_potencia.loc[:,(central,planificacion,banda,'Inferior')] = (
                        df_potencias.loc[:,(central,planificacion)]
                        - df_potencias.loc[:,(central,dic_col[banda]['Inferior'])]
                    )
            print_progress(i+1, l, prefix='Creating power margins table:', 
                        suffix='Complete')
        df_margenes_potencia.to_csv(
            carpeta_de_informacion+'tabla_margenes_potencia_up.csv',
            sep=';',
        )
        print(
            'The power margins dataframe has been stored in the '
            'information folder. Next time it will be imported.'
        )
    return df_margenes_potencia


def obtener_margenes_potencia_empresas(
            df_margenes_potencia,
            centrales_en_empresa,
            carpeta_de_informacion,
        ):
    """Cumulate power margins per Unidad de Programacion to obtain the
    result for every Zona de Regulacion (company).

    Keyword arguments:
    df_margenes_potencia -- power margins of every Unidad de
        Programación as computed in the previous function.
    centrales_en_empresa -- Dictionary with companies as keys and a
        list of their Unidades de Programacion as values.
    """
    try:
        df_margenes_potencia_empresas = pd.read_csv(
            carpeta_de_informacion+'tabla_margenes_potencia_empresas.csv',
            sep=';',
            header=[0,1,2,3],
            index_col=0,
            parse_dates=True,
            low_memory=False,
        )
        df_margenes_potencia_empresas.index = pd.date_range(
            start=(df_margenes_potencia_empresas.index[0]
                   .strftime('%Y-%m-%d %H:%M')),
            end=(df_margenes_potencia_empresas.index[-1]
                 .strftime('%Y-%m-%d %H:%M')),
            freq='H',tz='Europe/Madrid',
        )
        print(
            'The companies power margins dataframe has been imported '
            'from memory. '
            'If you wish to compute it again please first erase the '
            'file "tabla_margenes_potencia_empresas.csv" from your '
            'information folder.'
        )
    except:
        empresas = list(centrales_en_empresa.keys())
        planificaciones = ['P48','PVP']
        bandas = ['Casada','Ofertada']
        margenes = ['Superior','Inferior']
        df_margenes_potencia_empresas = pd.DataFrame(
            columns=pd.MultiIndex.from_product(
                [empresas,planificaciones,bandas,margenes]
            ),
            index=df_margenes_potencia.index,
        )

        # Progress bar
        l=len(empresas)
        print_progress(
            0, l, prefix='Creating company power margins table:', 
            suffix='Complete',
        )

        for i,empresa in enumerate(empresas):
            for planificacion in planificaciones:
                for banda in bandas:
                    for margen in margenes:
                        df_margenes_potencia_empresas.loc[
                            :,(empresa,planificacion,banda,margen)
                        ] = (
                            df_margenes_potencia.loc[
                                :,
                                (centrales_en_empresa[empresa],
                                planificacion,banda,margen)
                            ].sum(axis=1)
                        )
            print_progress(
                i+1, l, prefix='Creating company power margins table:',
                suffix='Complete',
            )
        df_margenes_potencia_empresas.to_csv(
            carpeta_de_informacion+'tabla_margenes_potencia_empresas.csv',
            sep=';',
        )
        print(
            'The companies power margins dataframe has been stored in '
            'the information folder. Next time it will be imported.'
        )
    
    return df_margenes_potencia_empresas


def obtener_mw_imposibles(df_marg_pot):
    """Return the absolute value for negative values and 0 for
    positive values of the passed DataFrame.
    """
    return df_marg_pot.mask(df_marg_pot>0,0).abs()


def obtener_horas_imposibles(df_marg_pot):
    """Return True if the margin is negative and False if the margin is
    positive.
    """
    return df_marg_pot<0


def obtener_beneficio_extra(df_mw_imp,df_mercado):
    """Multiply the impossible MWs by the BRS price at that hour
    to compute the extra profit obtained.

    Keyword arguments:
    df_marg_pot -- Dataframe with the extra MW for each hour.
    df_mercado -- Dataframe with market data.   
    """
    df_beneficio = df_mw_imp.copy()
    for column in df_beneficio.columns:
        df_beneficio.loc[:,column] = (
            df_beneficio.loc[:,column] 
            * df_mercado['Precio mercado SPOT Diario']
        )
    return df_beneficio


def obtener_correlaciones(df_mercado,dic_df):
    lista_correlaciones = []
    lista_nombres_df = list(dic_df.keys())

    # Progress bar
    l_d = len(dic_df)
    l_m = len(df_mercado.columns)
    l_tot = l_d * l_m
    print_progress(
        0, l_tot, prefix='Creating correlations table:', 
        suffix='Complete',
    )
    for i,(_,df) in enumerate(dic_df.items()):
        for j,column in enumerate(df_mercado.columns):
            lista_correlaciones.append(df.corrwith(df_mercado[column]))
            print_progress(
                i*l_m+j+1, l_tot, prefix='Creating correlations table:',
                suffix='Complete',
            )

    df_corr = pd.concat(lista_correlaciones,axis=1)
    df_corr.columns = pd.MultiIndex.from_product(
        [lista_nombres_df,
        df_mercado.columns]
    )
    df_corr.columns.names = ['Elemento 1', 'Elemento 2']
    df_corr.index.names = ['Empresa', 'Planificación','BRS', 'Extremo']

    return df_corr

