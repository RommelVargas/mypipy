from django import forms
from .data_tables import ROUGHNESS

# Generar opciones de rugosidad
ROUGHNESS_CHOICES = [(k, k.replace('_', ' ').title()) for k in ROUGHNESS.keys()]


class FluidInputForm(forms.Form):
    # 1. SISTEMA DE UNIDADES Y CÁLCULO
    system = forms.ChoiceField(
        label='Sistema de Unidades',
        choices=[
            ('SI', 'Sistema Internacional (m, kg, s)'),
            ('INGLES', 'Sistema Inglés (ft, lb, s)'),
        ]
    )

    variable_to_solve = forms.ChoiceField(
        label='¿Qué desea calcular?',
        choices=[
            ('HL_DP_POWER', 'Pérdida de Carga, Caída de Presión y Potencia'),
            ('V', 'Velocidad/Caudal (V/Q) - Requiere Δz y ΔP'),
        ]
    )

    # 2. DATOS DEL FLUIDO
    rho = forms.FloatField(
        label='Densidad (ρ)',
        min_value=0.01,
        required=True,
        help_text='SI: kg/m³ | Inglés: slug/ft³ (lbm/ft³ ÷ 32.2)'
    )
    mu = forms.FloatField(
        label='Viscosidad Dinámica (μ)',
        min_value=0.0,
        required=True,
        help_text='SI: kg/m·s | Inglés: lb·s/ft² (Ejemplo: agua ≈ 2.37e-5)'
    )

    # 3. DATOS DE FLUJO
    input_type = forms.ChoiceField(
        label='Variable de Entrada Conocida',
        choices=[
            ('V', 'Velocidad (V)'),
            ('Q', 'Caudal (Q)'),
        ]
    )
    velocity = forms.FloatField(
        label='Velocidad (V)',
        min_value=0.0,
        required=False,
        help_text='Debe ingresarse si la variable seleccionada es Velocidad.'
    )
    caudal = forms.FloatField(
        label='Caudal (Q)',
        min_value=0.0,
        required=False,
        help_text='Debe ingresarse si la variable seleccionada es Caudal.'
    )

    # 4. DATOS DE LA TUBERÍA
    length = forms.FloatField(
        label='Longitud de la Tubería (L)',
        min_value=0.01,
        required=True,
        help_text='Longitud total del tramo en metros o pies.'
    )
    nominal = forms.FloatField(
        label='Diámetro Nominal (DN o in)',
        min_value=0.001,
        required=True,
        help_text='Ingresar en la unidad base (m o ft) o en pulgadas.'
    )
    schedule = forms.IntegerField(
        label='Cédula (SCH)',
        min_value=10,
        required=True,
        help_text='Ejemplo: SCH 40, SCH 80, etc.'
    )
    material = forms.ChoiceField(
        label='Material de la Tubería',
        choices=ROUGHNESS_CHOICES
    )

    # 5. ACCESORIOS Y EFICIENCIA
    pump_efficiency = forms.FloatField(
        label='Eficiencia de Bombeo (η)',
        min_value=0.01,
        max_value=1.0,
        required=True,
        help_text='Eficiencia fraccional de la bomba (Ej: 0.75 para 75%).'
    )

    # 6. PARÁMETROS DE LA ECUACIÓN DE ENERGÍA
    P1 = forms.FloatField(label='Presión 1 (P₁)', required=False)
    P2 = forms.FloatField(label='Presión 2 (P₂)', required=False)
    z1 = forms.FloatField(label='Altura 1 (z₁)', required=False)
    z2 = forms.FloatField(label='Altura 2 (z₂)', required=False)

    # --- VALIDACIÓN PERSONALIZADA ---
    def clean(self):
        cleaned_data = super().clean()
        input_type = cleaned_data.get('input_type')
        velocity = cleaned_data.get('velocity')
        caudal = cleaned_data.get('caudal')

        # Validar entrada según tipo
        if input_type == 'V' and (velocity is None or velocity <= 0):
            self.add_error(
                'velocity',
                'Debe ingresar una Velocidad (V) positiva cuando selecciona esta opción.'
            )

        if input_type == 'Q' and (caudal is None or caudal <= 0):
            self.add_error(
                'caudal',
                'Debe ingresar un Caudal (Q) positivo cuando selecciona esta opción.'
            )

        return cleaned_data
