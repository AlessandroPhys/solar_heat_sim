import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from math import pi

I_sc = 1367  # Irradiación solar extraatmosférica
tau_alpha = 0.85
R = 0.89

def get_n(dia, mes):
    meses_dias_acum = [0,31,59,90,120,151,181,212,243,273,304,334]
    return meses_dias_acum[mes-1] + dia

def get_delta(n):
    B = (pi/180)*((n-1)*360/365)
    return (
        0.006918
        - 0.399912*np.cos(B)
        + 0.070257*np.sin(B)
        - 0.006758*np.cos(2*B)
        + 0.000907*np.sin(2*B)
        - 0.002697*np.cos(3*B)
        + 0.00148*np.sin(3*B)
    )

def get_omega(t_sec):
    # Corrección: omega en radianes con omega=0 a mediodía solar
    t_hour = t_sec / 3600
    omega_deg = 15 * (t_hour - 12)
    return np.radians(omega_deg)

def get_alt_solar(delta, phi, omega):
    theta_z = np.arccos(np.sin(delta)*np.sin(phi) + np.cos(delta)*np.cos(phi)*np.cos(omega))
    alpha = 90 - np.degrees(theta_z)
    return alpha

def correction_factor(n):
    return (
        1.00011 + 0.034221*np.cos(2*np.pi*n/365) +
        0.00128*np.sin(2*np.pi*n/365) +
        0.000719*np.cos(4*np.pi*n/365) +
        0.000077*np.sin(4*np.pi*n/365)
    )

def irradiance_from_altitude(alpha_deg, n):
    alpha_rad = np.radians(alpha_deg)
    E0 = correction_factor(n)
    I = I_sc * E0 * np.sin(alpha_rad)
    I[I < 0] = 0
    return I

def apply_cloudiness_variation(IT_array, block_size=60, low=0.91, high=1.04):
    IT_mod = IT_array.copy()
    n_blocks = len(IT_array) // block_size + 1
    factors = np.random.uniform(low, high, size=n_blocks)

    for i in range(n_blocks):
        start = i * block_size
        end = min((i+1) * block_size, len(IT_array))  # corregido
        IT_mod[start:end] *= factors[i]

    return IT_mod

def generate_IT_S_csv(dia=15, mes=6, phi_deg=-27,
                      start_hour=0, end_hour=23, interval_min=15,
                      input_csv="solar_data.csv"):
    # Leer archivo anterior para recuperar Ta y Ti (si hay)
    try:
        df_prev = pd.read_csv(input_csv)
        Ta_prev = df_prev["Ta"].values
        Ti_prev = df_prev["Ti"].values
    except:
        Ta_prev = None
        Ti_prev = None

    H_horizontal = {
        1: 6.2, 2: 5.8, 3: 5.0, 4: 4.1, 5: 3.3, 6: 2.8,
        7: 3.0, 8: 3.9, 9: 5.0, 10: 5.7, 11: 6.1, 12: 6.3
    }
    R_values = {
        1: 1.13, 2: 1.15, 3: 1.12, 4: 1.10, 5: 1.08, 6: 1.05,
        7: 1.05, 8: 1.07, 9: 1.10, 10: 1.12, 11: 1.14, 12: 1.15
    }
    tau_alpha = 0.9  # Transmitancia y absorción del colector
    H_mes = H_horizontal[mes]  # kWh/m² mes
    R_mes = R_values[mes]
    S_deseado = tau_alpha * R_mes * H_mes * 3.6 * 1e6  # J/m²·día

    times = np.arange(start_hour * 60, (end_hour + 1) * 60, interval_min)

    phi = np.radians(phi_deg)
    n = get_n(dia, mes)
    delta = get_delta(n)
    omegas = np.array([get_omega(t*60) for t in times])  # Multiplicar por 60 para pasar minutos a segundos
    alphas = np.array([get_alt_solar(delta, phi, omega) for omega in omegas])
    alphas[alphas < 0] = 0

    alpha_norm = alphas / np.max(alphas)

    E0 = correction_factor(n)
    IT_Wm2 = I_sc * E0 * alpha_norm  # irradiancia instantánea [W/m²]


    energia_total_actual = np.sum(IT_Wm2 * 300)  # energía total diaria [J/m²]
    factor = S_deseado / energia_total_actual
    IT_Wm2 *= factor
    IT_Whm2 = IT_Wm2 * (interval_min / 60)
    
    IT_MJm2h = IT_Whm2 * 0.0036

    # Perturbación por nubes
    
    
    IT_MJm2h = apply_cloudiness_variation(IT_MJm2h, block_size=1, low=0.73, high=1.12)

    S_MJm2h = IT_MJm2h * tau_alpha * R

    if Ta_prev is not None:
        Ta_interp = np.interp(times, np.linspace(0, 1440, len(Ta_prev)), Ta_prev)
        factor_Ta = np.random.normal(loc=1.0, scale=0.02, size=Ta_interp.shape)
        factor_Ta = np.clip(factor_Ta, 0.95, 1.05)
        Ta = np.round(Ta_interp * factor_Ta, 1)
    else:
        Ta = np.linspace(18, 26, len(times))  # día genérico

    Ti = Ta.copy()

    df = pd.DataFrame({
        "Minute": times,
        "Ta": Ta,
        "IT": np.round(IT_MJm2h, 4),
        "S": np.round(S_MJm2h, 4),
        "Ti": Ti
    })

    print("Alphas (grados):", alphas)
    print("IT_MJm2h (primeros valores):", IT_MJm2h[:10])
    print("S_MJm2h (primeros valores):", S_MJm2h[:10])

    df.to_csv("solar_data.csv", index=False)
    print(f"CSV generado con intervalos de {interval_min} minutos.")

if __name__ == "__main__":
    generate_IT_S_csv(dia=21, mes=12, phi_deg=-27, interval_min=15)
