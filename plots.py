import pandas as pd
import matplotlib.pyplot as plt

def plot_combined(filename, start_hour=0, end_hour=24):
    df_data = pd.read_csv("solar_data.csv")
    df_results = pd.read_csv("results.csv")
    df_data = df_data[(df_data["Minute"] >= start_hour * 60) & (df_data["Minute"] < end_hour * 60)].reset_index(drop=True)
    df_results = df_results[(df_results["Minute"] >= start_hour * 60) & (df_results["Minute"] < end_hour * 60)].reset_index(drop=True)
    df_irr = pd.read_csv(filename)
    df_irr = df_irr[(df_irr["Minute"] >= start_hour * 60) & (df_irr["Minute"] < end_hour * 60)].reset_index(drop=True)

    hours_data = df_results["Minute"] / 60

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)

    # Gráfico de temperaturas (solo líneas)
    ax1.plot(hours_data, df_results["Ti"], linestyle='-', label='Inlet Temperature Ti (°C)', color='blue')
    ax1.plot(hours_data, df_results["To [°C]"], linestyle='--', label='Outlet Temperature To (°C)', color='red')
    ax1.plot(hours_data, df_data["Ta"], linestyle=':', label='Ambient Temperature Ta (°C)', color='green')
    ax1.set_ylabel("Temperatura (°C)")
    ax1.set_title(f"Temperaturas entre {start_hour} y {end_hour} horas")
    ax1.legend()
    ax1.grid(True)

    # Gráfico de irradiancia (solo línea)
    ax2.plot(df_irr["Minute"] / 60, df_irr["IT"], linestyle='-', color='orange')
    ax2.set_xlabel("Hora del día")
    ax2.set_ylabel("Irradiancia IT (MJ/m²·h)")
    ax2.set_title(f"Irradiancia (MJ/m²·h) entre {start_hour} y {end_hour} horas")
    ax2.grid(True)
    ax2.set_xticks(range(start_hour, end_hour + 1))

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    plot_combined("solar_data.csv", start_hour=0, end_hour=24)
