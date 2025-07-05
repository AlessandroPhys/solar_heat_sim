import pandas as pd
import matplotlib.pyplot as plt
from params import m_dot, Cp, Ac

def plot_temperatures():
    df_data = pd.read_csv("solar_data.csv")
    df_results = pd.read_csv("results.csv")

    Ti = df_data["Ti"]
    Qu = df_results["q_u [MJ/m²·h]"] * Ac

    To = Ti + (Qu * 1e6) / (m_dot * Cp * 3600)
    hours = df_results["Hour"].astype(int)

    plt.figure(figsize=(8, 4))
    plt.plot(hours, Ti, marker='o', linestyle='-', label='Inlet Temperature Ti (\u00b0C)', color='blue')
    plt.plot(hours, To, marker='o', linestyle='--', label='Outlet Temperature To (\u00b0C)', color='red')

    plt.title("Inlet and Outlet Water Temperature")
    plt.xlabel("Hour of Day")
    plt.ylabel("Temperature (\u00b0C)")
    plt.xticks(hours)
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    plot_temperatures()
