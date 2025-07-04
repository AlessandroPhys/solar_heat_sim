def calculate_UL(Tp, Ta, h_conv, epsilon_plate, epsilon_glass, k_ins, d_ins):
    """
    Estima UL usando valores razonables de convección, radiación y conducción.
    """
    # Constante de Stefan-Boltzmann
    sigma = 5.67e-8  # W/m²K⁴

    Tp_K = Tp + 273.15
    Ta_K = Ta + 273.15
    T_sky = Ta_K - 6  # cielo efectivo (simplificado)

    # Convección desde la placa hacia el vidrio
    h_conv = h_conv  # típicamente entre 5 y 10 W/m²·K

    # Radiación entre placa y cielo vía vidrio
    epsilon_eff = 1 / (1 / epsilon_plate + 1 / epsilon_glass - 1)
    h_rad = epsilon_eff * sigma * ((Tp_K + T_sky) / 2)**3 * (Tp_K - T_sky)

    # Conducción inferior
    h_cond = k_ins / d_ins

    # Pérdidas totales
    UL = h_conv + h_rad + h_cond

    # Limitar UL a valores típicos
    return UL
