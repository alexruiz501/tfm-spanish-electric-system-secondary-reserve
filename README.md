# tfm-spanish-electric-system-secondary-reserve

In this project you can find all programs and resulting data used for the Master's Thesis *nombre aquí*.

This ReadMe file is only a reference of what can be found here, but it requires reading the Thesis to get a full understanding of the files present in this project.


## Reading and processing data to analyse it

In the folder `read_raw_data` there are several python scripts that have been used to process the raw data which is formed by the files *I90DIA* belonging to the dates of this study (2014-2018) downloaded from the [esios.ree.es](esios.ree.es) website.

The main files in the folder are `lectura_datos_brutos.py` and `procesado_datos.py`. The script `lectura_datos_brutos.py` reads all the excel files and exctracts relevant information that is then stored as a simple csv file containing information about every *Unidad de Programación* (UP) regarding their participation in the electricity market. This resulting file is `processed-data/tabla_potencia_agregada.zip`. It also captures general market data such as prices and secondary reserve requirements and saves them to the file `tabla_datos_mercado.csv`. The script `procesado_datos.py` then takes this csv and further processes it to get what has been called in the Thesis *power margins*, which are computed by UP (`processed-data/tabla_margenes_potencia_up.*`) and by *Zona de Regulación* (ZR) (`processed-data/tabla_margenes_potencia_empresas.zip`).

The other files in this folder are auxiliary functions that are called in the previously mentioned scripts.


## Optimisation

The folder `optimisation` contains all the necessary files to create the optimisation models used in the Thesis and to run them with the input data from the markets (`tabla_datos_mercado.csv`). The files `modelo_varias_centrales_sin_datos_juntas.gms` and `modelo_varias_centrales_sin_datos_separadas.gms` contain the equations of the models of the 3 UPs in the same ZR and of the 3 UPs as their own ZR, respectively. The script `full-time-optimisation.py` reads market data from every day in the study interval and calls the GAMS solver to optimise both models. The final result is saved as `processed-data/optimizacion_juntas.csv` and `processed-data/optimizacion_separadas.csv`.

## Visualisation

The folder `Visualisation` contains Jupyter Notebook files where the results can be shown graphically.
