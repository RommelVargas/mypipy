# Calculadora de Flujo en Tuberías | MyPipe

## Descripción

**MyPipe** es una aplicación web interactiva desarrollada en **Django** diseñada para la resolución de problemas de **flujo interno en tuberías**. Utiliza la **Ecuación General de la Energía** y el modelo de **Darcy-Weisbach** con la correlación de **Colebrook-White** para determinar las pérdidas por fricción ($f$).

El objetivo es proporcionar una herramienta robusta que maneje la complejidad de los cálculos de ingeniería quimica, permitiendo a los usuarios calcular de forma precisa:

* **Pérdida de Carga** ($H_L$) y **Caída de Presión** ($\Delta P$).
* **Caudal** ($Q$) o **Velocidad** ($V$) de flujo.
* **Potencia de Bombeo** ($\dot{W}$) necesaria.
* Análisis del **Factor de Fricción** ($f$) y Número de Reynolds ($\text{Re}$).
* Manejo de **accesorios dinámicos** y sistemas de unidades **SI/Inglés**.

***

## Tecnologías Utilizadas

| Componente | Tecnología | Propósito |
| :--- | :--- | :--- |
| **Backend/Framework** | Python 3.11.x, Django | Lógica de la aplicación web y gestión de datos. |
| **Cálculos Numéricos** | **NumPy**, **SciPy** | Resolución de ecuaciones implícitas (Colebrook-White) y álgebra. |
| **Servidor de Producción** | Gunicorn | Servidor WSGI para despliegue. |
| **Frontend/Gráficos** | JavaScript (Chart.js) | Interfaz de usuario interactiva y visualización de datos de $H_L$ vs. $V$. |

***

## Instalación y Ejecución Local

Sigue estos pasos para configurar y ejecutar el proyecto en tu máquina local.

### 1. Clonar el Repositorio

```bash
git clone [https://github.com/RommelVargas/mypipy.git](https://github.com/RommelVargas/mypipy.git)
cd mypipe
