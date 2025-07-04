import pandas as pd
import numpy as np
from params import Us, Ub, UL, F_, m_dot, Cp, Ac, n_collectors

def main():
    df = pd.read_csv("solar_data.csv")

    Ta_list = df["Ta"].values
    IT_list = df["IT"].values
    S_list = df["S"].values
    Ti_list = df["Ti"].values

    mf = (m_dot * Cp) / (Ac * UL * F_)
    Fpp = mf * (1 - np.exp(-1 / mf))
    FR = F_ * Fpp

    print(f"Collector flow factor (F'') = {Fpp:.3f}")
    print(f"Heat removal factor (F_R)   = {FR:.3f}\n")

    results = []

    q_u_total = 0.0
    IT_total = 0.0
    S_total = 0.0  # Para acumular radiación absorbida

    for i in range(len(df)):
        hour = int(df["Hour"][i])
        Ta = Ta_list[i]
        IT = IT_list[i]
        S = S_list[i]
        Ti = Ti_list[i]

        loss_surface = Us * (Ti - Ta) * 3600 / 1e6  # MJ/m²·h
        loss_bottom = Ub * (Ti - Ta) * 3600 / 1e6   # MJ/m²·h
        loss_total = loss_surface + loss_bottom

        if S <= loss_total:
            q_u = 0.0
            eta = 0.0
        else:
            q_u = FR * (S - loss_total)
            eta = q_u / IT if IT > 0 else 0

        q_u_total += q_u
        IT_total += IT
        S_total += S

        results.append({
            "Hour": f"{hour}:00-{hour+1}:00",
            "Loss Surface Us [MJ/m²·h]": round(loss_surface, 3),
            "Loss Bottom Ub [MJ/m²·h]": round(loss_bottom, 3),
            "Loss Total UL [MJ/m²·h]": round(loss_total, 3),
            "q_u [MJ/m²·h]": round(q_u, 3),
            "Efficiency η": round(eta, 3)
        })

    pd.DataFrame(results).to_csv("results.csv", index=False)

    eta_day = q_u_total / IT_total if IT_total > 0 else 0
    Qu = q_u_total * Ac  # MJ por colector
    Qu_total = Qu * n_collectors

    E_disp_incident = IT_total * Ac    # Energía solar incidente total (MJ)
    E_disp_absorbed = S_total * Ac     # Energía térmica absorbida (MJ)

    eta_global = Qu / E_disp_absorbed if E_disp_absorbed > 0 else 0
    eta_global_total = Qu_total / (E_disp_absorbed * n_collectors) if E_disp_absorbed > 0 else 0

    # Energía total perdida por el colector (MJ)
    energy_loss_total = 0.0
    for i in range(len(df)):
        Ti = Ti_list[i]
        Ta = Ta_list[i]
        loss_total = UL * (Ti - Ta) * 3600 / 1e6  # MJ/m²·h
        energy_loss_total += loss_total
    energy_loss_total *= Ac  # MJ total para el área

    print("\n--- Daily Results ---")
    print(f"Total solar radiation incident:           {E_disp_incident:.2f} MJ")
    print(f"Total thermal energy absorbed (S * A):    {E_disp_absorbed:.2f} MJ")
    print(f"Total useful gain per m²:                   {q_u_total:.2f} MJ/m²")
    print(f"Total useful heat (1 collector):            {Qu:.2f} MJ")
    print(f"Total useful heat (all collectors):         {Qu_total:.2f} MJ")
    print(f"Daily collector efficiency:                 {eta_day:.2%}")
    print(f"Global efficiency (based on absorbed):     {eta_global:.2%}")
    print(f"Global efficiency total (all collectors):  {eta_global_total:.2%}")
    print(f"Total energy lost by the collector:         {energy_loss_total:.2f} MJ")

if __name__ == "__main__":
    main()
