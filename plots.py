import pandas as pd
import matplotlib.pyplot as plt
from params import m_dot, Cp, Ac

def plot_temperatures():
    # Cargar datos
    df_data = pd.read_csv("solar_data.csv")
    df_results = pd.read_csv("results.csv")

    # Extraer Ti y Qu
    Ti = df_data["Ti"]
    Qu = df_results["q_u [MJ/m²·h]"] * Ac  # MJ por colector

    # Calcular To (en grados Celsius)
    To = Ti + (Qu * 1e6) / (m_dot * Cp * 3600)

    # Extraer horas
    hours = [int(h.split(":")[0]) for h in df_results["Hour"]]

    # Graficar
    plt.figure(figsize=(8, 4))
    plt.plot(hours, Ti, marker='o', linestyle='-', label='Inlet Temperature Ti (°C)', color='blue')
    plt.plot(hours, To, marker='o', linestyle='--', label='Outlet Temperature To (°C)', color='red')

    plt.title("Inlet and Outlet Water Temperature")
    plt.xlabel("Hour of Day")
    plt.ylabel("Temperature (°C)")
    plt.xticks(hours)
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    plot_temperatures()
