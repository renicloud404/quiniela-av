"""
actualizar_resultados.py
Trae los marcadores reales del Mundial 2026 desde football-data.org y los
escribe en data/partidos.json. La app (app.py) luego solo los lee.

Es SEGURO correrlo muchas veces: solo reescribe los mismos valores, no duplica.

Uso:
  python actualizar_resultados.py             -> actualiza data/partidos.json
  python actualizar_resultados.py --dry-run   -> vista previa, NO escribe nada

Respaldo manual: si editas data/resultados_manual.json, esos valores se aplican
AL FINAL y MANDAN sobre la API (por si la API falla o se equivoca). Formato:
  { "19": [2, 1], "45": [0, 0] }   (juego 19 = 2-1, juego 45 = 0-0)

El emparejamiento equipo espanol<->API se hace por codigo (TLA) O por nombre en
ingles: con que coincida cualquiera de los dos, basta (mas robusto).
"""

import json
import os
import sys
import unicodedata
import urllib.error
import urllib.request
from pathlib import Path

from motor_puntos import generar_leaderboard

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:
    tomllib = None

BASE = Path(__file__).parent
DATA = BASE / "data"
PARTIDOS = DATA / "partidos.json"
MANUAL = DATA / "resultados_manual.json"
RANKING_PREV = DATA / "ranking_anterior.json"
SECRETS = BASE / ".streamlit" / "secrets.toml"
API_URL = "https://api.football-data.org/v4/competitions/WC/matches"

# Equivalencias: nombre en espanol -> (codigo TLA, nombre en ingles) de la API
EQUIPOS = {
    "Alemania": ("GER", "Germany"), "Arabia Saudita": ("KSA", "Saudi Arabia"),
    "Argelia": ("ALG", "Algeria"), "Argentina": ("ARG", "Argentina"),
    "Australia": ("AUS", "Australia"), "Austria": ("AUT", "Austria"),
    "Bosnia y Herzegovina": ("BIH", "Bosnia-Herzegovina"), "Brasil": ("BRA", "Brazil"),
    "Bélgica": ("BEL", "Belgium"), "Cabo Verde": ("CPV", "Cape Verde Islands"),
    "Canadá": ("CAN", "Canada"), "Catar": ("QAT", "Qatar"),
    "Colombia": ("COL", "Colombia"), "Corea del Sur": ("KOR", "South Korea"),
    "Costa de Marfil": ("CIV", "Ivory Coast"), "Croacia": ("CRO", "Croatia"),
    "Curazao": ("CUW", "Curaçao"), "Ecuador": ("ECU", "Ecuador"),
    "Egipto": ("EGY", "Egypt"), "Escocia": ("SCO", "Scotland"),
    "España": ("ESP", "Spain"), "Estados Unidos": ("USA", "United States"),
    "Francia": ("FRA", "France"), "Ghana": ("GHA", "Ghana"),
    "Haití": ("HAI", "Haiti"), "Inglaterra": ("ENG", "England"),
    "Irak": ("IRQ", "Iraq"), "Irán": ("IRN", "Iran"),
    "Japón": ("JPN", "Japan"), "Jordania": ("JOR", "Jordan"),
    "Marruecos": ("MAR", "Morocco"), "México": ("MEX", "Mexico"),
    "Noruega": ("NOR", "Norway"), "Nueva Zelanda": ("NZL", "New Zealand"),
    "Panamá": ("PAN", "Panama"), "Paraguay": ("PAR", "Paraguay"),
    "Países Bajos": ("NED", "Netherlands"), "Portugal": ("POR", "Portugal"),
    "Rep. Dem. Congo": ("COD", "Congo DR"), "Republica Checa": ("CZE", "Czechia"),
    "República Checa": ("CZE", "Czechia"), "Senegal": ("SEN", "Senegal"),
    "Sudáfrica": ("RSA", "South Africa"), "Suecia": ("SWE", "Sweden"),
    "Suiza": ("SUI", "Switzerland"), "Turquía": ("TUR", "Turkey"),
    "Túnez": ("TUN", "Tunisia"), "Uruguay": ("URY", "Uruguay"),
    "Uzbekistán": ("UZB", "Uzbekistan"),
}


def norm(texto):
    """Normaliza un nombre para comparar (sin acentos, minusculas, solo letras/numeros)."""
    base = unicodedata.normalize("NFKD", str(texto))
    base = "".join(c for c in base if not unicodedata.combining(c))
    return "".join(c for c in base.lower() if c.isalnum())


def leer_token():
    """Token de la API. Lo busca en este orden:
    1) Variable de entorno FOOTBALL_DATA_TOKEN  (la usa el robot de GitHub Actions).
    2) .streamlit/secrets.toml                  (tu PC, como hasta ahora).
    """
    token_env = os.environ.get("FOOTBALL_DATA_TOKEN")
    if token_env:
        return token_env.strip()
    if tomllib and SECRETS.exists():
        with open(SECRETS, "rb") as fp:
            return tomllib.load(fp).get("football_data_token")
    return None


def traer_api(token):
    """Devuelve la lista de partidos de fase de grupos (registros simples)."""
    req = urllib.request.Request(API_URL, headers={"X-Auth-Token": token})
    with urllib.request.urlopen(req, timeout=30) as resp:
        datos = json.loads(resp.read().decode())
    registros = []
    for match in datos.get("matches", []):
        if match.get("stage") != "GROUP_STAGE":
            continue
        score = match.get("score", {}).get("fullTime", {})
        registros.append({
            "home_tla": match["homeTeam"].get("tla"),
            "away_tla": match["awayTeam"].get("tla"),
            "home_name": match["homeTeam"].get("name"),
            "away_name": match["awayTeam"].get("name"),
            "status": match["status"],
            "utc": match.get("utcDate"),
            "gh": score.get("home"), "ga": score.get("away"),
        })
    return registros


