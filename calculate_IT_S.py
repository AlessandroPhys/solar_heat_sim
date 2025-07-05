import numpy as np
import pandas as pd
from math import pi

# Constantes
I_sc = 1367
tau_alpha = 0.85
R = 0.89

def get_n(dia, mes):
    meses_dias_acum = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
    return meses_dias_acum[mes-1] + dia

def get_delta(n):
    B = (pi / 180) * ((n - 1) * 360 / 365)
    return (
        0.006918
        - 0.399912 * np.cos(B)
        + 0.070257 * np.sin(B)
        - 0.006758 * np.cos(2 * B)
        + 0.000907 * np.sin(2 * B)
        - 0.002697 * np.cos(3 * B)
        + 0.00148 * np.sin(3 * B)
    )

def get_omega(t_min):
    omega_dot = 15 / 60
    omega_0 = -90 - 6 * 60 * omega_dot
    omega_deg = omega_0 + omega_dot * t_min
    return np.radians(omega_deg)

def get_alt_solar(delta, phi, omega):
    from numpy import arccos, sin, cos, degrees
    theta_z = np.arccos(np.sin(delta)*np.sin(phi) + np.cos(delta)*np.cos(phi)*np.cos(omega))
    alpha = 90 - np.degrees(theta_z)
    return alpha

def correction_factor(n):
    return (
        1.00011 + 0.034221 * np.cos(2 * np.pi * n / 365) +
        0.00128 * np.sin(2 * np.pi * n / 365) +
        0.000719 * np.cos(4 * np.pi * n / 365) +
        0.000077 * np.sin(4 * np.pi * n / 365)
    )

def irradiance_from_altitude(alpha_deg, n):
    alpha_rad = np.radians(alpha_deg)
    E0 = correction_factor(n)
    I = I_sc * E0 * np.sin(alpha_rad)
    I[I < 0] = 0
    return I

def generate_IT_S_csv(
    dia=15, mes=1, phi_deg=-27, start_hour=0, end_hour=23,
    interval_min=60, input_csv="solar_data.csv"
):
    # Leer los valores de Ta y Ti existentes
    df_prev = pd.read_csv(input_csv)
    Ta = df_prev["Ta"].values
    Ti = df_prev["Ti"].values

    phi = np.radians(phi_deg)
    n = get_n(dia, mes)

    times = np.arange(start_hour*60, end_hour*60 + interval_min, interval_min)
    alphas = np.array([get_alt_solar(get_delta(n), phi, get_omega(t)) for t in times])
    IT_Wm2 = irradiance_from_altitude(alphas, n)

    IT_Whm2 = IT_Wm2 * (interval_min / 60)
    IT_MJm2h = IT_Whm2 * 0.0036

    # --- Factor aleatorio para simular nubes ---
    np.random.seed(5000)  # para reproducibilidad
    factor_nubes = np.random.normal(loc=1.0, scale=0.1, size=IT_MJm2h.shape)
    factor_nubes = np.clip(factor_nubes, 0.4, 1.0)  # limitar entre 0.4 y 1.0

    IT_MJm2h *= factor_nubes  # aplicar perturbación

    # --- Factor aleatorio para simular fluctuaciones en Ta ---
    factor_Ta = np.random.normal(loc=1.0, scale=0.02, size=Ta.shape)
    factor_Ta = np.clip(factor_Ta, 0.95, 1.05)  # limitar entre 0.95 y 1.05
    Ta_perturbado = Ta * factor_Ta

    S_MJm2h = IT_MJm2h * tau_alpha * R

    df = pd.DataFrame({
        "Hour": (times / 60).astype(int),
        "Ta": np.round(Ta_perturbado, 1),  # ahora con fluctuación
        "IT": np.round(IT_MJm2h, 4),
        "S": np.round(S_MJm2h, 4),
        "Ti": np.round(Ti, 1)
    })

    df.to_csv("solar_data.csv", index=False)
    print("Archivo 'solar_data.csv' actualizado con irradiancia, radiación absorbida y Ta fluctuante.")
    print(df)

if __name__ == "__main__":
    generate_IT_S_csv(dia=15, mes=1, phi_deg=-27, start_hour=0, end_hour=23)
