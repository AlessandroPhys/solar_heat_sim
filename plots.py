import pandas as pd
import matplotlib.pyplot as plt
from params import m_dot, Cp, Ac  # Si no los usás acá, podés eliminar esta línea

def plot_irradiance(filename):
    df = pd.read_csv(filename)

    plt.figure(figsize=(10,5))
    plt.plot(df["Hour"], df["IT"], marker='o', linestyle='-', color='orange')
    plt.title("Irradiancia horaria (MJ/m²·h) vs Hora del día")
    plt.xlabel("Hora del día")
    plt.ylabel("Irradiancia IT (MJ/m²·h)")
    plt.grid(True)
    plt.xticks(range(int(df["Hour"].min()), int(df["Hour"].max())+1))
    plt.show()

def plot_temperatures():
    df_data = pd.read_csv("solar_data.csv")
    df_results = pd.read_csv("results.csv")

    Ti = df_results["Ti"]   # Directo de results.csv
    To = df_results["To [°C]"]   # Directo de results.csv
    hours = df_results["Hour"].astype(int)

    plt.figure(figsize=(8, 4))
    plt.plot(hours, Ti, marker='o', linestyle='-', label='Inlet Temperature Ti (°C)', color='blue')
    plt.plot(hours, To, marker='x', linestyle='--', label='Outlet Temperature To (°C)', color='red')

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
    plot_irradiance("solar_data.csv")
