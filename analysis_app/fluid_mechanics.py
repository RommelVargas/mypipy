# fluid_mechanics.py (CÓDIGO COMPLETO CORREGIDO)
import warnings
import numpy as np
from scipy.optimize import root_scalar

# Constantes de Gravedad
G_SI = 9.81    # m/s^2
G_INGLES = 32.2  # ft/s^2

# --- UTILERÍAS DE UNIDADES Y FÍSICA BÁSICA ---


def get_constants(system: str):
    """Devuelve (g, g_unit, L_unit, Q_unit, P_unit, rho_unit, nu_unit, power_unit)."""
    if system == 'SI':
        # g, g_unit, L_unit, Q_unit, P_unit, rho_unit, nu_unit, W_unit
        return G_SI, 'm/s²', 'm', 'm³/s', 'Pa', 'kg/m³', 'm²/s', 'W'
    else:
        return G_INGLES, 'ft/s²', 'ft', 'ft³/s', 'lbf/ft²', 'slug/ft³', 'ft²/s', 'hp'


def kinematic_viscosity(mu: float, rho: float) -> float:
    """Calcula la viscosidad cinemática (nu = mu / rho). Lanza excepción si rho inválida."""
    if rho <= 0:
        raise ValueError("La densidad (rho) debe ser positiva.")
    return mu / rho


def reynolds_number(V: float, D: float, nu: float) -> float:
    """Calcula el Número de Reynolds (Re). Retorna 0 si entradas no válidas."""
    if V <= 0 or D <= 0 or nu <= 0:
        return 0.0
    return (V * D) / nu


# --- ECUACIONES CLAVE ---


def colebrook_white_friction_factor(Re: float, epsilon_D: float) -> float:
    """
    Resuelve el factor de fricción 'f' mediante la ecuación de Colebrook-White.
    Se usan múltiples estrategias (brentq, secant, newton). Retorna f>0.
    - Re: Reynolds
    - epsilon_D: rugosidad relativa (epsilon / D)
    """
    # Casos simples
    if Re <= 0:
        warnings.warn("Re <= 0 en colebrook_white_friction_factor; devolviendo 0.0")
        return 0.0
    if Re < 2000:
        return 64.0 / Re  # laminar

    def colebrook_equation(f):
        # evitamos sqrt de números <= 0
        if f <= 0:
            return 1e6
        return 1.0 / np.sqrt(f) + 2.0 * np.log10((epsilon_D / 3.7) + (2.51 / (Re * np.sqrt(f))))

    # Estimación empírica inicial (explicit approx)
    try:
        f_guess = 0.25 / (np.log10((epsilon_D / 3.7) + (5.74 / (Re ** 0.9)))) ** 2
    except Exception:
        f_guess = 0.02  # fallback razonable

    # Intentos de resolución (ordenados por robustez)
    # 1) brentq en un intervalo amplio si existe cambio de signo
    bracket_low, bracket_high = 1e-6, 0.1
    try:
        fl = colebrook_equation(bracket_low)
        fh = colebrook_equation(bracket_high)
        if np.sign(fl) != np.sign(fh):
            sol = root_scalar(colebrook_equation, bracket=[bracket_low, bracket_high], method='brentq', maxiter=200)
            if sol.converged and sol.root > 0:
                return float(sol.root)
    except Exception:
        # no interrumpimos; intentaremos otros métodos
        pass

    # 2) secant cerca de f_guess
    try:
        x0 = max(1e-6, f_guess * 0.8)
        x1 = min(0.5, f_guess * 1.2)
        sol = root_scalar(colebrook_equation, x0=x0, x1=x1, method='secant', maxiter=200)
        if sol.converged and sol.root > 0:
            return float(sol.root)
    except Exception:
        pass

    # 3) newton (requiere buena aproximación inicial)
    try:
        sol = root_scalar(colebrook_equation, x0=f_guess, method='newton', maxiter=200)
        if sol.converged and sol.root > 0:
            return float(sol.root)
    except Exception:
        pass

    # 4) fallback: usar aproximación explícita (f_guess)
    warnings.warn("Colebrook no convergió; usando aproximación explícita f_guess.")
    return float(f_guess)


def total_head_loss(f: float, L: float, D: float, V: float, sum_K: float, g: float) -> float:
    """
    Calcula las pérdidas totales de energía (hL) en unidades de longitud (m o ft).
    Hf = f * (L/D) * (V^2 / 2g)
    Hm = sum_K * (V^2 / 2g)
    """
    if D <= 0 or g <= 0:
        return 0.0
    velocity_head = (V ** 2) / (2 * g)
    Hf = f * (L / D) * velocity_head
    Hm = sum_K * velocity_head
    return Hf + Hm


def pressure_drop(rho: float, g: float, hL: float) -> float:
    """
    Calcula la caída de presión (Delta P) a partir de pérdida de carga hL.
    Delta P = rho * g * hL
    """
    return rho * g * hL


