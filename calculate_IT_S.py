import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from math import pi

I_sc = 1367  # Irradiación solar extraatmosférica (W/m²)

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
    t_hour = t_sec / 3600
    omega_deg = 15 * (t_hour - 12)
    return np.radians(omega_deg)

def get_alt_solar(delta, phi, omega):
    cos_theta_z = np.sin(delta)*np.sin(phi) + np.cos(delta)*np.cos(phi)*np.cos(omega)
    cos_theta_z = np.clip(cos_theta_z, -1, 1)
    theta_z = np.arccos(cos_theta_z)
    alpha = 90 - np.degrees(theta_z)
    return alpha if alpha > 0 else 0

def correction_factor(n):
    return (
        1.00011 + 0.034221*np.cos(2*np.pi*n/365) +
        0.00128*np.sin(2*np.pi*n/365) +
        0.000719*np.cos(4*np.pi*n/365) +
        0.000077*np.sin(4*np.pi*n/365)
    )

def apply_cloudiness_variation(IT_array, block_size=60, low=0.91, high=1.04):
    IT_mod = IT_array.copy()
    n_blocks = int(np.ceil(len(IT_array) / block_size))
    factors = np.random.uniform(low, high, size=n_blocks)

    for i in range(n_blocks):
        start = i * block_size
        end = min((i+1) * block_size, len(IT_array))
        IT_mod[start:end] *= factors[i]

    return IT_mod


def generate_IT_S_csv(dia=21, mes=12, phi_deg=-27, interval_min=15):
    H_horizontal = {1: 6.5, 2: 6, 3: 5.0, 4: 4.0, 5: 3.0, 6: 2.5,
                    7: 2.5, 8: 3.5, 9: 4.0, 10: 5.5, 11: 6, 12: 6.5}
    R_values = {1: 0.89, 2: 0.95, 3: 1.04, 4: 1.15, 5: 1.30, 6: 1.35,
                7: 1.33, 8: 1.20, 9: 1.07, 10: 0.97, 11: 0.91, 12: 0.88}

    tau_alpha_local = 0.9
    H_mes = H_horizontal[mes]
    R_mes = R_values[mes]
    S_deseado = tau_alpha_local * R_mes * H_mes * 3.6e6

    times_min = np.arange(0, 1440, interval_min)
    phi = np.radians(phi_deg)
    n = get_n(dia, mes)
    delta = get_delta(n)
    omegas = np.array([get_omega(t*60) for t in times_min])
    alphas = np.array([get_alt_solar(delta, phi, omega) for omega in omegas])

    max_alpha = np.max(alphas)
    alpha_norm = alphas / max_alpha if max_alpha > 0 else np.zeros_like(alphas)

    E0 = correction_factor(n)
    IT_Wm2 = I_sc * E0 * alpha_norm
    IT_Wm2 = np.clip(IT_Wm2, 0, None)

    energia_total_actual = np.sum(IT_Wm2 * interval_min * 60)
    factor = S_deseado / energia_total_actual if energia_total_actual > 0 else 1
    IT_Wm2 *= factor

    IT_Jm2_interval = IT_Wm2 * interval_min * 60
    IT_MJm2 = IT_Jm2_interval / 1e6
    IT_MJm2 = apply_cloudiness_variation(IT_MJm2, block_size=1, low=0.73, high=1.12)
    S_MJm2 = IT_MJm2 * tau_alpha_local * R_mes

    df_data= pd.read_csv("solar_data.csv")
    Ti = df_data["Ti"]
    Ta = df_data["Ta"]
    
    print(IT_MJm2)
    print(S_MJm2)
    df = pd.DataFrame({
        "Minute": times_min,
        "Ta": Ta,
        "IT": np.round(IT_MJm2, 6),
        "S": np.round(S_MJm2, 6),
        "Ti": Ti
    })

    df.to_csv("solar_data.csv", index=False)
    print(f"CSV generado con intervalos de {interval_min} minutos.")

    plt.figure(figsize=(10,5))
    plt.plot(times_min/60, IT_MJm2, label='Irradiancia (MJ/m² por intervalo)')
    plt.xlabel('Hora del día [h]')
    plt.ylabel('Energía solar [MJ/m²]')
    plt.title(f'Irradiancia solar el día {dia}/{mes}')
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.show()

    intervals_per_hour = int(60 / interval_min)
    hours = np.arange(0, 24)
    energy_per_hour = []
    for h in range(len(hours)):
        start_idx = h * intervals_per_hour
        end_idx = start_idx + intervals_per_hour
        energy_h = np.sum(IT_MJm2[start_idx:end_idx])
        energy_per_hour.append(energy_h)

    print("\nEnergía solar por hora (MJ/m²):")
    print("Hora\tEnergía [MJ/m²]")
    for h, energy_h in zip(hours, energy_per_hour):
        print(f"{h:02d}:00\t{energy_h:.4f}")

if __name__ == "__main__":
    generate_IT_S_csv(dia=21, mes=12, phi_deg=-27, interval_min=15)