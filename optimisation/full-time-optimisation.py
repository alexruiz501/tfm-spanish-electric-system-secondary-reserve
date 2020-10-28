"""
Este programa realiza una optimización de todos los días de los años
2014-2018 para 3 centrales que participan en el mercado diario y en
el servicio de regulación secundaria en dos casos diferentes:
En uno de ellos concurren al servicio de regulación secundaria
como Zonas de Regulación independientes y en otro como miembros
de la misma Zona de Regulación.

En este modelo se considera que las centrales son tomadoras de
precio que no tienen impacto en el precio del servicio y que
conocen a la perfección los precios del mercado y la utilización
de regulación secundaria del día siguiente.
"""


import gams
import sys
import os
import pandas as pd


# Crea el WorkSpace de Gams en el que vamos a trabajar
ws = gams.GamsWorkspace(debug=gams.DebugLevel.KeepFiles)

# Datos comunes a todos los días
centrales = ["1","2","3"]
potencia_maxima = {
    "1": 10, "2": 10, "3": 10,
}
coste_fijo = {
    "1": 10, "2": 25, "3": 30,
}
coste_variable = {
    "1": 40, "2": 15, "3": 5,
}

# Importa los datos genéricos del mercado eléctrico
df_total = pd.read_csv(
    "/home/alejandro/Documentos/Universidad/MII_2/TFM/"
    + "TrabajoConDatos/informacion_procesada/tabla_datos_mercado.csv",
    sep=";", index_col=0,
)

# Crea el índice como fechas
df_total.index=pd.date_range(
    start='2014-01-01',end='2018-12-31 23:00',freq='H',tz='Europe/Madrid'
)

# Elimina los NaNs sin poner ceros en los requerimientos de BRS
# para evitar dividir por 0 en el modelo
(df_total["Requerimientos Banda de regulación secundaria a subir"]
    .fillna(method="pad",inplace=True,))
(df_total["Requerimientos Banda de regulación secundaria a bajar"]
    .fillna(method="pad",inplace=True,))
df_total.fillna(0,inplace=True)

# Indica la ruta del modelo y de la base de datos
modelo_sep = ws.add_job_from_file(
    "/home/alejandro/Documentos/Universidad/MII_2/TFM/"
    + "Optimizacion/modelo_varias_centrales_sin_datos_separadas.gms"
    )
modelo_jun = ws.add_job_from_file(
    "/home/alejandro/Documentos/Universidad/MII_2/TFM/"
    + "Optimizacion/modelo_varias_centrales_sin_datos_juntas.gms"
    )
opt = ws.add_options()
opt.defines["gdxincname"] = (
    "/home/alejandro/Documentos/Universidad/MII_2/TFM/"
    + "Optimizacion/datos_partida.gdx"
)

inicio = True
mode = 'w'

