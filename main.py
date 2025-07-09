import math
import pandas as pd
import numpy as np
from calculate_IT_S import generate_IT_S_csv
from interpolate import interpolate_temperature
from plots import plot_combined
from params import dia, mes, anio, phi_deg, interval_min
from import_data_meteostat import download_weather_data


# ----- Constantes y parámetros -----
k = 209.30
delta = 0.02
kd = k * delta

W = 0.08
D = 0.02
hc = 1000.0
m_dot = 0.04
Cp = 4190.0

sigma = 5.670374419e-8
epsilon = 0.85

t_insul = 0.2
k_insul = 0.03

tasa_viento = 0.2

k_insul_lat = 0.200
t_insul_lat = 0.025

largo = 1.95
ancho = 0.54
Ac = largo * ancho
A_abs = Ac
espesor_colector = 0.075
perimetro = 2 * (largo + ancho)

def calculate_UL(Tp_list, Ta_list,
                 epsilon_p=0.9, epsilon_c=0.88,
                 hw=2.0, hc_pc=5.7,
                 k_insul=0.02, thickness_insul=0.07,
                 k_insul_lat=0.045, thickness_insul_lat=0.025,
                 largo=1.5, ancho=0.8, t=0.075,
                 max_iter=100, tol=0.01):

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
    hfi = 300

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
    df_I = pd.read_csv("solar_data.csv")
    df = pd.read_csv("temperature_interpolated.csv")
    df = df[(df["Minute"] >= start_minute) & (df["Minute"] < end_minute)].reset_index(drop=True)
    
    Ta_list = df["temp"].values
    IT_list = df_I["IT"].values  # MJ/m² por intervalo
    S_list = df_I["S"].values    # MJ/m² por intervalo
    time_list = df["Minute"].values

    interval_minutes = df["Minute"].iloc[1] - df["Minute"].iloc[0]
    interval_seconds = interval_minutes * 60

    Ti_list = np.zeros_like(Ta_list)
    Ti_list[0] = Ta_list[0] if initial_Ti is None else initial_Ti

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

        UL = UL_array[-1] # W/m2 K
        FR = FR_array[-1]

        Ti_prev = Ti_list[i-1] if i > 0 else Ti_list[0]
        loss_total = UL * (Ti_prev - Ta) * interval_seconds / 1e6  # MJ/m²
        loss_total = max(0, loss_total)
        Qu = Ac * FR * (S - loss_total)  # MJ
        Qu = max(0, Qu)
        q_u = Qu / Ac                    # MJ/m²
        
        # Eficiencia limitada al rango [0, 1] 
        eta = q_u / IT if IT > 0 else 0
       
       

        To = Ti_prev + (q_u * 1e6) / (m_dot * Cp * interval_seconds)

        if i < len(df) - 1:
            
            alpha_a = 0.9 
            Ti_list[i+1] = alpha_a * To + (1 - alpha_a) * Ta

        T_consumer = (To + Ti_prev) / 2
        Tp = Ta + (S - q_u) * 1e6 / (UL * interval_seconds)
        Tp_list.append(Tp)
        e_disp = IT * Ac

        results.append({
            "Minute": minute,
            "Ta": round(Ta, 1),
            "Ti": round(Ti_list[i], 1),
            "UL_total [W/m²K]": round(UL, 6),
            "FR": round(FR, 6),
            "Loss Total [MJ]": round(loss_total*Ac, 6),
            "q_u [MJ]": round(Qu, 6),
            "e_disp [MJ]": round(e_disp, 6),
            "Efficiency η": round(eta, 3),
            "To [°C]": round(To, 2),
            "Tp [°C]": round(Tp, 2),
            "T_cons [°C]": round(T_consumer, 2)

        })

        q_u_total += q_u
        IT_total += IT

    print(len(Tp_list))
    df_results = pd.DataFrame(results)
    df_results.to_csv("results.csv", index=False)
    print("\n--- Tabla exportada: results.csv ---")

    eta_day = q_u_total / IT_total if IT_total > 0 else 0
    Qu_total = q_u_total * Ac
    E_disp = IT_total * Ac

    print("\n--- Daily Results ---")
    print(f"Total solar radiation:               {IT_total:.2f} MJ/m²")
    print(f"Total useful gain per m²:            {q_u_total:.2f} MJ/m²")
    print(f"Total useful heat :     {Qu_total:.2f} MJ")
    print(f"Daily collector efficiency:          {eta_day:.2%}")
    print(f"\nEnergy available :      {E_disp:.2f} MJ")

if __name__ == "__main__":

    
    download_weather_data(output_dir="data/raw") # Obtengo el CSV necesito internet
     # Paso 1: interpolar temperatura desde CSV meteorológico
     
     
    archivo_csv_temp = f"data/raw/datos_meteostat-{dia:02d}-{mes:02d}-{anio:02d}.csv"
    interpolate_temperature(archivo_csv_temp, interval_min=interval_min)
     # Paso 2: calcular irradiancia y S
    generate_IT_S_csv(dia, mes, phi_deg, interval_min)
    # Paso 3: simulación principal
    main()  # esto debería crear 'results.csv' y usar 'solar_data.csv'


    df_results_temp = pd.read_csv("results.csv")
    Ti0 = df_results_temp["To [°C]"].iloc[-1]
    main(initial_Ti=Ti0)

    # Paso 4: gráficos
    plot_combined("solar_data.csv", start_hour=0, end_hour=24)
    
   
