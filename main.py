import math
import pandas as pd
import numpy as np

# ----- Parámetros físicos constantes modificados para mejorar rendimiento -----
k = 209.30                   # [W/m·K] aluminio (igual)
delta = 0.002               # [m] espesor realista de placa metálica (igual)
kd = k * delta          # [W/m²·K] conductividad térmica de la placa metálica (igual)
print(f"Conductividad térmica de la placa metálica: {kd:.2f} W/m²·K")
W = 0.1                     # [m] (igual)
D = 0.02                    # [m] (igual)
hc = 1000.0                 # [W/m²·K] (igual)
m_dot = 0.02                # [kg/s] aumento flujo másico para captar más energía
Cp = 4190.0                 # [J/kg·K] (igual)
Ac = 2.0                    # [m²] (igual)

sigma = 5.670374419e-8      # [W/m²·K⁴] (igual)
epsilon = 0.85               # [–] policarbonato alveolar (igual)
k_insul = 0.03            # [W/m·K] mejor aislante (antes 0.04)
thickness_insul = 0.0254      # [m] aumenté espesor a 5 cm (antes 3 cm)
U_b = k_insul / thickness_insul
viento = 0.2                # menos viento, menos pérdida por convección
h_conv = 5.7 + 3.8 * viento

n_collectors = 1



def calculate_UL(Tp_list, Ta_list,
                 epsilon_p=0.9, epsilon_c=0.88,
                 hw=2.0,
                 hc_pc=5.7,
                 k_insul=0.02, thickness_insul=0.07,
                 k_insul_lat=0.02, thickness_insul_lat=0.04,
                 A_abs=2.0, A_lat=0.5,
                 max_iter=100, tol=0.01):

    sigma = 5.670374419e-8  # W/m²·K⁴
    UL_array = []

    for Tp_C, Ta_C in zip(Tp_list, Ta_list):
        Tp = Tp_C + 273.15
        Ta = Ta_C + 273.15

        # Inicializar Tc
        Tc = Tp - 5

        for _ in range(max_iter):
            denom_pc = (1 / epsilon_p) + (1 / epsilon_c) - 1
            hr_pc = sigma * (Tp + Tc) * (Tp**2 + Tc**2) / denom_pc
            h_pc_total = hc_pc + hr_pc

            # hr y hc entre cubierto y ambiente
            denom_ca = (1 / epsilon_c) + 1 - 1
            hr_ca = sigma * (Tc + Ta) * (Tc**2 + Ta**2) / denom_ca
            hc_ca = 5.7 + 3.8 * hw
            h_ca_total = hr_ca + hc_ca

            # Nuevo valor de Tc por balance
            Ut = 1 / (1 / h_pc_total + 1 / h_ca_total)
            Tc_new = Tp - Ut * (Tp - Ta) / h_pc_total

            if abs(Tc_new - Tc) < tol:
                break
            Tc = Tc_new

        # Calcular Ub y Us
        Ub = k_insul / thickness_insul
        Us = (k_insul_lat / thickness_insul_lat) * (A_lat / A_abs)

        UL_total = Ut + Ub + Us

        print(f"Tp: {Tp_C:.2f} °C, Ta: {Ta_C:.2f} °C, UL_total: {UL_total:.2f} W/m²·K")
        UL_array.append(UL_total)

    return UL_array




def calculate_FR(UL_array):
    F_array = []
    Fp_array = []
    Fpp_array = []
    FR_array = []
    for UL in UL_array:
        if UL <= 0:
            # Evitar raíz cuadrada de negativo o cero
            F_array.append(0)
            Fp_array.append(0)
            Fpp_array.append(0)
            FR_array.append(0)
            continue
        
        hfi = 3852 # [W/m²·K] coeficiente de convección forzado
        m = math.sqrt(UL / (k * delta))
        x = m * (W - D) / 2
        F = math.tanh(x) / x if x != 0 else 1.0
        term1 = 1 / hc
        term2 = (D / (W - D)) * (1 / (k * delta)) * (1 / F)
        Fp = (1 / (UL * W)) * (
        (1 / (UL * (D + (W - D) * F))) +
        (1 / k_insul) +
        (1 / (math.pi * D * hfi)))
        Fp = 0.841 # Valor fijo para simplificar el cálculo
        print(f"UL: {UL:.2f} W/m²·K, F: {F:.4f}, Fp: {Fp:.4f}")
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

        Qu = Ac * FR * ( S - loss_total)  # MJ/m²·h
        print(f"Hour {hour}: Ta = {Ta:.2f} °C, IT = {IT:.2f} MJ/m²·h, S = {S:.2f} MJ/m²·h, Ti = {Ti:.2f} °C, UL = {UL:.2f} W/m²·K, FR = {FR:.4f}, Loss Total = {loss_total:.3f} MJ/m²·h")

        q_u = Qu / Ac  # MJ/m²·h
        if q_u < 0:
            q_u = 0
        eta = q_u / IT if IT > 0 else 0
        To = Ti + (q_u * 1e6) / (m_dot * Cp * 3600)
        print(f"Hour {hour}: q_u = {q_u:.3f} MJ/m²·h, eta = {eta:.3%}, delta_T = {To:.2f} °C")

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
            "To [°C]": round(To, 2)
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
    main(0, 24)

