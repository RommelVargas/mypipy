# analysis_app/data_tables.py (CÓDIGO COMPLETO FINAL Y CORREGIDO)
from typing import Dict, Any

# -------------------------------------------------------------
# 1. TABLA ÚNICA DE DIÁMETROS INTERNOS (D) EN METROS [m]
# Se eliminan las tablas duplicadas (PIPE_DIAMETERS_IN_M y PIPE_DIAMETERS_DN_M)
# -------------------------------------------------------------

PIPE_DIAMETERS_M: Dict[tuple, float] = {
    (0.125, 40): 0.0068,  # 1/8"
    (0.25, 40): 0.0092,   # 1/4"
    (0.375, 40): 0.0125,  # 3/8"
    (0.5, 40): 0.0158,    # 1/2"
    (0.75, 40): 0.0209,   # 3/4"
    (1, 40): 0.0266,      # 1"
    (1.25, 40): 0.0351,   # 1 1/4"
    (1.5, 40): 0.0409,    # 1 1/2"
    (2, 40): 0.0525,      # 2"
    (2.5, 40): 0.0627,    # 2 1/2"
    (3, 40): 0.0779,      # 3"
    (3.5, 40): 0.0901,    # 3 1/2"
    (4, 40): 0.1023,      # 4"
    (5, 40): 0.128,       # 5"
    (6, 40): 0.154,       # 6"
    (8, 40): 0.203,       # 8"
    (10, 40): 0.255,      # 10"
    (12, 40): 0.303,      # 12"
    (14, 40): 0.333,      # 14"
    (16, 40): 0.381,      # 16"
    (18, 40): 0.429,      # 18"
    (20, 40): 0.478,      # 20"
    (24, 40): 0.575,      # 24"
}

# -------------------------------------------------------------
# 2. RUGOSIDADES (ε) EN METROS (Claves en MINÚSCULAS)
# -------------------------------------------------------------
ROUGHNESS: Dict[str, float] = {
    "plástico (pe, pvc)": 1.5e-6,
    "poliester reforzado con fibra de vidrio": 1.0e-5,
    "tubos estirados de acero": 2.4e-6,
    "tubos de latón o cobre": 1.5e-6,
    "fundición revestida de cemento": 2.4e-6,
    "fundición con revestimiento bituminoso": 2.4e-6,
    "fundición centrifugada": 3.0e-6,
    "acero comercial y soldado": 6.0e-5,  # <-- CLAVE DE FALLBACK
    "fundición asfaltada": 1.2e-4,
    "fundición": 3.6e-4,
    "hierro forjado": 6.0e-5,
    "hierro galvanizado": 1.5e-4,
    "madera": 5.4e-4,
    "hormigón": 1.65e-3, # Dejamos la tilde en el valor si está en el Forms
}

# -------------------------------------------------------------
# 3. COEFICIENTES DE PÉRDIDA MENOR (K) (Claves en MINÚSCULAS)
# -------------------------------------------------------------
MINOR_LOSS_COEFFICIENTS: Dict[str, float] = {
    "Rejilla de Entrada": 0.80,
    "Válvula de Pie": 3.00,
    "Entrada Cuadrada": 0.50,
    "Entrada Abocinada": 0.10,
    "Entrada de Borda o Reentrada": 1.00,
    "Ampliación Gradual": 0.30,
    "Ampliación Brusca": 0.20,
    "Reducción Gradual": 0.25,
    "Reducción Brusca": 0.35,
    "Codo Corto 90°": 0.90,
    "Codo Corto 45°": 0.40,
    "Codo Largo 90°": 0.40,
    "Codo Largo 45°": 0.20,
    "Codo Largo 22°30'": 0.10,
    "Tee Flujo Recto": 0.10,
    "Tee Flujo en Ángulo": 1.50,
    "Tee Salida Bilateral": 1.80,
    "Válvula de Compuerta Abierta": 5.00,
    "Válvula de Ángulo Abierta": 5.00,
    "Válvula de Globo Abierta": 10.0,
    "Válvula Alfalfera": 2.00,
    "Válvula de Retención": 2.50,
    "Boquilla": 2.75,
    "Controlador de Gasto": 2.50,
    "Medidor Venturi": 2.50,
    "Confluencia": 0.40,
    "Bifurcación": 0.10,
    "Pequeña Derivación": 0.03,
    "Válvula de Mariposa Abierta": 0.24,
}

# -------------------------------------------------------------
# 4. CONSTANTES Y FUNCIONES DE BÚSQUEDA
# -------------------------------------------------------------
CONVERSION_M_TO_FT = 3.28084 # Factor de conversión: 1 metro = 3.28084 pies


def get_pipe_diameter(nominal: float, schedule: int, system: str) -> float:
    """
    Busca el diámetro interno D en la unidad correspondiente (m o ft).
    Aplica la conversión de metros a pies si el sistema es Inglés.
    """
    key = (nominal, schedule)
    
    # 1. Buscar el diámetro en METROS (D_m)
    diameter_m = PIPE_DIAMETERS_M.get(key)
    
    # 2. Si no está en tabla (ej. el usuario ingresó 0.06 o 0.25), usa el valor nominal directamente.
    if diameter_m is None:
        # Asumimos que el nominal introducido es D en la unidad base (m o ft)
        # Convertimos ese input base a metros para tener un D_m inicial
        if system == 'SI':
            diameter_m = nominal
        else:
            # Si el usuario ingresó 0.5 pies, convertimos 0.5 ft a metros:
            diameter_m = nominal / CONVERSION_M_TO_FT 
    
    # 3. Aplicar conversión final: Este es el paso crucial
    if system == 'SI':
        return diameter_m
    else:
        # CONVERSIÓN DE METROS A PIES
        return diameter_m * CONVERSION_M_TO_FT


def get_roughness_by_material(material: str, system: str) -> float:
    """Devuelve la rugosidad e del material en la unidad correspondiente (m o ft)."""
    material_lower = material.lower().strip()
    epsilon_m = ROUGHNESS.get(material_lower, ROUGHNESS["acero comercial y soldado"])
    
    if system == 'SI':
        return epsilon_m
    else:
        return epsilon_m * CONVERSION_M_TO_FT


def get_minor_loss_k(componente: str) -> float:
    """Devuelve el coeficiente K de un accesorio (0.0 si no existe)."""
    return MINOR_LOSS_COEFFICIENTS.get(componente.lower().strip(), 0.0)


def get_accessories_dict():
    """Devuelve el diccionario {Nombre: K_valor} para llenar el selector HTML."""
    return {k.title(): v for k, v in MINOR_LOSS_COEFFICIENTS.items()}