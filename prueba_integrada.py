"""
prueba_integrada.py
Prueba el motor de punta a punta con los 25 jugadores reales.

Inventa resultados FALSOS para los juegos 1 a 6 SOLO EN MEMORIA
(nunca se escriben en partidos.json) y muestra un mini-leaderboard.
Al final verifica que partidos.json sigue limpio.
"""

import json
import os

from motor_puntos import generar_leaderboard

CARPETA = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(CARPETA, "data")


def cargar(nombre):
    with open(os.path.join(DATA, nombre), "r", encoding="utf-8") as fp:
        return json.load(fp)


# Resultados de mentira SOLO para esta prueba (juego -> (local, visitante)).
RESULTADOS_FALSOS = {
    1: (2, 0),   # Mexico vs Sudafrica
    2: (1, 1),   # Corea del Sur vs Republica Checa (empate)
    3: (0, 2),   # Canada vs Bosnia
    4: (3, 1),   # Estados Unidos vs Paraguay
    5: (1, 1),   # Catar vs Suiza (empate)
    6: (2, 1),   # Brasil vs Marruecos
}


def main():
    jugadores = cargar("jugadores.json")
    pronosticos = cargar("pronosticos.json")
    partidos = cargar("partidos.json")  # copia en memoria

    # Inyectar los resultados falsos SOLO en esta copia en memoria.
    for partido in partidos:
        falso = RESULTADOS_FALSOS.get(partido["juego"])
        if falso is not None:
            partido["gl_real"], partido["gv_real"] = falso
            partido["jugado"] = True

    tabla = generar_leaderboard(jugadores, pronosticos, partidos)

    lineas = []
    lineas.append("MINI-LEADERBOARD DE PRUEBA (juegos 1-6 con resultados inventados)")
    lineas.append("=" * 70)
    lineas.append(f"{'#':>2}  {'JUGADOR':30} {'PUNTOS':>7} {'EXACTOS':>8} {'JUGADOS':>8}")
    lineas.append("-" * 70)
    for fila in tabla[:10]:
        lineas.append(f"{fila['puesto']:>2}  {fila['nombre']:30} "
                      f"{fila['puntos']:>7} {fila['exactos']:>8} {fila['evaluados']:>8}")
    lineas.append("=" * 70)
    texto = "\n".join(lineas)

    # Escribir a un archivo UTF-8 para que los acentos se vean bien.
    salida = os.path.join(CARPETA, "_prueba_leaderboard.txt")
    with open(salida, "w", encoding="utf-8") as fp:
        fp.write(texto + "\n")

    # Verificar que partidos.json en disco sigue intacto (todo en None / no jugado).
    en_disco = cargar("partidos.json")
    sucios = [p["juego"] for p in en_disco
              if p["gl_real"] is not None or p["gv_real"] is not None or p["jugado"]]
    print(texto)
    print()
    if sucios:
        print("ATENCION: partidos.json quedo con datos en los juegos:", sucios)
    else:
        print("OK: partidos.json sigue LIMPIO (todos los resultados vacios, jugado=false).")


if __name__ == "__main__":
    main()