def leer_manual():
    if MANUAL.exists():
        try:
            with open(MANUAL, encoding="utf-8") as fp:
                return json.load(fp)
        except Exception as err:
            print("AVISO: no pude leer resultados_manual.json:", err)
    return {}


def buscar(registros, tla_loc, en_loc, tla_vis, en_vis):
    """Busca el partido de la API que enfrenta a estos dos equipos.
    Empareja por TLA o por nombre (cualquiera que coincida).
    Devuelve (registro, es_local_en_casa) o (None, None)."""
    quiero = {tla_loc, norm(en_loc)}
    quiero_v = {tla_vis, norm(en_vis)}
    for reg in registros:
        casa = {reg["home_tla"], norm(reg["home_name"])}
        fuera = {reg["away_tla"], norm(reg["away_name"])}
        if (quiero & casa) and (quiero_v & fuera):
            return reg, True
        if (quiero & fuera) and (quiero_v & casa):
            return reg, False
    return None, None


def main():
    dry = "--dry-run" in sys.argv

    token = leer_token()
    if not token:
        print("ERROR: no encontre 'football_data_token' en .streamlit/secrets.toml")
        return

    with open(PARTIDOS, encoding="utf-8") as fp:
        partidos = json.load(fp)
    with open(DATA / "jugadores.json", encoding="utf-8") as fp:
        jugadores = json.load(fp)
    with open(DATA / "pronosticos.json", encoding="utf-8") as fp:
        pronosticos = json.load(fp)

    # Ranking ANTES de aplicar los nuevos resultados (para las flechitas ▲▼).
    ranking_previo = {x["id"]: x["puesto"]
                      for x in generar_leaderboard(jugadores, pronosticos, partidos)}

    try:
        registros = traer_api(token)
    except urllib.error.HTTPError as err:
        cuerpo = err.read().decode()[:200] if hasattr(err, "read") else ""
        print(f"ERROR de la API ({err.code}). ¿Token correcto o limite por minuto?")
        print("  detalle:", cuerpo)
        return
    except Exception as err:
        print("ERROR de conexion con la API:", err)
        return

    manual = leer_manual()
    cambios = []
    manual_aplicados = []
    no_encontrados = []

    for game in partidos:
        num = game["juego"]
        if game["local"] not in EQUIPOS or game["visitante"] not in EQUIPOS:
            no_encontrados.append(num)
            continue
        tla_loc, en_loc = EQUIPOS[game["local"]]
        tla_vis, en_vis = EQUIPOS[game["visitante"]]
        reg, local_en_casa = buscar(registros, tla_loc, en_loc, tla_vis, en_vis)

        nuevo = None
        if reg is None:
            no_encontrados.append(num)
        else:
            if reg.get("utc"):
                game["utc_date"] = reg["utc"]   # hora oficial del partido (UTC)
            if reg["status"] == "FINISHED" and reg["gh"] is not None:
                nuevo = (reg["gh"], reg["ga"]) if local_en_casa else (reg["ga"], reg["gh"])

        # Respaldo manual: si existe, MANDA sobre la API.
        if str(num) in manual:
            valor = manual[str(num)]
            nuevo = (valor[0], valor[1])
            manual_aplicados.append(num)

        if nuevo is not None:
            antes = (game["gl_real"], game["gv_real"], game["jugado"])
            game["gl_real"], game["gv_real"], game["jugado"] = nuevo[0], nuevo[1], True
            if antes != (nuevo[0], nuevo[1], True):
                cambios.append((num, game["local"], game["visitante"], nuevo[0], nuevo[1]))

    jugados = sum(1 for g in partidos if g["jugado"])
    print("=" * 56)
    print("ACTUALIZACION DE RESULTADOS - Mundial 2026")
    print("=" * 56)
    print(f"Partidos con marcador (total): {jugados} de 72")
    print(f"Cambios en esta corrida: {len(cambios)}")
    for num, loc, vis, gl, gv in cambios:
        print(f"   Juego {num:2d}: {loc} {gl}-{gv} {vis}")
    if manual_aplicados:
        print("Resultados MANUALES aplicados (juegos):", manual_aplicados)
    if no_encontrados:
        print("Sin match en la API (juegos):", no_encontrados)
    print(f"Por jugar: {72 - jugados}")

    if dry:
        print("\n(DRY-RUN) No se escribio nada. Quita --dry-run para guardar.")
        return

    with open(PARTIDOS, "w", encoding="utf-8") as fp:
        json.dump(partidos, fp, ensure_ascii=False, indent=2)
    print("\nOK: data/partidos.json actualizado. Refresca la app para ver los puntos.")

    # Guardar la "foto" del ranking (para las flechas de movimiento) solo cuando
    # hubo cambios, o si aun no existe (primera vez). Asi las flechas reflejan el
    # cambio de la ultima jornada procesada.
    if cambios or not RANKING_PREV.exists():
        with open(RANKING_PREV, "w", encoding="utf-8") as fp:
            json.dump(ranking_previo, fp, ensure_ascii=False, indent=2)
        print("Foto del ranking anterior guardada (ranking_anterior.json).")


if __name__ == "__main__":
    main()
