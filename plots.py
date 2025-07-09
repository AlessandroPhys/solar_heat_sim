import pandas as pd
import matplotlib.pyplot as plt
from params import dia, mes, interval_min

def plot_combined(filename, start_hour=0, end_hour=24):
    
    plt.style.use("grayscale")  # Activar estilo antes de crear la figura

    df_data = pd.read_csv("solar_data.csv")
    df_results = pd.read_csv("results.csv")
    df_tempa = pd.read_csv("temperature_interpolated.csv")
    df_data = df_data[(df_data["Minute"] >= start_hour * 60) & (df_data["Minute"] < end_hour * 60)].reset_index(drop=True)
    df_results = df_results[(df_results["Minute"] >= start_hour * 60) & (df_results["Minute"] < end_hour * 60)].reset_index(drop=True)
    df_irr = pd.read_csv(filename)
    df_irr = df_irr[(df_irr["Minute"] >= start_hour * 60) & (df_irr["Minute"] < end_hour * 60)].reset_index(drop=True)

    hours_data = df_results["Minute"] / 60

    fig, axs = plt.subplots(2, 2, figsize=(14, 10), sharex=True)
    fig.suptitle(f"Análisis del calefón solar - {dia:02d}/{mes:02d}/24", fontsize=18, fontweight="bold")

    # --- Estilos comunes ---
    for ax in axs.flat:
        ax.grid(True, linestyle="--", alpha=0.4)
        ax.tick_params(axis='both', labelsize=10)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

    # --- Temperaturas (izquierda arriba) ---
    axs[0, 0].plot(hours_data, df_results["Ti"], linestyle='-', label='Inlet Temperature Ti (°C)', color='blue')
    axs[0, 0].plot(hours_data, df_results["To [°C]"], linestyle='--', label='Outlet Temperature To (°C)', color='red')
    axs[0, 0].plot(hours_data, df_tempa["temp"], linestyle=':', label='Ambient Temperature Ta (°C)', color='green')
    axs[0, 0].plot(hours_data, df_results["T_cons [°C]"], linestyle='-.', label='T for consumer (°C)', color='purple')
    axs[0, 0].plot(hours_data, df_results["Tp [°C]"], linestyle='-.', label='Tp (°C)', color='orange')

    axs[0, 0].set_ylabel("Temperatura (°C)", fontsize=11)
    axs[0, 0].set_title(f"Temperaturas entre {start_hour} y {end_hour} horas", fontsize=13, fontweight="bold")
    axs[0, 0].legend(fontsize=9, loc='upper left', frameon=False)

    # --- Irradiancia (derecha arriba) ---
    axs[0, 1].plot(df_irr["Minute"] / 60, df_irr["IT"] * 1e6 / (60 * interval_min), color='darkorange', linewidth=2)
    axs[0, 1].set_ylabel(f"Irradiancia IT (W/m²)", fontsize=11)
    axs[0, 1].set_title("Irradiancia solar entre 0 y 24 horas", fontsize=13, fontweight="bold")

    # --- Energías (izquierda abajo) ---
    axs[1, 0].plot(hours_data, df_results["q_u [MJ]"] * 1e6 / (interval_min * 60) , label='Qu útil', color='#1f77b4', linewidth=2)
    axs[1, 0].plot(hours_data, df_results["Loss Total [MJ]"] * 1e6 / (interval_min * 60) , label='Pérdidas', color='#d62728', linewidth=2)
    axs[1, 0].plot(hours_data, df_results["e_disp [MJ]"] * 1e6 / (interval_min * 60), label='Energía disponible', color='black', linewidth=2)
    axs[1, 0].set_xlabel("Hora del día", fontsize=11)
    axs[1, 0].set_ylabel(f"Energía por unidad de tiempo [W]", fontsize=11)
    axs[1, 0].set_title("Energía útil, pérdidas y radiación absorbida por unidad de tiempo", fontsize=13, fontweight="bold")
    axs[1, 0].legend(fontsize=9, frameon=False)
    axs[1, 0].set_xticks(range(start_hour, end_hour + 1))

    # --- Eficiencia (derecha abajo) ---
    axs[1, 1].plot(hours_data, df_results["Efficiency η"], color='forestgreen', linewidth=2)
    axs[1, 1].set_xlabel("Hora del día", fontsize=11)
    axs[1, 1].set_ylabel("Eficiencia Instantánea η", fontsize=11)
    axs[1, 1].set_title("Eficiencia instantánea del colector", fontsize=13, fontweight="bold")
    axs[1, 1].set_xticks(range(start_hour, end_hour + 1))

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.show()

if __name__ == "__main__":
    plot_combined("solar_data.csv", start_hour=0, end_hour=24)
