import pandas as pd
import numpy as np

def generate_IT_S_csv(start_hour=6, end_hour=18):
    if end_hour <= start_hour + 1:
        raise ValueError("El rango horario debe tener al menos 2 horas")

    hours = np.arange(start_hour, end_hour)

    # Datos fijos para enero
    H_barra = 6.5  # kWh/m2/día horizontal para enero
    R = 0.89       # Factor de corrección para plano inclinado
    tau_alpha = 0.85

    # Irradiancia solo entre 6 y 18
    irradiance = []
    for h in hours:
        if 6 <= h <= 18:
            theta = np.pi * (h - 6) / 12  # 0 a pi de 6 a 18
            irradiance.append(np.sin(theta))  # W/m2, máximo a mediodía
        else:
            irradiance.append(0.0)
    irradiance = np.array(irradiance)

    # Energía diaria total corregida
    H_barra_Wh = H_barra * 1000
    E_inclined_daily = H_barra_Wh * R

    E_hourly_Wh = irradiance / irradiance.sum() * E_inclined_daily
    S_Wm2 = E_hourly_Wh * tau_alpha

    I_T_MJm2h = np.round(E_hourly_Wh * 0.0036, 2)
    S_MJm2h = np.round(S_Wm2 * 0.0036, 2)

    # Temperatura ambiente tipo verano
    Ta = 24 + 6 * np.sin((hours - 12) * np.pi / 12)
    Ta = np.round(Ta, 1)
    Ti = Ta.copy()

    df = pd.DataFrame({
        "Hour": hours,
        "Ta": Ta,
        "IT": I_T_MJm2h,
        "S": S_MJm2h,
        "Ti": Ti
    })

    filename = "solar_data.csv"
    df.to_csv(filename, index=False)
    print(f"Archivo {filename} creado con éxito.")
    print(df)

# Ejemplo
generate_IT_S_csv(0, 24)