def pumping_power(Q: float, delta_P: float, system: str, efficiency: float = 1.0) -> float:
    """
    Calcula la potencia de bombeo necesaria.
    - SI: Q [m^3/s], delta_P [Pa] => resultado en W
    - INGLES: Q [ft^3/s], delta_P [lbf/ft^2] => resultado en hp (1 hp = 550 ft*lbf/s)
    efficiency: fracción (0-1). Se divide la potencia bruta entre la eficiencia.
    """
    if efficiency <= 0:
        raise ValueError("La eficiencia debe ser positiva y mayor que 0.")

    # Potencia bruta en unidades base:
    # SI: m^3/s * Pa = N*m/s = W
    # EN: ft^3/s * lbf/ft^2 = ft*lbf/s
    power_brute = Q * delta_P

    if system == 'SI':
        return power_brute / efficiency
    else:
        # convertir ft*lbf/s a HP
        return (power_brute / 550.0) / efficiency


# --- DESPEJE DE VELOCIDAD (Para resolver V/Q) ---


def energy_equation_for_V(V: float, P1: float, P2: float, z1: float, z2: float,
                          L: float, D: float, rho: float, nu: float, sum_K: float, g: float,
                          material_epsilon: float) -> float:
    """
    Ecuación de energía (balance) puesta en forma F(V) = 0 para despejar V.
    Retorna hL - ( (P1-P2)/(rho*g) + (z1 - z2) ) donde hL depende de V.
    material_epsilon: rugosidad absoluta (m o ft) - se convertirá a epsilon/D internamente.
    """
    if V <= 0:
        # devolver un valor grande para indicar que V no puede ser <= 0
        return 1e10

    Re = reynolds_number(V, D, nu)
    if D == 0:
        return 1e10

    epsilon_D = material_epsilon / D if material_epsilon is not None else 0.0
    f = colebrook_white_friction_factor(Re, epsilon_D)
    hL = total_head_loss(f, L, D, V, sum_K, g)

    # carga disponible en unidades de longitud
    delta_z_p = (P1 - P2) / (rho * g) + (z1 - z2)
    return hL - delta_z_p


def solve_velocity(P1: float, P2: float, z1: float, z2: float,
                   L: float, D: float, rho: float, nu: float, sum_K: float, g: float,
                   material_epsilon: float, V_min: float = 1e-3, V_max: float = 20.0):
    """
    Resuelve la velocidad V y el caudal Q (V * Area) intentando varias estrategias.
    Devuelve (V, Q) o (None, None) si no converge.
    - V_min, V_max: límites para el intento con brentq.
    """
    Area = np.pi * (D ** 2) / 4.0

    # Functor parcial para root_scalar (solo V como variable)
    def F(V):
        return energy_equation_for_V(V, P1, P2, z1, z2, L, D, rho, nu, sum_K, g, material_epsilon)

    # 1) Intentar brentq si hay cambio de signo en [V_min, V_max]
    try:
        f_low = F(V_min)
        f_high = F(V_max)
        if np.sign(f_low) != np.sign(f_high):
            sol = root_scalar(F, bracket=[V_min, V_max], method='brentq', maxiter=200)
            if sol.converged and sol.root > 0:
                V = sol.root
                return V, V * Area
    except Exception:
        pass

    # 2) Intentar secant/newton con guesses alrededor de una estimación
    try:
        # Estimación rudimentaria: asumir que hL ~ delta_z_p => V_est = sqrt(2*g*delta_z_p) (si delta_z_p>0)
        try:
            delta_z_p = (P1 - P2) / (rho * g) + (z1 - z2)
            if delta_z_p > 0:
                V_est = np.sqrt(2 * g * delta_z_p)
            else:
                V_est = (V_min + V_max) / 2.0
        except Exception:
            V_est = (V_min + V_max) / 2.0

        x0 = max(V_min, V_est * 0.5)
        x1 = min(V_max, V_est * 1.5)
        sol = root_scalar(F, x0=x0, x1=x1, method='secant', maxiter=200)
        if sol.converged and sol.root > 0:
            V = sol.root
            return V, V * Area
    except Exception:
        pass

    # 3) Intentar newton con una sola semilla
    try:
        sol = root_scalar(F, x0=(V_min + V_max) / 2.0, method='newton', maxiter=200)
        if sol.converged and sol.root > 0:
            V = sol.root
            return V, V * Area
    except Exception:
        pass

    warnings.warn("No se pudo resolver la velocidad con las estrategias disponibles.")
    return None, None


# --- GENERADOR DE DATOS PARA GRÁFICA ---


def generate_hl_vs_v_data(V_min: float, V_max: float, steps: int,
                          L: float, D: float, nu: float, sum_K: float, g: float,
                          material_epsilon: float):
    """
    Genera lista de tuplas (V, hL) para graficar la pérdida total en función de la velocidad.
    """
    if steps <= 0:
        raise ValueError("steps debe ser un entero positivo.")

    V_values = np.linspace(V_min, V_max, steps)
    data = []

    for V in V_values:
        if V <= 0:
            continue
        Re = reynolds_number(V, D, nu)
        epsilon_D = material_epsilon / D if D != 0 else 0.0
        f = colebrook_white_friction_factor(Re, epsilon_D)
        hL = total_head_loss(f, L, D, V, sum_K, g)
        data.append((V, hL))

    return data
