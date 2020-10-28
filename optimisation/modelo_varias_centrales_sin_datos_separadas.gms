$title Optimizacion conjunta de la venta de energía y reserva secundaria de varias centrales

$onText
Modelo simplificado para observar la provisión de servicio de regulación
secundaria de varias centrales, concurriendo de manera conjunta o
independiente.

Se van a proponer 3 centrales caracterizadas de manera simple por
su coste fijo y su coste variable por MW y por su potencia máxima.
Se supone además posibilidad técnica de operar a cualquier factor de
carga con coste marginal constante.

Los parámetros del sistema mercado utilizados en el modelo corresponden
al día 1/1/2014.
$offText

* OPTIONS LIMROW=1500, LIMCOL=1500;

sets
t       "hora del dia"
i       "central";

parameters
pr_prog(t) "precio del mercado diario" 
pr_brs(t) "precio de la BRS"
pr_ut_res_sub(t) "precio de la utilizacion de BRS a subir"
pr_ut_res_baj(t) "precio de la utilizacion de BRS a bajar"
requerimiento_brs_subir(t) "requerimiento de brs a subir"
requerimiento_brs_bajar(t) "requerimiento de brs a bajar"
utilizacion_reserva_bajar(t) "cantidad de energía de reserva secundaria utilizada a bajar"
utilizacion_reserva_subir(t) "cantidad de energía de reserva secundaria utilizada a subir"
cf(i)
cv(i)
pm(i);

scalars
m       "Número grande";


$if not set gdxincname $abort 'no include file name for data file provided'
$gdxin %gdxincname%
$load t i pr_prog pr_brs pr_ut_res_sub pr_ut_res_baj requerimiento_brs_subir requerimiento_brs_bajar utilizacion_reserva_bajar utilizacion_reserva_subir cf cv pm m
$gdxin

parameters
fact_ut_sub(t)      "Factor de utilización de brs a subir"
fact_ut_baj(t)      "Factor de utilización de brs a bajar";

fact_ut_sub(t) = utilizacion_reserva_subir(t) / requerimiento_brs_subir(t);
fact_ut_baj(t) = utilizacion_reserva_bajar(t) / requerimiento_brs_bajar(t);
fact_ut_sub(t) $ (fact_ut_sub(t) >= 1) = 1;
fact_ut_baj(t) $ (fact_ut_baj(t) >= 1) = 1;

variables
ing_hor(i,t)            "Ingresos horarios"
ing_hor_ut_brs(i,t)     "Ingresos horarios debidos al uso de BRS"
z                       "Función objetivo"
ben(t)                  "Beneficio en la hora t"
;

positive variables
pot_prog(i,t)       "Potencia programada en el mercado diario"
brs_sub(i,t)        "BRS a subir"    
brs_baj(i,t)        "BRS a bajar"
brs_ut_baj(i,t)     "Uso de BRS a subir"
brs_ut_sub(i,t)     "Uso de BRS a bajar"
coste_hor(i,t)      "Coste total horario de la producción"
brs_net_sub(i,t)    "utilizada neta a subir"
brs_net_baj(i,t)    "utilizada neta a bajar"
;

binary variables
ut_neta_sub(i,t)    "Utilización neta es a subir (1) o a bajar (0)"
;

equations
e_pot_max(i,t)
e_pot_min(i,t)
e_ratio_sub_baj_central(i,t)
e_ratio_sub_baj_zona(t)
e_ut_brs_sub(i,t)
e_ut_brs_baj(i,t)
e_ut_brs_net(i,t)
e_ing_hor_ut_brs(i,t)
e_ing(i,t)
e_cost(i,t)
e_ben(t)
e_fun_obj
e_ut_brs_net_s(i,t)
e_ut_brs_net_b(i,t)
;


* Factibilidad de la prestación de BRS y potencia programada
e_pot_max(i,t)..        pot_prog(i,t) + brs_sub(i,t) =l= pm(i);
e_pot_min(i,t)..        pot_prog(i,t) - brs_baj(i,t) =g= 0;

* Cumplimiento del ratio por centrales
e_ratio_sub_baj_central(i,t)..  brs_sub(i,t) =e= brs_baj(i,t) * requerimiento_brs_subir(t) / requerimiento_brs_bajar(t);

* Cumplimiento del ratio por zona
e_ratio_sub_baj_zona(t).. sum(i,brs_sub(i,t)) =e= requerimiento_brs_subir(t) / requerimiento_brs_bajar(t) * sum(i,brs_baj(i,t));

* Utilización de BRS
e_ut_brs_sub(i,t)..     brs_ut_sub(i,t) =e= brs_sub(i,t) * fact_ut_sub(t);
e_ut_brs_baj(i,t)..     brs_ut_baj(i,t) =e= brs_baj(i,t) * fact_ut_baj(t);


* Ingresos por utilización de BRS
e_ut_brs_net(i,t)..     brs_net_sub(i,t) - brs_net_baj(i,t) =e= brs_ut_sub(i,t) - brs_ut_baj(i,t);
e_ut_brs_net_s(i,t)..   brs_net_sub(i,t) =l= m * ut_neta_sub(i,t);
e_ut_brs_net_b(i,t)..   brs_net_baj(i,t) =l= m * (1 - ut_neta_sub(i,t));
e_ing_hor_ut_brs(i,t).. ing_hor_ut_brs(i,t) =e= brs_net_sub(i,t) * pr_ut_res_sub(t) - pr_ut_res_baj(t) * brs_net_baj(i,t);


* Beneficios totales
e_ing(i,t)..    ing_hor(i,t) =e= pot_prog(i,t) * pr_prog(t) + (brs_baj(i,t) + brs_sub(i,t)) * pr_brs(t) + ing_hor_ut_brs(i,t);
e_cost(i,t)..   coste_hor(i,t) =e= cf(i) * pm(i) + cv(i) * (pot_prog(i,t) + brs_net_sub(i,t) - brs_net_baj(i,t));
e_ben(t)..      ben(t) =e= sum(i, ing_hor(i,t) - coste_hor(i,t));


* Función objetivo
e_fun_obj..     z =e= sum(t,ben(t));


* Modelos
models  ecuaciones_generales  / e_pot_max, e_pot_min, e_ut_brs_sub, e_ut_brs_baj,
                                e_ut_brs_net, e_ing_hor_ut_brs, e_ing, e_cost, e_fun_obj,
                                e_ut_brs_net_s, e_ut_brs_net_b, e_ben /
        centrales_separadas    / ecuaciones_generales, e_ratio_sub_baj_central /
        centrales_agrupadas     / ecuaciones_generales, e_ratio_sub_baj_zona /
;


* Solve
Solve   centrales_separadas using mip maximazing z;
* Solve   centrales_agrupadas using mip maximazing z;

*display z.l;
