import math
import pandas as pd
import numpy as np

# ----- Parámetros físicos constantes -----
k = 200.0                   # [W/m·K] aluminio
delta = 0.002               # [m] espesor realista de placa metálica
W = 0.1                     # [m]
D = 0.02                    # [m]
hc = 1000.0                 # [W/m²·K]
m_dot = 0.03                # [kg/s]
Cp = 4190.0                # [J/kg·K]
Ac = 2.0                    # [m²]

sigma = 5.670374419e-8      # [W/m²·K⁴]
epsilon = 0.9               # [–] policarbonato alveolar
k_insul = 0.04              # [W/m·K]
thickness_insul = 0.03      # [m] mejor aislación térmica (3 cm)
U_b = k_insul / thickness_insul
viento = 1.0
h_conv = 5.7 + 3.8 * viento

n_collectors = 1


def calculate_UL(Tp_list, Ta_list):
    UL_array = []
    for Tp, Ta in zip(Tp_list, Ta_list):
        Tp_K = Tp + 273.15
        Ta_K = Ta + 273.15
        delta_T = Tp_K - Ta_K
        if abs(delta_T) < 1e-3:
            U_rad = 0.0
        else:
            U_rad = epsilon * sigma * (Tp_K**2 + Ta_K**2) * (Tp_K + Ta_K) / delta_T
        U_t = U_rad + h_conv
        UL_total = U_t + U_b
        UL_array.append(UL_total)
    return UL_array


def calculate_FR(UL_array):
    F_array = []
    Fp_array = []
    Fpp_array = []
    FR_array = []
    for UL in UL_array:
        m = math.sqrt(UL / (k * delta))
        x = m * (W - D) / 2
        F = math.tanh(x) / x if x != 0 else 1.0
        term1 = 1 / hc
        term2 = (D / (W - D)) * (1 / (k * delta)) * (1 / F)
        Fp = 1 / (UL * (term1 + term2))
        num = m_dot * Cp
        den = Fp * UL * Ac
        Fpp = (num / den) * (1 - math.exp(-den / num))
        FR = Fp * Fpp
        F_array.append(F)
        Fp_array.append(Fp)
        Fpp_array.append(Fpp)
        FR_array.append(FR)
    return FR_array


def main(start_hour=6, end_hour=18):
    df = pd.read_csv("solar_data.csv")
    df = df[(df["Hour"] >= start_hour) & (df["Hour"] < end_hour)].reset_index(drop=True)

    Ta_list = df["Ta"].values
    IT_list = df["IT"].values
    S_list = df["S"].values
    Ti_list = df["Ti"].values
    hour_list = df["Hour"].values
    Tp_list = (Ti_list + Ta_list) / 2
    UL_array = calculate_UL(Tp_list, Ta_list)
    FR_array = calculate_FR(UL_array)

    results = []
    q_u_total = 0.0
    IT_total = 0.0

    for i in range(len(df)):
        hour = int(hour_list[i])
        Ta = Ta_list[i]
        IT = IT_list[i]
        S = S_list[i]
        Ti = Ti_list[i]
        UL = UL_array[i]
        FR = FR_array[i]
        loss_total = UL * (Ti - Ta) * 3600 / 1e6

        if S <= loss_total:
            q_u = 0.0
            eta = 0.0
            delta_T = 0.0
        else:
            q_u = FR * (S - loss_total)
            eta = q_u / IT if IT > 0 else 0
            delta_T = (q_u * Ac * 1e6) / (m_dot * Cp)

        q_u_total += q_u
        IT_total += IT

        results.append({
            "Hour": hour,
            "Ta": round(Ta, 2),
            "Ti": round(Ti, 2),
            "UL_total [W/m²K]": round(UL, 2),
            "FR": round(FR, 4),
            "Loss Total [MJ/m²·h]": round(loss_total, 3),
            "q_u [MJ/m²·h]": round(q_u, 3),
            "Efficiency η": round(eta, 3),
            "Delta T [°C]": round(delta_T, 2)
        })

    pd.DataFrame(results).to_csv("results.csv", index=False)

    eta_day = q_u_total / IT_total if IT_total > 0 else 0
    Qu = q_u_total * Ac
    Qu_total = Qu * n_collectors

    E_disp = IT_total * Ac
    E_disp_total = E_disp * n_collectors

    eta_global = Qu / E_disp if E_disp > 0 else 0
    eta_global_total = Qu_total / E_disp_total if E_disp_total > 0 else 0

    delta_T_total = (Qu_total * 1e6) / (n_collectors * m_dot * Cp)

    print("\n--- Daily Results ---")
    print(f"Total solar radiation:               {IT_total:.2f} MJ/m²")
    print(f"Total useful gain per m²:            {q_u_total:.2f} MJ/m²")
    print(f"Total useful heat (1 collector):     {Qu:.2f} MJ")
    print(f"Total useful heat (all collectors):  {Qu_total:.2f} MJ")
    print(f"Daily collector efficiency:          {eta_day:.2%}")
    print(f"\nEnergy available (1 collector):      {E_disp:.2f} MJ")
    print(f"Energy available (all collectors):   {E_disp_total:.2f} MJ")
    print(f"Global efficiency (1 collector):     {eta_global:.2%}")
    print(f"Global efficiency (all collectors):  {eta_global_total:.2%}")
    print(f"\nEstimated temperature rise ΔT total: {delta_T_total:.2f} °C")


if __name__ == "__main__":
    main(start_hour=0, end_hour=24)
