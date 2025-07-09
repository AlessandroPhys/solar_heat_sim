from meteostat import Hourly
from datetime import datetime, timedelta
import os
import pandas as pd
from params import dia, mes, anio

def download_weather_data(output_dir="data/raw"):
    os.makedirs(output_dir, exist_ok=True)

    # Período en UTC
    start = datetime(anio, mes, dia, 0, 0)
    end = datetime(anio, mes, dia, 23, 59)

    station_id = "87166"

    # Descargar datos horarios (en UTC)
    data = Hourly(station_id, start, end).fetch()

    if data.empty:
        print(f"No hay datos para la estación {station_id} en esa fecha.")
        return

    # Resetear índice y quedarte con las columnas necesarias
    data = data.reset_index()[["time", "temp"]]

    # Corregir hora UTC → hora local (UTC-3)
    data["time"] = data["time"] + timedelta(hours=-3)

    filename = f"{output_dir}/datos_meteostat-{dia:02d}-{mes:02d}-{anio:02d}.csv"
    data.to_csv(filename, index=False)
    print(f"Archivo guardado: {filename}")

if __name__ == "__main__":
    download_weather_data()
