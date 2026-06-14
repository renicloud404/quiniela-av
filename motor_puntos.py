"""
motor_puntos.py
El "cerebro" de la quiniela: calcula cuantos puntos saca un jugador.

Reglas:
  - Acerta el lado del resultado (gana local / gana visitante / empate): 2 puntos
  - Si ademas el marcador es EXACTO: +1 punto (total 3)
  - Si no acerta el lado: 0 puntos
  - Pronostico vacio: 0 puntos
  - Partido no jugado: no se evalua (devuelve None)

Estas funciones NO leen archivos: reciben los datos ya cargados.
Asi son faciles de probar y de reutilizar en la app de Streamlit.
"""


def _lado(goles_local, goles_visitante):
    """Devuelve quien gana segun un marcador:
       1  = gana el local
       0  = empate
      -1  = gana el visitante
    """
    if goles_local > goles_visitante:
        return 1
    if goles_local < goles_visitante:
        return -1
    return 0


def calcular_puntos(pronostico, resultado):
    """Calcula los puntos de UN pronostico contra UN resultado real.

    pronostico: dict con 'gl' y 'gv' (goles pronosticados local / visitante).
                Pueden ser None si el jugador dejo la casilla vacia.
    resultado:  dict con 'gl_real', 'gv_real' y 'jugado' (True/False).

    Devuelve:
        None  -> el partido no se ha jugado (o no tiene marcador): NO se evalua
        0, 2 o 3 (int) -> los puntos obtenidos
    """
    # 1) Si el partido no se jugo, no se evalua.
    if not resultado.get("jugado"):
        return None
    real_local = resultado.get("gl_real")
    real_visitante = resultado.get("gv_real")
    # Marcado como jugado pero sin marcador cargado: tampoco se evalua todavia.
    if real_local is None or real_visitante is None:
        return None

    # 2) Pronostico vacio (caso Leonardo J17 / Dian J45): 0 puntos.
    pron_local = pronostico.get("gl")
    pron_visitante = pronostico.get("gv")
    if pron_local is None or pron_visitante is None:
        return 0

    # 3) Comparar el "lado" (ganador o empate).
    if _lado(pron_local, pron_visitante) != _lado(real_local, real_visitante):
        return 0  # acerto a otro ganador, o empate vs no-empate

    # 4) Acerto el lado: 2 puntos base.
    puntos = 2
    # 5) Si ademas el marcador es identico: +1 (total 3).
    if pron_local == real_local and pron_visitante == real_visitante:
        puntos += 1
    return puntos


def calcular_totales(pronosticos, partidos):
    """Suma los puntos de TODOS los jugadores sobre los partidos ya jugados.

    pronosticos: dict { id_jugador: [ {'juego':n, 'gl':.., 'gv':..}, ... 72 ] }
    partidos:    lista de dicts { 'juego':n, 'gl_real':.., 'gv_real':.., 'jugado':bool }

    Devuelve: dict { id_jugador: {'puntos': int, 'exactos': int, 'evaluados': int} }
        puntos    = total acumulado
        exactos   = cuantos marcadores EXACTOS acerto (desempate del leaderboard)
        evaluados = cuantos partidos jugados se le contaron
    """
    # Indexar partidos por numero de juego para buscarlos rapido.
    partido_por_juego = {p["juego"]: p for p in partidos}

    totales = {}
    for id_jugador, lista_pron in pronosticos.items():
        puntos = 0
        exactos = 0
        evaluados = 0
        for pron in lista_pron:
            partido = partido_por_juego.get(pron["juego"])
            if partido is None:
                continue
            p = calcular_puntos(pron, partido)
            if p is None:
                continue  # no jugado: no se cuenta
            puntos += p
            evaluados += 1
            if p == 3:
                exactos += 1
        totales[id_jugador] = {
            "puntos": puntos,
            "exactos": exactos,
            "evaluados": evaluados,
        }
    return totales


def generar_leaderboard(jugadores, pronosticos, partidos):
    """Arma la tabla de posiciones ya ordenada.

    Orden: mas puntos primero; si hay empate, mas marcadores exactos.
    Devuelve una lista de dicts lista para mostrar:
        { 'puesto', 'id', 'nombre', 'puntos', 'exactos', 'evaluados' }
    """
    totales = calcular_totales(pronosticos, partidos)
    nombre_por_id = {j["id"]: j["nombre"] for j in jugadores}

    filas = []
    for id_jugador, t in totales.items():
        filas.append({
            "id": id_jugador,
            "nombre": nombre_por_id.get(id_jugador, id_jugador),
            "puntos": t["puntos"],
            "exactos": t["exactos"],
            "evaluados": t["evaluados"],
        })

    # Ordenar: puntos desc, luego exactos desc, luego nombre para que sea estable.
    filas.sort(key=lambda f: (-f["puntos"], -f["exactos"], f["nombre"]))

    # Asignar puesto. Empate TOTAL (mismos puntos Y exactos) comparte puesto.
    # Ej: dos en el puesto 1 -> el siguiente queda en el 3 (ranking deportivo).
    puesto = 0
    clave_anterior = None
    for i, fila in enumerate(filas, start=1):
        clave = (fila["puntos"], fila["exactos"])
        if clave != clave_anterior:
            puesto = i
            clave_anterior = clave
        fila["puesto"] = puesto
    return filas
