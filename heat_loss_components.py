# heat_loss_components.py

def calculate_heat_loss_components(Tp, Ta, params):
    """
    Calcula los componentes individuales de la pérdida de calor:
    - Convección desde la cubierta superior
    - Radiación desde la cubierta superior
    - Conducción en la parte inferior

    Parámetros:
    Tp : temperatura de la placa [°C]
    Ta : temperatura ambiente [°C]
    params : diccionario con propiedades del colector

    Devuelve:
    U_top, U_bottom, U_total [W/m²·K]
    """
    sigma = 5.67e-8  # constante de Stefan-Boltzmann [W/m^2 K^4]

    Tp_K = Tp + 273.15
    Ta_K = Ta + 273.15

    # Convección desde cubierta superior (puede ser forzada o natural)
    h_conv = params["h_conv"]

    # Radiación desde la cubierta superior al cielo
    epsilon_p = params["epsilon_plate"]
    epsilon_g = params["epsilon_glass"]
    T_sky = Ta_K - 6  # cielo efectivo estimado [K]

    h_rad = sigma * ((Tp_K + T_sky) / 2)**3 * (Tp_K - T_sky) * (
        1 / epsilon_p + 1 / epsilon_g - 1)

    # Conducción inferior
    k_ins = params["k_ins"]
    d_ins = params["d_ins"]
    h_cond = k_ins / d_ins

    U_top = h_conv + h_rad
    U_bottom = h_cond
    U_total = U_top + U_bottom

    return U_top, U_bottom, U_total


# Diccionario de parámetros del colector
loss_params = {
    "h_conv": 5.0,             # convección natural [W/m²·K]
    "epsilon_plate": 0.95,     # emisividad de la placa
    "epsilon_glass": 0.88,     # emisividad del vidrio
    "k_ins": 0.045,            # conductividad del aislante [W/m·K]
    "d_ins": 0.05              # espesor del aislante [m]
}
