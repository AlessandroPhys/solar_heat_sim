import pandas as pd
import numpy as np
from params import F_, m_dot, Cp, Ac, n_collectors
from heat_loss_components import calculate_UL

def main():
    df = pd.read_csv("solar_data.csv")

    Ta_list = df["Ta"].values
    IT_list = df["IT"].values
    S_list = df["S"].values
    Ti_list = df["Ti"].values

    results = []

    q_u_total = 0.0
    IT_total = 0.0

    # Parámetros físicos reales basados en materiales indicados

    h_conv = 5.0                  # Coeficiente convección natural en aire [W/m²·K], rango típico 5-25, tomamos bajo para calma
    epsilon_plate = 0.90          # Emisividad pintura negro mate (placa absorbente)
    epsilon_glass = 0.85          # Emisividad policarbonato alveolar
    k_ins = 0.03                  # Conductividad térmica poliestireno expandido (aislante)
    d_ins = 0.0254                # Espesor del aislamiento poliestireno expandido, 2.54 cm (1 pulgada)


    for i in range(len(df)):
        hour = int(df["Hour"][i])
        Ta = Ta_list[i]
        IT = IT_list[i]
        S = S_list[i]
        Ti = Ti_list[i]

        Tp = (Ti + Ta) / 2  # estimación para temperatura de la placa
        UL = calculate_UL(Tp, Ta, h_conv, epsilon_plate, epsilon_glass, k_ins, d_ins)

        print(f"Hour {hour}: UL = {UL:.2f} W/m²K")  # Debug: mostrar UL por hora

        mf = (m_dot * Cp) / (Ac * UL * F_)
        Fpp = mf * (1 - np.exp(-1 / mf))
        FR = F_ * Fpp

        loss_total = UL * (Ti - Ta) * 3600 / 1e6  # MJ/m²·h

        if S <= loss_total:
            q_u = 0.0
            eta = 0.0
        else:
            q_u = FR * (S - loss_total)
            eta = q_u / IT if IT > 0 else 0

        q_u_total += q_u
        IT_total += IT

        results.append({
            "Hour": f"{hour}:00-{hour+1}:00",
            "UL_total [W/m²K]": round(UL, 2),
            "Loss Total [MJ/m²·h]": round(loss_total, 3),
            "q_u [MJ/m²·h]": round(q_u, 3),
            "Efficiency η": round(eta, 3)
        })

    # Guardar resultados horarios como CSV
    pd.DataFrame(results).to_csv("results.csv", index=False)

    # Resumen final
    eta_day = q_u_total / IT_total if IT_total > 0 else 0
    Qu = q_u_total * Ac  # MJ por colector
    Qu_total = Qu * n_collectors

    E_disp = IT_total * Ac  # MJ disponibles para un colector
    E_disp_total = E_disp * n_collectors  # para el arreglo completo

    eta_global = Qu / E_disp if E_disp > 0 else 0
    eta_global_total = Qu_total / E_disp_total if E_disp_total > 0 else 0

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

if __name__ == "__main__":
    main()
