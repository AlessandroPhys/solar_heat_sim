import pandas as pd
import numpy as np
from params import dia, mes, anio, phi_deg, interval_min

def interpolate_temperature(input_file, output_file="temperature_interpolated.csv", interval_min=15, final_minute=1440 - interval_min):
    # Leer CSV original con parsing de fechas
    df = pd.read_csv(input_file, parse_dates=["time"])

    # Crear columna Minute desde la fecha/hora
    df["Minute"] = df["time"].dt.hour * 60 + df["time"].dt.minute
    df = df.set_index("Minute").sort_index()

    # Rango de minutos para interpolar, desde primer minuto hasta final_minute en pasos de interval_min
    minute_range = np.arange(df.index.min(), final_minute + 1, interval_min)

    # Reindexar para agregar filas intermedias
    df_interp = df.reindex(minute_range)

    # Interpolación lineal para 'temp'
    df_interp["temp"] = df_interp["temp"].interpolate(method="linear")

    # Extrapolar al final si quedan NaN (valores fuera del rango original)
    if df_interp["temp"].isna().any():
        last_valid = df_interp["temp"].last_valid_index()
        # Pendiente aproximada entre los dos últimos puntos válidos
        last_vals = df_interp.loc[last_valid-interval_min:last_valid, "temp"]
        slope = (last_vals.iloc[-1] - last_vals.iloc[0]) / interval_min
        for i in range(last_valid + interval_min, final_minute + 1, interval_min):
            df_interp.loc[i, "temp"] = df_interp.loc[i - interval_min, "temp"] + slope

    # Exportar archivo con Minute y temp
    df_interp_out = df_interp[["temp"]].reset_index().rename(columns={"index": "Minute"})
    df_interp_out.to_csv(output_file, index=False)
    print(f"Archivo exportado como: {output_file}")

if __name__ == "__main__":
    filename = f"data/raw/datos_meteostat-{dia:02d}-{mes:02d}-{anio:02d}.csv"
    interpolate_temperature(filename, interval_min=interval_min, final_minute=1440 - interval_min)
