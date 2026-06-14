"""
test_motor.py
Prueba el motor de puntos con casos conocidos y muestra una tabla
con lo esperado, lo obtenido y si PASA o FALLA.
"""

from motor_puntos import calcular_puntos


def jugado(gl, gv):
    """Atajo para construir un resultado real ya jugado."""
    return {"gl_real": gl, "gv_real": gv, "jugado": True}


# Cada caso: (descripcion, pronostico, resultado, esperado)
CASOS = [
    ("Pronostico 2-1, real 3-0 (mismo ganador, score distinto)",
     {"gl": 2, "gv": 1}, jugado(3, 0), 2),
    ("Pronostico 2-1, real 2-1 (exacto)",
     {"gl": 2, "gv": 1}, jugado(2, 1), 3),
    ("Pronostico 2-1, real 0-1 (ganador contrario)",
     {"gl": 2, "gv": 1}, jugado(0, 1), 0),
    ("Pronostico 1-1, real 2-2 (empate, score distinto)",
     {"gl": 1, "gv": 1}, jugado(2, 2), 2),
    ("Pronostico 1-1, real 1-1 (empate exacto)",
     {"gl": 1, "gv": 1}, jugado(1, 1), 3),
    ("Pronostico 2-1, real 1-1 (pronostico ganador, fue empate)",
     {"gl": 2, "gv": 1}, jugado(1, 1), 0),
    ("Pronostico 1-1, real 2-0 (pronostico empate, hubo ganador)",
     {"gl": 1, "gv": 1}, jugado(2, 0), 0),
    ("Pronostico vacio, cualquier resultado",
     {"gl": None, "gv": None}, jugado(3, 1), 0),
    ("Partido no jugado (no se evalua)",
     {"gl": 2, "gv": 1}, {"gl_real": None, "gv_real": None, "jugado": False}, None),
]


def fmt(v):
    return "no evalua" if v is None else str(v)


def main():
    print("=" * 92)
    print(f"{'CASO':62} | {'ESPERA':9} | {'DIO':9} | RESULTADO")
    print("-" * 92)
    todos_ok = True
    for desc, pron, real, esperado in CASOS:
        obtenido = calcular_puntos(pron, real)
        ok = obtenido == esperado
        if not ok:
            todos_ok = False
        print(f"{desc:62} | {fmt(esperado):9} | {fmt(obtenido):9} | {'PASA' if ok else 'FALLA <==='}")
    print("=" * 92)
    print("TODAS LAS PRUEBAS PASARON" if todos_ok else "HAY PRUEBAS QUE FALLARON")
    return todos_ok


if __name__ == "__main__":
    main()
