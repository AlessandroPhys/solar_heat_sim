import math
import pandas as pd
import numpy as np

# ----- Constantes y parámetros -----
k = 209.30
delta = 0.02
kd = k * delta
print(f"Conductividad térmica de la placa metálica: {kd:.2f} W/m²·K")

W = 0.1
D = 0.02
hc = 1000.0
m_dot = 0.05
Cp = 4190.0
Ac = 1.2

sigma = 5.670374419e-8
epsilon = 0.85

t_insul = 0.0254
k_insul = 0.03
U_b = k_insul / t_insul

tasa_viento = 0.2
h_conv = 5.7 + 3.8 * tasa_viento

k_insul_lat = 0.200
t_insul_lat = 0.025

largo = 1.5
ancho = 0.8
espesor_colector = 0.075
A_abs = largo * ancho
perimetro = 2 * (largo + ancho)

k_air = 0.0293
nu = 196e-6
Pr = 0.7

def calculate_UL(Tp_list, Ta_list,
                 epsilon_p=0.9, epsilon_c=0.88,
                 hw=2.0, hc_pc=5.7,
                 k_insul=0.02, thickness_insul=0.07,
                 k_insul_lat=0.045, thickness_insul_lat=0.025,
                 largo=1.5, ancho=0.8, t=0.075,
                 max_iter=100, tol=0.01):

    sigma = 5.670374419e-8
    UL_array = []
    Ac = largo * ancho
    perimetro = 2 * (largo + ancho)

    for Tp_C, Ta_C in zip(Tp_list, Ta_list):
        Tp = Tp_C + 273.15
        Ta = Ta_C + 273.15
        Tc = Tp - 5

        for _ in range(max_iter):
            denom_pc = (1 / epsilon_p) + (1 / epsilon_c) - 1
            hr_pc = sigma * (Tp + Tc) * (Tp**2 + Tc**2) / denom_pc
            h_pc_total = hc_pc + hr_pc

            denom_ca = (1 / epsilon_c)
            hr_ca = sigma * (Tc + Ta) * (Tc**2 + Ta**2) / denom_ca
            hc_ca = 5.7 + 3.8 * hw
            h_ca_total = hr_ca + hc_ca

            Ut = 1 / (1 / h_pc_total + 1 / h_ca_total)
            Tc_new = Tp - Ut * (Tp - Ta) / h_pc_total

            if abs(Tc_new - Tc) < tol:
                break
            Tc = Tc_new

        Ub = k_insul / thickness_insul
        Ue = (k_insul_lat / thickness_insul_lat) * (perimetro * t / Ac)

        UL_total = Ut + Ub + Ue
        UL_array.append(UL_total)

    return UL_array

def calculate_FR(UL_array):
    FR_array = []
    hfi = 3852

    for UL in UL_array:
        if UL <= 0:
            FR_array.append(0)
            continue

        m = math.sqrt(UL / (k * delta))
        x = m * (W - D) / 2
        F = math.tanh(x) / x if x != 0 else 1.0

        denom = UL * W * (
            (1 / (UL * (D + (W - D) * F))) +
            (1 / (math.pi * D * hfi))
        )
        Fp = 1 / denom

        num = m_dot * Cp
        den = Fp * UL * Ac
        Fpp = (num / den) * (1 - math.exp(-den / num))
        FR = Fp * Fpp

        FR_array.append(FR)

    return FR_array

def main(start_minute=0, end_minute=1440, initial_Ti=None):
    df = pd.read_csv("solar_data.csv")
    df = df[(df["Minute"] >= start_minute) & (df["Minute"] < end_minute)].reset_index(drop=True)

    Ta_list = df["Ta"].values
    IT_list = df["IT"].values
    S_list = df["S"].values
    time_list = df["Minute"].values

    interval_minutes = df["Minute"].iloc[1] - df["Minute"].iloc[0]
    interval_seconds = interval_minutes * 60

    Ti_list = np.zeros_like(Ta_list)
    Ti_list[0] = Ta_list[0]

    q_u_total = 0.0
    IT_total = 0.0
    Tp_list = []
    results = []

    for i in range(len(df)):
        Tp_init_list = (Ti_list[:i+1] + Ta_list[:i+1]) / 2
        UL_array = calculate_UL(Tp_init_list, Ta_list[:i+1])
        FR_array = calculate_FR(UL_array)

        minute = int(time_list[i])
        Ta = Ta_list[i]
        IT = IT_list[i]
        S = S_list[i]

        UL = UL_array[-1]
        FR = FR_array[-1]

        Ti_prev = Ti_list[i-1] if i > 0 else Ti_list[0]
        loss_total = UL * (Ti_prev - Ta) * interval_seconds / 1e6
        Qu = Ac * FR * (S - loss_total)
        q_u = Qu / Ac
        eta = q_u / IT if IT > 0 else 0
        To = Ti_prev + (q_u * 1e6) / (m_dot * Cp * interval_seconds)

        if i < len(df) - 1:
            alpha_a = 0.8  # Por ejemplo, 80% del agua recircula y 20% es fresca
            Ti_list[i+1] = alpha_a * To + (1 - alpha_a) * Ta


        Tp = Ta + (S - q_u) / UL if (UL > 0 and q_u > 0) else Ta
        Tp_list.append(Tp)

        results.append({
            "Minute": minute,
            "Ta": round(Ta, 1),
            "Ti": round(Ti_list[i], 1),
            "UL_total [W/m²K]": round(UL, 2),
            "FR": round(FR, 4),
            "Loss Total [MJ/m²]": round(loss_total, 3),
            "q_u [MJ/m²]": round(q_u, 3),
            "Efficiency η": round(eta, 3),
            "To [°C]": round(To, 2),
            "Tp [°C]": round(Tp, 2)
        })

        q_u_total += q_u
        IT_total += IT

    df_results = pd.DataFrame(results)
    df_results.to_csv("results.csv", index=False)
    print("\n--- Tabla exportada: results.csv ---")

    eta_day = q_u_total / IT_total if IT_total > 0 else 0
    Qu_total = q_u_total * Ac
    E_disp = IT_total * Ac
    eta_global = Qu_total / E_disp if E_disp > 0 else 0

    print("\n--- Daily Results ---")
    print(f"Total solar radiation:               {IT_total:.2f} MJ/m²")
    print(f"Total useful gain per m²:            {q_u_total:.2f} MJ/m²")
    print(f"Total useful heat (1 collector):     {Qu_total:.2f} MJ")
    print(f"Daily collector efficiency:          {eta_day:.2%}")
    print(f"\nEnergy available (1 collector):      {E_disp:.2f} MJ")
    print(f"Global efficiency (1 collector):     {eta_global:.2%}")

if __name__ == "__main__":
    # Primera pasada para estimar la salida al final del día
    main()
    df_results_temp = pd.read_csv("results.csv")
    Ti0 = df_results_temp["To [°C]"].iloc[-1]

    # Segunda pasada con mejor estimación del estado inicial
    main(initial_Ti=Ti0)
