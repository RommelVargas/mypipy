# analysis_app/views.py (CÓDIGO COMPLETO FINAL Y CONSOLIDADO)

import numpy as np
import json
from django.shortcuts import render
from .forms import FluidInputForm 
from .fluid_mechanics import (
    colebrook_white_friction_factor, total_head_loss, reynolds_number, 
    generate_hl_vs_v_data, solve_velocity, get_constants, 
    kinematic_viscosity, pressure_drop, pumping_power
)
from .data_tables import (
    get_pipe_diameter, get_roughness_by_material, get_minor_loss_k, 
    get_accessories_dict
)

def calculate_fluid_flow(request):
    """
    Gestiona la entrada del formulario, realiza los cálculos de mecánica de fluidos
    y genera los datos para la gráfica HL vs V.
    """
    results = None
    chart_data_struct = {}
    units = {}
    
    # INICIALIZACIÓN CRÍTICA: Asegura que V y Q siempre tengan un valor (0.0)
    V = 0.0
    Q = 0.0
    
    form = FluidInputForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        try:
            # --- 1. EXTRACCIÓN DE DATOS Y CONSTANTES ---
            data = form.cleaned_data
            
            # Obtener constantes y unidades
            system = data['system']
            g, g_unit, L_unit, Q_unit, P_unit, rho_unit, nu_unit_name, W_unit = get_constants(system)
            units = {'length': L_unit, 'velocity': f"{L_unit}/s", 'pressure': P_unit, 'power': W_unit, 'caudal': Q_unit}
            
            # Datos principales
            rho = data['rho']; mu = data['mu']; L = data['length']; nominal = data['nominal']; schedule = data['schedule']
            material = data['material']; solve_for = data['variable_to_solve']; input_type = data['input_type']
            pump_efficiency = data['pump_efficiency']
            P1, P2 = data['P1'] or 0, data['P2'] or 0; z1, z2 = data['z1'] or 0, data['z2'] or 0
            
            nu = kinematic_viscosity(mu, rho)
            
            # 2. PROCESAMIENTO DE ACCESORIOS (JSON del HTML)
            accessories_json_str = request.POST.get('accessories_json', '{}')
            accessories_dict = json.loads(accessories_json_str)

            sum_K = 0
            for component_name, count in accessories_dict.items():
                sum_K += get_minor_loss_k(component_name.lower()) * count # Multiplicamos por la cantidad
            
            # 3. CÁLCULOS GEOMÉTRICOS Y FÍSICOS
            D = get_pipe_diameter(nominal, schedule, system); Area = np.pi * (D**2) / 4
            if Area <= 0: raise ValueError("El diámetro interno es cero o negativo.")
            epsilon = get_roughness_by_material(material, system)
            
            # 4. DETERMINAR V y Q DE ENTRADA
            # Aquí V y Q se reasignan a los valores del formulario
            if input_type == 'V':
                V = data['velocity'] or 0.0
                Q = V * Area
            else:
                Q = data['caudal'] or 0.0
                V = Q / Area if Area > 0 else 0.0

            # 5. DESPACHO DE CÁLCULO
            if solve_for == 'V':
                V_solved, Q_solved = solve_velocity(P1, P2, z1, z2, L, D, rho, nu, sum_K, g, epsilon)
                
                if V_solved is not None:
                    V, Q = V_solved, Q_solved # Usamos valores resueltos
                    
                    Re = reynolds_number(V, D, nu); epsilon_D = epsilon / D
                    f = colebrook_white_friction_factor(Re, epsilon_D); hL = total_head_loss(f, L, D, V, sum_K, g)
                    delta_P = pressure_drop(rho, g, hL); power = pumping_power(Q, delta_P, system, pump_efficiency)
                    
                    results = {
                        'variable_solved': f'Velocidad y Caudal (Resuelto)', 'V': f"{V:.3f} {units['velocity']}", 'Q': f"{Q:.4f} {units['caudal']}",
                        'HL': f"{hL:.2f} {units['length']}", 'dP': f"{delta_P:.2f} {units['pressure']}",
                        'Power': f"{power:.2f} {units['power']}", 'f': f"{f:.4f}", 'Re': f"{Re:.0f}",
                    }
                else:
                    results = {'error': 'El cálculo de V/Q no convergió. Revise si la energía disponible es suficiente.'}
                    
            else: # HL_DP_POWER (Cálculo con V o Q de entrada)
                Re = reynolds_number(V, D, nu); epsilon_D = epsilon / D
                f = colebrook_white_friction_factor(Re, epsilon_D); hL = total_head_loss(f, L, D, V, sum_K, g)
                delta_P = pressure_drop(rho, g, hL); power = pumping_power(Q, delta_P, system, pump_efficiency)
                
                results = {
                    'variable_solved': 'Pérdida de Carga, Presión y Potencia', 'V': f"{V:.3f} {units['velocity']}", 'Q': f"{Q:.4f} {units['caudal']}",
                    'HL': f"{hL:.2f} {units['length']}", 'dP': f"{delta_P:.2f} {units['pressure']}",
                    'Power': f"{power:.2f} {units['power']}", 'f': f"{f:.4f}", 'Re': f"{Re:.0f}",
                }
            
            # 6. GENERAR DATOS PARA LA GRÁFICA
            # V y Q siempre tienen un valor aquí, ya sea del input o resuelto.
            V_min, V_max, steps = (0.5, 5.0, 20) if system == 'SI' else (1.0, 15.0, 20)
            chart_raw_data = generate_hl_vs_v_data(V_min, V_max, steps, L, D, nu, sum_K, g, epsilon)
            
            chart_data_struct = {
                'labels': [f"{v:.2f}" for v, hl in chart_raw_data],
                'values': [f"{hl:.3f}" for v, hl in chart_raw_data],
            }
            
        except ValueError as e:
            results = {'error': f"Error en la entrada de datos: {e}"}
        except Exception as e:
            # Este bloque ahora es seguro gracias a la inicialización de V y Q
            results = {'error': f"Error interno inesperado: {e}. Revise los logs del servidor para más detalles."}

    context = {
        'form': form,
        'results': results,
        'units': units,
        'chart': chart_data_struct, 
        'accessories': get_accessories_dict(), 
    }
    return render(request, 'analysis_app/calculator.html', context)