# Bucle con la simulación de cada día para evitar sobrepasar
# el límite de la licencia
for fecha in pd.date_range(start="2014",end="2018-12-31 23:00",freq="d"):

    # Crea un dataframe en el que guardar los datos de salida
    df_opt_sep = pd.DataFrame(
        columns=["p1","p2","p3","brs_sub1","brs_sub2","brs_sub3",
        "brs_baj1","brs_baj2","brs_baj3","ben"])
    df_opt_jun = pd.DataFrame(
        columns=["p1","p2","p3","brs_sub1","brs_sub2","brs_sub3",
        "brs_baj1","brs_baj2","brs_baj3","ben"])
    
    df_dia = df_total.loc[fecha.strftime("%Y-%m-%d")]

    # Crea un objeto GamsDatabase
    db = ws.add_database()

    # Añade set i de centrales
    i = db.add_set("i", 1, "centrales")
    for central in centrales:
        i.add_record(central)

    # Añade parámetros de cada central
    pm = db.add_parameter_dc("pm",[i],"potencia máxima de la central i")
    for central in centrales:
        pm.add_record(central).value = potencia_maxima[central]

    cf = db.add_parameter_dc("cf",[i],"coste fijo horario por MW de la central i")
    for central in centrales:
        cf.add_record(central).value = coste_fijo[central]

    cv = db.add_parameter_dc(
        "cv",[i],
        "coste variable horario por MW de la central i")
    for central in centrales:
        cv.add_record(central).value = coste_variable[central]

    # Añade escalar genérico grande
    m = db.add_parameter("m", 0, "número muy grande")
    m.add_record().value = 1000000

    # Añadimos parámetros particulares del día que dependen
    # de la hora
    t = db.add_set("t",1,"hora del día")
    for hora in df_dia.index:
        t.add_record(str(hora))

    pr_prog = db.add_parameter_dc(
        "pr_prog",[t],"precio del mercado diario")
    for hora in df_dia.index:
        pr_prog.add_record(str(hora)).value = (
            df_dia.loc[hora,"Precio mercado SPOT Diario"])

    pr_brs = db.add_parameter_dc("pr_brs",[t],"precio de la BRS")
    for hora in df_dia.index:
        pr_brs.add_record(str(hora)).value = (
            df_dia.loc[hora,"Precio Banda de regulación secundaria"])

    pr_ut_res_sub = db.add_parameter_dc(
        "pr_ut_res_sub",[t],"precio de la utilizacion de BRS a subir")
    for hora in df_dia.index:
        pr_ut_res_sub.add_record(str(hora)).value = (
            df_dia.loc[hora,"Precio de Regulación Secundaria subir"])
        
    pr_ut_res_baj = db.add_parameter_dc(
        "pr_ut_res_baj",[t],"precio de la utilizacion de BRS a bajar")
    for hora in df_dia.index:
        pr_ut_res_baj.add_record(str(hora)).value = (
            df_dia.loc[hora,"Precio de Regulación Secundaria bajar"])
        
    requerimiento_brs_subir = db.add_parameter_dc(
        "requerimiento_brs_subir",[t],"requerimiento de brs a subir")
    for hora in df_dia.index:
        requerimiento_brs_subir.add_record(str(hora)).value = (
            df_dia.loc[
                hora,
                "Requerimientos Banda de regulación secundaria a subir"])
        
    requerimiento_brs_bajar = db.add_parameter_dc(
        "requerimiento_brs_bajar",[t],"requerimiento de brs a bajar")
    for hora in df_dia.index:
        requerimiento_brs_bajar.add_record(str(hora)).value = (
            df_dia.loc[
                hora,
                "Requerimientos Banda de regulación secundaria a bajar"])

    utilizacion_reserva_bajar = db.add_parameter_dc(
        "utilizacion_reserva_bajar",[t],
        "cantidad de energía de reserva secundaria utilizada a bajar")
    for hora in df_dia.index:
        utilizacion_reserva_bajar.add_record(str(hora)).value = (
            df_dia.loc[
                hora,
                "Energía utilizada de Regulación Secundaria bajar"])

    utilizacion_reserva_subir = db.add_parameter_dc(
        "utilizacion_reserva_subir",[t],
        "cantidad de energía de reserva secundaria utilizada a subir")
    for hora in df_dia.index:
        utilizacion_reserva_subir.add_record(str(hora)).value = (
            df_dia.loc[
                hora,
                "Energía utilizada de Regulación Secundaria subir"])

    # Exporta la base de datos
    db.export(
        "/home/alejandro/Documentos/Universidad/MII_2/TFM/"
        + "Optimizacion/datos_partida.gdx")

    # Ejecuta el modelo con los datos de la base de datos
    modelo_sep.run(opt)
    modelo_jun.run(opt)

    # Guarda los datos obtenidos de la simulación
    for rec in modelo_sep.out_db['pot_prog']:
        df_opt_sep.loc[rec.keys[1],"p"+rec.keys[0]] = rec.level
    for rec in modelo_sep.out_db['brs_sub']:
        df_opt_sep.loc[rec.keys[1],"brs_sub"+rec.keys[0]] = rec.level
    for rec in modelo_sep.out_db['brs_baj']:
        df_opt_sep.loc[rec.keys[1],"brs_baj"+rec.keys[0]] = rec.level
    for rec in modelo_sep.out_db["ben"]:
        df_opt_sep.loc[rec.keys[0],"ben"] = rec.level
    
    for rec in modelo_jun.out_db['pot_prog']:
        df_opt_jun.loc[rec.keys[1],"p"+rec.keys[0]] = rec.level
    for rec in modelo_jun.out_db['brs_sub']:
        df_opt_jun.loc[rec.keys[1],"brs_sub"+rec.keys[0]] = rec.level
    for rec in modelo_jun.out_db['brs_baj']:
        df_opt_jun.loc[rec.keys[1],"brs_baj"+rec.keys[0]] = rec.level
    for rec in modelo_jun.out_db["ben"]:
        df_opt_jun.loc[rec.keys[0],"ben"] = rec.level


    # Exporta los datos al archivo
    df_opt_sep.sort_index()
    df_opt_sep.to_csv("/home/alejandro/Documentos/Universidad/MII_2/TFM/"
        + "Optimizacion/optimizacion_separadas.csv", mode=mode,header=inicio)
    df_opt_jun.sort_index()
    df_opt_jun.to_csv("/home/alejandro/Documentos/Universidad/MII_2/TFM/"
        + "Optimizacion/optimizacion_juntas.csv",mode=mode,header=inicio)
    
    inicio = False
    mode = 'a'


    # Elimina todos los registros de la base de datos para
    # utilizarla de nuevo
    db.clear()
    print(fecha)


print("El programa ha terminado.")






