"""
app.py - Quiniela AV · Mundial 2026
App web (Streamlit) con login para que cada participante consulte sus puntos.
Solo LEE los archivos JSON de la carpeta data/ (nunca los modifica).
Para correrla:  python -m streamlit run app.py

NOTA: la logica (motor de puntos, login, mapeo de usuarios, lectura de JSON)
no cambia. Este archivo trae ademas toda la capa visual (CSS) integrada.
"""

import base64
import hashlib
import hmac
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import streamlit as st

from motor_puntos import calcular_puntos, generar_leaderboard

# --------------------------------------------------------------------------
# Configuracion general de la pagina
# --------------------------------------------------------------------------
st.set_page_config(
    page_title="Quiniela AV · Mundial 2026",
    page_icon="⚽",
    layout="centered",
)

BASE = Path(__file__).parent
DATA = BASE / "data"
ASSETS = BASE / "assets"

# --------------------------------------------------------------------------
# Usuarios: cada usuario (lo que se escribe en el login) -> id del jugador
# en jugadores.json. Esto NO es secreto (la clave si lo es, va en secrets.toml).
# --------------------------------------------------------------------------
USUARIOS = {
    "renzo": "Renzo",
    "diegoalexandre": "Diego",
    "diegofernandez": "Diego F",
    "victor": "Victor",
    "mauricio": "Mauricio",
    "richard": "Richard",
    "jesus": "Jesus G",
    "andres": "Andres",
    "gustavo": "Gustavo",
    "sofia": "Sofia",
    "gabriel": "Gabriel F",
    "gabrielc": "Gabriel C",
    "marielys": "Marielys",
    "pedro": "Pedro M",
    "yimys1": "Yimys 1",
    "yimys2": "Yimys 2",
    "ronny": "Ronny S",
    "eduardo": "Eduardo K",
    "antonella": "Antonella G",
    "leonardo": "Leonardo",
    "dian": "Dian",
    "patrick": "Patrick",
    "erick": "Erick",
    "jose": "Jose Ignacio",
    "federico": "Federico",
    "valentina": "Valentina G",
}

MESES = {1: "ene", 2: "feb", 3: "mar", 4: "abr", 5: "may", 6: "jun",
         7: "jul", 8: "ago", 9: "sep", 10: "oct", 11: "nov", 12: "dic"}


# --------------------------------------------------------------------------
# Imagenes incrustadas (logo, copa y fondos optimizados)
# --------------------------------------------------------------------------
@st.cache_data
def _img_b64(path):
    try:
        with open(path, "rb") as fp:
            return base64.b64encode(fp.read()).decode()
    except Exception:
        return ""


LOGO_B64 = _img_b64(str(ASSETS / "Logo_av.png"))
LOGO_RB_B64 = _img_b64(str(ASSETS / "logo_RB.png"))
LOGO_LOGIN_GIF_B64 = _img_b64(str(ASSETS / "logo_login.gif"))  # animacion del login (optimizada)
FONDO_LOGIN_B64 = _img_b64(str(ASSETS / "fondo_login_web.jpg"))
FONDO_APP_B64 = _img_b64(str(ASSETS / "fondo_adentro_web.jpg"))


# --------------------------------------------------------------------------
# ESTILOS (CSS)
# --------------------------------------------------------------------------
def css_base():
    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Poppins:wght@600;700;800&display=swap');

:root{
  --green:#1f8a4c; --green2:#2aa65c; --green-deep:#0b3d2e;
  --gold:#efc75e; --ink:#13211b; --muted:#6b7280;
}
html, body, [class*="css"], .stApp{ font-family:'Inter',system-ui,-apple-system,sans-serif; }
h1,h2,h3,h4{ font-family:'Poppins','Inter',sans-serif; }

/* Ocultar cromo de Streamlit para un look propio */
[data-testid="stHeader"]{ background:transparent; height:0; }
[data-testid="stToolbar"]{ display:none; }
[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"],
[data-testid="collapsedControl"]{ display:none; }
#MainMenu, footer{ visibility:hidden; }

/* Botones */
.stButton>button, .stFormSubmitButton>button{
  background:linear-gradient(135deg,var(--green2),var(--green));
  color:#fff; border:0; border-radius:12px; padding:.65rem 1rem; width:100%;
  font-weight:700; font-family:'Poppins',sans-serif; letter-spacing:.3px;
  box-shadow:0 6px 18px rgba(31,138,76,.35); transition:transform .05s, box-shadow .2s;
}
.stButton>button:hover, .stFormSubmitButton>button:hover{
  box-shadow:0 8px 24px rgba(31,138,76,.5); transform:translateY(-1px);
}

/* Tablas tipo tarjeta */
.cardwrap{ background:#fff; border-radius:16px; padding:6px;
  box-shadow:0 12px 30px rgba(0,0,0,.22); overflow-x:auto; }
.qtab{ width:100%; border-collapse:collapse; font-size:14px; }
.qtab th,.qtab td{ padding:10px 8px; text-align:center; border-bottom:1px solid #eef0ee; }
.qtab thead th{ background:var(--green-deep); color:#fff; font-family:'Poppins',sans-serif;
  font-weight:600; font-size:12px; text-transform:uppercase; letter-spacing:.4px; }
.qtab td.izq,.qtab th.izq{ text-align:left; }
.qtab tbody tr:nth-child(even){ background:#f7faf8; }
.qtab td{ color:var(--ink); }
.qtab tbody tr:last-child td{ border-bottom:0; }
.badge{ display:inline-block; min-width:26px; padding:3px 9px; border-radius:999px;
  color:#fff; font-weight:800; font-size:12.5px; }
.b3{ background:#2e7d32; } .b2{ background:#e0a008; } .b0{ background:#9aa3ad; }
.porjugar{ color:#9aa3ad; font-style:italic; }
.qtab tr.mifila td{ background:#fff7e0 !important; font-weight:700;
  box-shadow: inset 3px 0 0 var(--green); }

/* Tiles del dashboard */
.tiles{ display:flex; gap:12px; margin:4px 0 16px; }
.tile{ flex:1; background:rgba(255,255,255,.97); border-radius:16px; padding:14px 8px;
  text-align:center; box-shadow:0 12px 26px rgba(0,0,0,.20); border-top:3px solid var(--green); }
.t-label{ display:block; font-size:11px; color:var(--muted); font-weight:700;
  text-transform:uppercase; letter-spacing:.5px; }
.t-num{ display:block; font-family:'Poppins',sans-serif; font-weight:800; font-size:30px;
  color:var(--ink); line-height:1.1; margin-top:4px; }
.tile-pos .t-num{ color:var(--green-deep); }
.tile-pts .t-num{ color:var(--green); }
.tile-ex  .t-num{ color:#c79a14; }

@media (max-width:480px){
  .t-num{ font-size:23px; } .tiles{ gap:8px; }
  .qtab th,.qtab td{ padding:8px 5px; font-size:13px; }
}
</style>
""", unsafe_allow_html=True)


def css_login():
    st.markdown(f"""
<style>
/* Fondo de cuadros acercado (cover), como estaba antes */
.stApp{{
  background:#161e34 url('data:image/jpeg;base64,{FONDO_LOGIN_B64}') center/cover fixed no-repeat;
}}
.stApp::before{{
  content:""; position:fixed; inset:0; pointer-events:none;
  background: radial-gradient(circle at 50% 32%, rgba(10,16,32,.05), rgba(8,12,26,.66) 90%);
}}
.block-container{{ max-width:560px; padding-top:2rem; position:relative; z-index:1; }}

.hero{{ text-align:center; }}
/* Logo AV centrado, MUY grande, sin halo ni copa */
.hero .logo-av{{ width:440px; max-width:86vw; display:block; margin:0 auto;
  filter:drop-shadow(0 14px 30px rgba(0,0,0,.6)); }}

/* Logo RB abajo a la derecha del login */
.logo-rb{{ position:fixed; right:18px; bottom:16px; width:74px; z-index:5;
  opacity:.95; filter:drop-shadow(0 4px 12px rgba(0,0,0,.5)); pointer-events:none; }}

.hero h1{{ color:#fff; font-size:46px; font-weight:800; margin:10px 0 0; letter-spacing:.5px;
  text-shadow:0 4px 20px rgba(0,0,0,.7); }}
.hero .sub{{ color:var(--gold); font-family:'Poppins',sans-serif; font-weight:700;
  letter-spacing:8px; font-size:15px; text-transform:uppercase; margin-top:3px; }}

[data-testid="stForm"]{{
  background:rgba(10,16,30,.62); border:1px solid rgba(255,255,255,.16);
  border-radius:18px; padding:22px 18px 10px; margin-top:22px;
  backdrop-filter:blur(10px); box-shadow:0 22px 50px rgba(0,0,0,.55);
}}
[data-testid="stForm"] label{{ color:#eaf0f6 !important; font-weight:600; }}
/* Campos: fondo blanco con texto NEGRO */
[data-testid="stForm"] div[data-baseweb="input"]{{
  background:#ffffff !important; border:1px solid #cfd6dd; border-radius:10px; }}
[data-testid="stForm"] input{{ color:#111 !important; -webkit-text-fill-color:#111 !important; }}
[data-testid="stForm"] input::placeholder{{ color:#8a8f96 !important;
  -webkit-text-fill-color:#8a8f96 !important; }}
.stAlert{{ border-radius:12px; }}

@media (max-width:480px){{
  .hero .logo-av{{ width:88vw; }} .hero h1{{ font-size:36px; }}
}}
</style>
""", unsafe_allow_html=True)


def css_app():
    st.markdown(f"""
<style>
/* Fondo del estadio (cover, full bleed, sin bordes negros) */
.stApp{{
  background:#0b1f14 url('data:image/jpeg;base64,{FONDO_APP_B64}') center/cover fixed no-repeat;
}}
.stApp::before{{
  content:""; position:fixed; inset:0; pointer-events:none;
  background:linear-gradient(180deg, rgba(4,12,8,.74), rgba(4,12,8,.86));
}}
.block-container{{ max-width:760px; padding-top:9.5rem; padding-bottom:3rem;
  position:relative; z-index:1; }}
.block-container h1,.block-container h2,.block-container h3{{ color:#fff; }}

/* Barra superior fija (head grande, logo AV MUCHO mas grande) */
.topbar{{ position:fixed; top:0; left:0; right:0; z-index:1000;
  display:flex; align-items:center; gap:16px; min-height:120px; padding:12px 22px;
  background:linear-gradient(90deg, rgba(8,24,16,.97), rgba(10,38,23,.95));
  backdrop-filter:blur(8px); border-bottom:2px solid rgba(239,199,94,.4);
  box-shadow:0 6px 22px rgba(0,0,0,.45); }}
.topbar .left{{ display:flex; align-items:center; gap:16px; min-width:0; }}
.topbar .left img{{ height:100px; filter:drop-shadow(0 5px 14px rgba(0,0,0,.55)); }}
.topbar .brand{{ color:#fff; font-family:'Poppins',sans-serif; font-weight:800;
  font-size:24px; line-height:1; }}
.topbar .brand small{{ display:block; color:var(--gold); font-size:11px;
  letter-spacing:3px; font-weight:700; margin-top:4px; }}
.topbar .who{{ margin-left:auto; color:#eaf2ec; font-weight:600; font-size:15px;
  white-space:nowrap; overflow:hidden; text-overflow:ellipsis; max-width:34%; }}
.topbar .who .dot{{ color:var(--green2); font-size:11px; }}

/* Boton "Salir": st.button REAL en flujo normal (siempre clickeable), a la derecha */
div[data-testid="column"] .stButton>button{{
  width:auto; background:linear-gradient(135deg,#e0564f,#c0392b);
  box-shadow:0 6px 16px rgba(192,57,43,.45); padding:.45rem 1.1rem; }}
div[data-testid="column"] .stButton>button:hover{{ box-shadow:0 9px 22px rgba(192,57,43,.65); }}

@media (max-width:480px){{
  .topbar{{ min-height:96px; }} .topbar .left img{{ height:78px; }}
  .topbar .brand{{ font-size:20px; }}
  .block-container{{ padding-top:8rem; }}
}}

/* Pestañas */
.stTabs [data-baseweb="tab-list"]{{ gap:6px; background:rgba(255,255,255,.10);
  padding:6px; border-radius:14px; }}
.stTabs [data-baseweb="tab"]{{ color:#e7f0ea; border-radius:10px; padding:8px 14px;
  font-weight:600; font-family:'Poppins',sans-serif; }}
.stTabs [aria-selected="true"]{{ background:#fff !important; color:var(--green-deep) !important; }}
.stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"]{{ display:none; }}

.stSelectbox label{{ color:#fff !important; font-weight:600; }}

/* Toggle "Por partido / Consolidado" legible sobre el fondo oscuro */
[data-testid="stRadio"] label p{{ color:#eaf2ec !important; font-weight:600; }}
[data-testid="stRadio"] [role="radiogroup"]{{ gap:14px; }}

.welcome{{ color:#fff; font-family:'Poppins',sans-serif; font-weight:700;
  font-size:22px; margin:2px 0 12px; }}
.summary{{ color:#dff0e5; font-size:13.5px; margin:0 0 12px;
  background:rgba(255,255,255,.08); border:1px solid rgba(255,255,255,.14);
  border-radius:12px; padding:10px 14px; }}
.summary b{{ color:#fff; }}
.jornada{{ color:#fff; font-family:'Poppins',sans-serif; font-weight:700; font-size:15px;
  margin:18px 0 4px; padding-left:10px; border-left:4px solid var(--gold); }}
.legend{{ color:#cfe0d5; font-size:12.5px; margin-top:10px; }}
.subt{{ color:#fff; font-family:'Poppins',sans-serif; font-weight:700; font-size:18px; margin:6px 0 2px; }}

/* Desplegables (expanders) de "Puntos por juego" y "Juegos del dia" */
[data-testid="stExpander"] details{{ background:rgba(255,255,255,.97); border-radius:14px;
  border:1px solid rgba(255,255,255,.35); box-shadow:0 8px 22px rgba(0,0,0,.22);
  margin-bottom:10px; overflow:hidden; }}
[data-testid="stExpander"] summary{{ padding:11px 14px; font-family:'Poppins',sans-serif;
  font-weight:700; font-size:14px; color:#0b3d2e; }}
[data-testid="stExpander"] summary:hover{{ color:#1f8a4c; }}
[data-testid="stExpander"] summary p{{ color:#0b3d2e !important; font-weight:700; }}
[data-testid="stExpander"] [data-testid="stExpanderDetails"]{{ padding:2px 12px 12px; }}
.diahdr{{ color:#fff; font-family:'Poppins',sans-serif; font-weight:800; font-size:20px;
  margin:2px 0 4px; }}
.diasub{{ color:var(--gold); font-weight:700; font-size:13px; margin-bottom:12px;
  text-transform:uppercase; letter-spacing:1px; }}
.horachip{{ display:inline-block; background:var(--green); color:#fff; font-weight:700;
  font-size:12px; padding:2px 9px; border-radius:999px; margin-right:6px; }}

/* Distintivos del leaderboard (corona, oraculo, GM) */
.ic{{ height:16px; width:16px; vertical-align:-3px; }}
.dist{{ margin-left:5px; white-space:nowrap; }}
.legend .ic{{ vertical-align:-3px; }}
.badge-gm{{ display:inline-block; margin-left:5px; vertical-align:middle;
  background:linear-gradient(135deg,#0b3d2e,#1f8a4c); color:#efc75e;
  font-family:'Poppins',sans-serif; font-weight:800; font-size:10px; line-height:1;
  padding:2px 5px; border-radius:6px; border:1px solid rgba(239,199,94,.55); letter-spacing:.5px; }}

/* Banderas (imagen) - limpias, sin caja ni borde */
.flag{{ height:13px; width:auto; vertical-align:-2px; margin-right:6px; border-radius:1px; }}

/* Avatares (circulo con iniciales / emoji / imagen) */
.av{{ display:inline-flex; align-items:center; justify-content:center; border-radius:50%;
  vertical-align:middle; margin-right:7px; color:#fff; font-family:'Poppins',sans-serif;
  font-weight:700; overflow:hidden; box-shadow:0 0 0 1px rgba(0,0,0,.10); flex:0 0 auto; }}

/* Flechas de movimiento en el ranking */
.mov{{ font-size:11px; margin-left:3px; vertical-align:1px; }}
.mov-up{{ color:#2e7d32; }}
.mov-down{{ color:#c0392b; }}
.mov-eq{{ color:#9aa3ad; }}
.tile-acc .t-num{{ color:#1f8a4c; }}
.tile-racha .t-num{{ color:#c79a14; }}

/* Desplegables nativos (Puntos por juego / Juegos del dia) */
details.deta{{ background:rgba(255,255,255,.97); border-radius:12px; margin-bottom:10px;
  box-shadow:0 8px 22px rgba(0,0,0,.22); overflow:hidden;
  border:1px solid #e3eae5; border-left:4px solid var(--green); }}
details.deta>summary{{ position:relative; cursor:pointer; list-style:none;
  padding:12px 34px 12px 14px; font-family:'Poppins',sans-serif; font-weight:700;
  color:#0b3d2e; font-size:14px; transition:background .15s ease; }}
details.deta>summary:hover{{ background:rgba(31,138,76,.10); }}
details.deta>summary::-webkit-details-marker{{ display:none; }}
details.deta>summary::after{{ content:'▾'; position:absolute; right:14px; top:11px; color:#1f8a4c; }}
details.deta[open]>summary::after{{ content:'▴'; }}
.detbody{{ padding:2px 12px 12px; }}

/* Sub-desplegables dentro de cada partido */
details.sub{{ background:#f4f7f4; border-radius:10px; margin:8px 0; border:1px solid #e3eae5; }}
details.sub>summary{{ position:relative; cursor:pointer; list-style:none;
  padding:9px 30px 9px 12px; font-family:'Poppins',sans-serif; font-weight:700;
  font-size:13px; color:#0b3d2e; }}
details.sub>summary::-webkit-details-marker{{ display:none; }}
details.sub>summary::after{{ content:'▾'; position:absolute; right:12px; top:9px; color:#1f8a4c; }}
details.sub[open]>summary::after{{ content:'▴'; }}
.subbody{{ padding:4px 12px 12px; }}

/* Gráfico "La comunidad" (barras por lado) */
.comitem{{ margin:8px 0; }}
.comhead{{ display:flex; justify-content:space-between; align-items:center; gap:8px;
  font-size:13px; color:#13211b; font-weight:600; margin-bottom:4px; }}
.comname{{ display:flex; align-items:center; }}
.comnum{{ color:#0b3d2e; font-weight:800; white-space:nowrap; }}
.comtrack{{ background:#e7ece7; border-radius:999px; height:12px; overflow:hidden; }}
.comfill{{ height:100%; border-radius:999px; min-width:2px; }}
.cf-local{{ background:linear-gradient(90deg,#2aa65c,#1f8a4c); }}
.cf-draw{{ background:linear-gradient(90deg,#f3d271,#e0a008); }}
.cf-away{{ background:linear-gradient(90deg,#1f8a4c,#0b3d2e); }}
.comitem.gano .comhead{{ color:#0b3d2e; }}
.realchip{{ background:#0b3d2e; color:#efc75e; font-size:10px; font-weight:800;
  padding:1px 6px; border-radius:6px; margin-left:6px; border:1px solid rgba(239,199,94,.5);
  white-space:nowrap; }}

/* Podio top 3 */
.podio{{ display:flex; justify-content:center; align-items:flex-end; gap:10px; margin:6px 0 18px; }}
.podio .p{{ flex:1; max-width:33%; text-align:center; }}
.podio .corona{{ font-size:26px; line-height:1; margin-bottom:2px; }}
.podio .avatar{{ width:54px; height:54px; border-radius:50%; margin:0 auto 6px;
  display:flex; align-items:center; justify-content:center; font-family:'Poppins',sans-serif;
  font-weight:800; font-size:20px; color:#fff; border:3px solid rgba(255,255,255,.85);
  box-shadow:0 8px 18px rgba(0,0,0,.35); }}
.podio .p1 .avatar{{ width:66px; height:66px; font-size:25px; color:#5a4500;
  background:linear-gradient(135deg,#f9ecae,#e0a008); border-color:var(--gold); }}
.podio .p2 .avatar{{ background:linear-gradient(135deg,#e8eef0,#9aa9b0); color:#33424a; }}
.podio .p3 .avatar{{ background:linear-gradient(135deg,#e7b88a,#b5763f); }}
.podio .pname{{ color:#fff; font-weight:700; font-size:13px; line-height:1.15;
  min-height:30px; padding:0 2px; }}
.podio .ppts{{ color:var(--gold); font-family:'Poppins',sans-serif; font-weight:800;
  font-size:15px; margin-top:1px; }}
.podio .ped{{ margin-top:8px; border-radius:10px 10px 0 0;
  border:1px solid rgba(255,255,255,.16); border-bottom:0;
  display:flex; align-items:flex-start; justify-content:center; padding-top:8px;
  font-family:'Poppins',sans-serif; font-weight:800; font-size:18px; }}
.podio .ped1{{ height:92px; background:linear-gradient(180deg,#f6e08a,#caa12f); color:#5a4500; }}
.podio .ped2{{ height:68px; background:linear-gradient(180deg, rgba(31,138,76,.95), rgba(11,61,46,.95));
  color:rgba(255,255,255,.9); }}
.podio .ped3{{ height:50px; background:linear-gradient(180deg, rgba(31,138,76,.85), rgba(11,61,46,.92));
  color:rgba(255,255,255,.9); }}

@media (max-width:480px){{
  .topbar .brand{{ font-size:18px; }} .topbar .left img{{ height:50px; }}
  .podio .pname{{ font-size:11.5px; }} .podio .avatar{{ width:46px; height:46px; font-size:17px; }}
  .podio .p1 .avatar{{ width:56px; height:56px; font-size:21px; }}
}}
</style>
""", unsafe_allow_html=True)


# --------------------------------------------------------------------------
# Carga de datos (en cache para que sea rapido). La app solo LEE.
# --------------------------------------------------------------------------
def _firma_datos():
    """Marca de tiempo de los JSON: si cambian (al actualizar resultados),
    se refresca el cache automaticamente."""
    try:
        return tuple(os.path.getmtime(DATA / n) for n in
                     ("jugadores.json", "pronosticos.json", "partidos.json"))
    except Exception:
        return None


@st.cache_data
def cargar_datos(firma):
    with open(DATA / "jugadores.json", encoding="utf-8") as fp:
        jugadores = json.load(fp)
    with open(DATA / "pronosticos.json", encoding="utf-8") as fp:
        pronosticos = json.load(fp)
    with open(DATA / "partidos.json", encoding="utf-8") as fp:
        partidos = json.load(fp)
    return jugadores, pronosticos, partidos


TZ_OFFSET = timedelta(hours=-4)  # Venezuela (UTC-4)


def fecha_bonita(iso):
    """ '2026-06-11' -> '11 jun' """
    try:
        anio, mes, dia = iso[:10].split("-")
        return f"{int(dia)} {MESES[int(mes)]}"
    except Exception:
        return iso or "-"


def hora_local(utc_str):
    """ '2026-06-14T19:00:00Z' (UTC) -> datetime en hora de Venezuela (UTC-4)."""
    if not utc_str:
        return None
    try:
        base = datetime.strptime(utc_str[:19], "%Y-%m-%dT%H:%M:%S")
        return base + TZ_OFFSET
    except Exception:
        return None


def hoy_local():
    """Fecha de 'hoy' en hora de Venezuela."""
    return (datetime.now(timezone.utc) + TZ_OFFSET).date()


def fecha_local_de(partido):
    """Fecha local del partido (preferir la hora oficial UTC; si no, el campo fecha)."""
    hl = hora_local(partido.get("utc_date"))
    if hl:
        return hl.date()
    try:
        return datetime.strptime(partido["fecha"][:10], "%Y-%m-%d").date()
    except Exception:
        return None


def hora_ampm(utc_str):
    """ '...T19:00:00Z' -> '3:00 PM' en hora de Venezuela (o '' si no hay)."""
    hl = hora_local(utc_str)
    if not hl:
        return ""
    h12 = hl.hour % 12 or 12
    ampm = "AM" if hl.hour < 12 else "PM"
    return f"{h12}:{hl.minute:02d} {ampm}"


# Banderas como IMAGEN (flagcdn.com): se ven igual en Windows, Mac, Android e iPhone.
# Codigo de bandera por equipo (ISO 3166-1 alpha-2; Inglaterra/Escocia = subdivision).
COD_BANDERA = {
    "México": "mx", "Sudáfrica": "za", "Corea del Sur": "kr", "República Checa": "cz",
    "Republica Checa": "cz", "Canadá": "ca", "Bosnia y Herzegovina": "ba",
    "Estados Unidos": "us", "Paraguay": "py", "Catar": "qa", "Suiza": "ch", "Brasil": "br",
    "Marruecos": "ma", "Haití": "ht", "Australia": "au", "Turquía": "tr", "Alemania": "de",
    "Curazao": "cw", "Países Bajos": "nl", "Japón": "jp", "Irán": "ir", "Nueva Zelanda": "nz",
    "España": "es", "Cabo Verde": "cv", "Bélgica": "be", "Egipto": "eg", "Arabia Saudita": "sa",
    "Uruguay": "uy", "Francia": "fr", "Senegal": "sn", "Irak": "iq", "Noruega": "no",
    "Argentina": "ar", "Argelia": "dz", "Austria": "at", "Jordania": "jo", "Portugal": "pt",
    "Rep. Dem. Congo": "cd", "Suecia": "se", "Uzbekistán": "uz", "Colombia": "co",
    "Croacia": "hr", "Ghana": "gh", "Panamá": "pa", "Costa de Marfil": "ci", "Ecuador": "ec",
    "Túnez": "tn", "Inglaterra": "gb-eng", "Escocia": "gb-sct",
}


def bandera(nombre):
    """<img> de la bandera (flagcdn.com), o '' si el pais no esta mapeado.
    Si la imagen no carga, se oculta sola (queda solo el nombre)."""
    code = COD_BANDERA.get(nombre)
    if not code:
        return ""
    return (f"<img class='flag' loading='lazy' alt='' "
            f"src='https://flagcdn.com/40x30/{code}.png' "
            f"srcset='https://flagcdn.com/80x60/{code}.png 2x' "
            f"onerror=\"this.style.display='none'\">")


def eq(nombre):
    """Nombre del equipo con su bandera (imagen) delante."""
    return f"{bandera(nombre)}{nombre}"


def stats_jugador(pid, pronosticos, partidos):
    """% de acierto (partidos donde sumó puntos) y racha actual (seguidos sumando)."""
    jugados = [p for p in partidos
               if p["jugado"] and p["gl_real"] is not None and p["gv_real"] is not None]
    jugados.sort(key=lambda p: (hora_local(p.get("utc_date")) or datetime.min, p["juego"]))
    pron_por_juego = {x["juego"]: x for x in pronosticos.get(pid, [])}

    secuencia = []
    for p in jugados:
        pr = pron_por_juego.get(p["juego"])
        if pr is None:
            continue
        pts = calcular_puntos(pr, p)
        if pts is None:
            continue
        secuencia.append(pts)

    if not secuencia:
        return None
    aciertos = sum(1 for x in secuencia if x > 0)
    racha = 0
    for x in reversed(secuencia):
        if x > 0:
            racha += 1
        else:
            break
    return {"pct": round(aciertos * 100 / len(secuencia)), "racha": racha}


# --------------------------------------------------------------------------
# Avatares: iniciales en circulo de color, generadas del nombre (consistente).
# --------------------------------------------------------------------------
def _iniciales(nombre):
    tokens = [t for t in str(nombre).split() if not t.isdigit()]
    if not tokens:
        return "?"
    if len(tokens) == 1:
        return tokens[0][:1].upper()
    return (tokens[0][0] + tokens[1][0]).upper()


def _color_de(nombre):
    h = 0
    for c in str(nombre):
        h = (h * 31 + ord(c)) % 360
    return f"hsl({h}, 52%, 42%)"


def avatar_html(jug, size=28):
    """Círculo con las iniciales y un color derivado del nombre."""
    nombre = jug.get("nombre", "?")
    return (f"<span class='av av-ini' style='width:{size}px;height:{size}px;"
            f"background:{_color_de(nombre)};font-size:{int(size*0.42)}px'>"
            f"{_iniciales(nombre)}</span>")


def cargar_ranking_anterior():
    """Foto del ranking de la jornada pasada (la guarda actualizar_resultados.py)."""
    try:
        with open(DATA / "ranking_anterior.json", encoding="utf-8") as fp:
            return json.load(fp)
    except Exception:
        return {}


def flecha_mov(actual, anterior):
    """▲ subió, ▼ bajó, – igual (o '' si no hay dato previo)."""
    if anterior is None:
        return "<span class='mov mov-eq'>–</span>"
    if actual < anterior:
        return "<span class='mov mov-up'>▲</span>"
    if actual > anterior:
        return "<span class='mov mov-down'>▼</span>"
    return "<span class='mov mov-eq'>–</span>"


# Icono SVG del "Oraculo" (bola de cristal), paleta verde/dorado.
ORACULO_SVG = (
    "<svg class='ic' viewBox='0 0 24 24' xmlns='http://www.w3.org/2000/svg'>"
    "<defs><radialGradient id='oraculo' cx='40%' cy='34%' r='72%'>"
    "<stop offset='0' stop-color='#cdebd8'/><stop offset='55%' stop-color='#1f8a4c'/>"
    "<stop offset='100%' stop-color='#0b3d2e'/></radialGradient></defs>"
    "<path d='M7.5 17 h9 l-1.4 2.6 h-6.2 z' fill='#efc75e'/>"
    "<ellipse cx='12' cy='20.2' rx='5.2' ry='1' fill='#caa12f'/>"
    "<circle cx='12' cy='10' r='7' fill='url(#oraculo)' stroke='#efc75e' stroke-width='.6'/>"
    "<circle cx='9.6' cy='7.7' r='1.8' fill='#fff' opacity='.5'/></svg>"
)


def nombre_corto(n):
    """Primeras dos palabras del nombre, para que quepa en el podio."""
    partes = str(n).split()
    return " ".join(partes[:2]) if partes else n


def clave_compartida():
    """Lee la clave del archivo de secretos. Devuelve None si no esta configurada."""
    try:
        return st.secrets["clave"]
    except Exception:
        return None


# --------------------------------------------------------------------------
# Sesion persistente: guardamos el usuario en la URL (?u=...&t=...) para que
# la sesion sobreviva al refresco. El token "t" es un sello firmado con la
# clave compartida: prueba que la persona paso por el login y no se puede
# falsificar sin conocer la clave. Si cierran el navegador y entran a la URL
# limpia (sin ?u=...), se pedira login de nuevo.
# --------------------------------------------------------------------------
def _token_para(usuario):
    """Sello corto del usuario, firmado con la clave compartida (HMAC-SHA256)."""
    clave = clave_compartida() or ""
    firma = hmac.new(clave.encode(), usuario.encode(), hashlib.sha256)
    return firma.hexdigest()[:16]


def restaurar_sesion():
    """Si la URL trae un usuario + token validos, vuelve a iniciar la sesion.
    Esto es lo que hace que el login sobreviva al refrescar la pagina."""
    if st.session_state.get("logueado"):
        return
    u = st.query_params.get("u")
    t = st.query_params.get("t")
    if u and t and u in USUARIOS and hmac.compare_digest(t, _token_para(u)):
        st.session_state.logueado = True
        st.session_state.jugador_id = USUARIOS[u]
        st.session_state.usuario = u


def recordar_en_url(usuario):
    """Escribe el usuario y su token en la URL (para sobrevivir al refresco)."""
    st.query_params["u"] = usuario
    st.query_params["t"] = _token_para(usuario)


def olvidar_url():
    """Limpia la URL al cerrar sesion (borra ?u=...&t=...)."""
    st.query_params.clear()


def barra_superior(nombre):
    logo = f"<img src='data:image/png;base64,{LOGO_B64}'/>" if LOGO_B64 else "⚽"
    return f"""
<div class="topbar">
  <div class="left">{logo}<div class="brand">Quiniela AV<small>MUNDIAL 2026</small></div></div>
  <div class="who"><span class="dot">●</span> {nombre}</div>
</div>
"""


# --------------------------------------------------------------------------
# LOGIN
# --------------------------------------------------------------------------
def pantalla_login():
    # Logo animado (GIF). Si no esta, cae al logo PNG estatico de respaldo.
    if LOGO_LOGIN_GIF_B64:
        av = f"<img class='logo-av' src='data:image/gif;base64,{LOGO_LOGIN_GIF_B64}'/>"
    elif LOGO_B64:
        av = f"<img class='logo-av' src='data:image/png;base64,{LOGO_B64}'/>"
    else:
        av = ""
    st.markdown(
        f"<div class='hero'>{av}"
        f"<h1>Quiniela AV</h1><div class='sub'>Mundial 2026</div></div>",
        unsafe_allow_html=True,
    )
    if LOGO_RB_B64:
        st.markdown(f"<img class='logo-rb' src='data:image/png;base64,{LOGO_RB_B64}'/>",
                    unsafe_allow_html=True)

    with st.form("login"):
        usuario = st.text_input("Usuario", placeholder="tu usuario")
        clave = st.text_input("Clave", type="password", placeholder="clave compartida")
        entrar = st.form_submit_button("Entrar  →")

    if entrar:
        clave_ok = clave_compartida()
        if clave_ok is None:
            st.error("La app no tiene configurada la clave. "
                     "Falta el archivo .streamlit/secrets.toml.")
            return
        u = usuario.strip().lower()
        if u in USUARIOS and clave == clave_ok:
            st.session_state.logueado = True
            st.session_state.jugador_id = USUARIOS[u]
            st.session_state.usuario = u
            recordar_en_url(u)  # deja la sesion en la URL: sobrevive al refresco
            st.rerun()
        else:
            st.error("Usuario o clave incorrectos. Revisa e intenta de nuevo. 🙂")


# --------------------------------------------------------------------------
# PANTALLA 1: MI PERFIL
# --------------------------------------------------------------------------
def pantalla_perfil(jugadores, pronosticos, partidos):
    pid = st.session_state.jugador_id
    jug = next((j for j in jugadores if j["id"] == pid), {"id": pid, "nombre": pid})
    nombre = jug["nombre"]

    st.markdown(
        f"<div class='welcome'>{avatar_html(jug, 40)}¡Hola, {nombre}! 👋</div>",
        unsafe_allow_html=True,
    )

    tabla = generar_leaderboard(jugadores, pronosticos, partidos)
    mi = next((f for f in tabla if f["id"] == pid), None)
    puesto = f"#{mi['puesto']}" if mi else "-"
    puntos = mi["puntos"] if mi else 0
    exactos = mi["exactos"] if mi else 0

    st.markdown(f"""
<div class="tiles">
  <div class="tile tile-pos"><span class="t-label">Posición</span><span class="t-num">{puesto}</span></div>
  <div class="tile tile-pts"><span class="t-label">Puntos</span><span class="t-num">{puntos}</span></div>
  <div class="tile tile-ex"><span class="t-label">Exactos</span><span class="t-num">{exactos}</span></div>
</div>
""", unsafe_allow_html=True)

    est = stats_jugador(pid, pronosticos, partidos)
    acierto = f"{est['pct']}%" if est else "—"
    racha = (f"{est['racha']} 🔥" if est and est["racha"] > 0 else "0")
    st.markdown(f"""
<div class="tiles">
  <div class="tile tile-acc"><span class="t-label">Acierto</span><span class="t-num">{acierto}</span></div>
  <div class="tile tile-racha"><span class="t-label">Racha</span><span class="t-num">{racha}</span></div>
</div>
""", unsafe_allow_html=True)

    st.markdown("<div class='subt'>Mis 72 pronósticos</div>", unsafe_allow_html=True)

    pmap = {p["juego"]: p for p in partidos}
    filas = ""
    for pron in pronosticos.get(pid, []):
        partido = pmap[pron["juego"]]
        nombre_partido = f"{eq(partido['local'])} vs {eq(partido['visitante'])}"

        if pron["gl"] is None or pron["gv"] is None:
            pron_txt = "—"
        else:
            pron_txt = f"{pron['gl']}-{pron['gv']}"

        pts = calcular_puntos(pron, partido)
        if pts is None:
            real_txt = "<span class='porjugar'>Por jugar</span>"
            pts_html = ""
        else:
            real_txt = f"{partido['gl_real']}-{partido['gv_real']}"
            clase = "b3" if pts == 3 else "b2" if pts == 2 else "b0"
            pts_html = f"<span class='badge {clase}'>{pts}</span>"

        filas += (f"<tr><td>{pron['juego']}</td>"
                  f"<td class='izq'>{nombre_partido}</td>"
                  f"<td>{pron_txt}</td><td>{real_txt}</td><td>{pts_html}</td></tr>")

    st.markdown(
        "<div class='cardwrap'><table class='qtab'><thead><tr>"
        "<th>#</th><th class='izq'>Partido</th><th>Tu pron.</th>"
        "<th>Real</th><th>Pts</th></tr></thead><tbody>"
        + filas + "</tbody></table></div>",
        unsafe_allow_html=True,
    )
    st.markdown("<div class='legend'>🟢 3 = score exacto · "
                "🟡 2 = ganador/empate acertado · ⚪ 0 = no acertaste</div>",
                unsafe_allow_html=True)


# --------------------------------------------------------------------------
# PANTALLA 2: LEADERBOARD
# --------------------------------------------------------------------------
def _podio_card(slot, fila):
    """Una columna del podio. slot = 1 (centro), 2 (izq) o 3 (der)."""
    corona = "<div class='corona'>👑</div>" if slot == 1 else "<div class='corona'>&nbsp;</div>"
    nombre = nombre_corto(fila["nombre"])
    return (f"<div class='p p{slot}'>{corona}"
            f"<div class='avatar'>{slot}</div>"
            f"<div class='pname'>{nombre}</div>"
            f"<div class='ppts'>{fila['puntos']} pts</div>"
            f"<div class='ped ped{slot}'>{slot}</div></div>")


def pantalla_leaderboard(jugadores, pronosticos, partidos):
    st.markdown("<div class='welcome'>🏆 Tabla de posiciones</div>", unsafe_allow_html=True)

    jugados = sum(1 for p in partidos
                  if p["jugado"] and p["gl_real"] is not None and p["gv_real"] is not None)
    if jugados == 0:
        actualizacion = "aún no se han cargado resultados"
    else:
        ts = os.path.getmtime(DATA / "partidos.json")
        actualizacion = datetime.fromtimestamp(ts).strftime("%d/%m/%Y %H:%M")

    st.markdown(
        f"<div class='summary'>⚽ Partidos jugados: <b>{jugados} de 72</b> &nbsp;·&nbsp; "
        f"🕒 Última actualización: {actualizacion}</div>",
        unsafe_allow_html=True,
    )

    pid = st.session_state.jugador_id
    tabla = generar_leaderboard(jugadores, pronosticos, partidos)
    jug_por_id = {j["id"]: j for j in jugadores}
    anterior = cargar_ranking_anterior()  # foto de la jornada pasada (id -> puesto)

    # Podio top 3 (centro=1, izquierda=2, derecha=3). Robusto ante empates/ceros.
    if len(tabla) >= 3:
        izq = _podio_card(2, tabla[1])
        cen = _podio_card(1, tabla[0])
        der = _podio_card(3, tabla[2])
        st.markdown(f"<div class='podio'>{izq}{cen}{der}</div>", unsafe_allow_html=True)

    # Corona: UNA sola, para el #1 (tabla ya viene desempatada por puntos,
    # luego exactos, luego alfabetico -> tabla[0] es el unico lider).
    corona_id = tabla[0]["id"] if tabla else None
    # Oraculo: UNO solo, el de mas exactos (desempate: mas puntos, luego alfabetico).
    max_ex = max((f["exactos"] for f in tabla), default=0)
    oraculo_id = None
    if max_ex > 0:
        candidatos = [f for f in tabla if f["exactos"] == max_ex]
        oraculo_id = sorted(candidatos, key=lambda f: (-f["puntos"], f["nombre"]))[0]["id"]

    # Tabla COMPLETA, desde la posicion 1 hasta el ultimo.
    filas = ""
    for f in tabla:
        clase = "mifila" if f["id"] == pid else ""
        mov = flecha_mov(f["puesto"], anterior.get(f["id"]))
        avatar = avatar_html(jug_por_id.get(f["id"], {"nombre": f["nombre"]}), 26)
        distintivos = ""
        if f["id"] == corona_id:
            distintivos += "<span class='dist'>👑</span>"
        if f["id"] == oraculo_id:
            distintivos += f"<span class='dist'>{ORACULO_SVG}</span>"
        est = stats_jugador(f["id"], pronosticos, partidos)
        if est and est["racha"] >= 3:
            fuego = "🔥" if est["racha"] == 3 else f"🔥{est['racha']}"
            distintivos += f"<span class='dist'>{fuego}</span>"
        if f["id"] == "Renzo":
            distintivos += "<span class='badge-gm'>GM</span>"
        filas += (f"<tr class='{clase}'><td>{f['puesto']}{mov}</td>"
                  f"<td class='izq'>{avatar}{f['nombre']}{distintivos}</td>"
                  f"<td>{f['puntos']}</td><td>{f['exactos']}</td>"
                  f"<td>{f['evaluados']}</td></tr>")

    st.markdown(
        "<div class='cardwrap'><table class='qtab'><thead><tr>"
        "<th>Pos</th><th class='izq'>Jugador</th><th>Pts</th>"
        "<th>Exactos</th><th>Jugados</th></tr></thead><tbody>"
        + filas + "</tbody></table></div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<div class='legend'>👑 Líder &nbsp;·&nbsp; {ORACULO_SVG} Oráculo: más exactos "
        f"&nbsp;·&nbsp; 🔥 en racha (3+ seguidos sumando) &nbsp;·&nbsp; "
        f"<span class='badge-gm'>GM</span> creador &nbsp;·&nbsp; "
        "<span class='mov-up'>▲</span>/<span class='mov-down'>▼</span> cambio vs jornada "
        "anterior. Orden por puntos; desempate por exactos. Tu fila resaltada.</div>",
        unsafe_allow_html=True,
    )


# --------------------------------------------------------------------------
# PANTALLA 3: RESULTADOS
# --------------------------------------------------------------------------
def pantalla_resultados(partidos):
    st.markdown("<div class='welcome'>📅 Resultados</div>", unsafe_allow_html=True)

    fechas = sorted({p["fecha"] for p in partidos if p["fecha"]})
    opciones = ["TODAS"] + fechas
    sel = st.selectbox(
        "Filtrar por jornada",
        opciones,
        format_func=lambda x: "Todas las jornadas" if x == "TODAS" else fecha_bonita(x),
    )

    fechas_mostrar = fechas if sel == "TODAS" else [sel]

    for fecha in fechas_mostrar:
        del_dia = [p for p in partidos if p["fecha"] == fecha]
        st.markdown(f"<div class='jornada'>{fecha_bonita(fecha)}</div>", unsafe_allow_html=True)

        filas = ""
        orden = sorted(del_dia, key=lambda x: (hora_local(x.get("utc_date")) or datetime.min,
                                               x["juego"]))
        for p in orden:
            nombre_partido = f"{eq(p['local'])} vs {eq(p['visitante'])}"
            hora = hora_ampm(p.get("utc_date")) or "—"
            if p["jugado"] and p["gl_real"] is not None and p["gv_real"] is not None:
                marcador = f"<b>{p['gl_real']}-{p['gv_real']}</b>"
            else:
                marcador = "<span class='porjugar'>Por jugar</span>"
            filas += (f"<tr><td>{p['juego']}</td>"
                      f"<td class='izq'>{nombre_partido}</td>"
                      f"<td>{hora}</td><td>{marcador}</td></tr>")

        st.markdown(
            "<div class='cardwrap'><table class='qtab'><thead><tr>"
            "<th>#</th><th class='izq'>Partido</th><th>Hora</th><th>Marcador</th>"
            "</tr></thead><tbody>" + filas + "</tbody></table></div>",
            unsafe_allow_html=True,
        )


# --------------------------------------------------------------------------
# Ayudante compartido: tabla de "que pronostico cada jugador" para un partido
# --------------------------------------------------------------------------
def _filas_pronos(partido, pronosticos, nombre_por_id, con_puntos):
    filas = []
    for pid, lista in pronosticos.items():
        pron = next((x for x in lista if x["juego"] == partido["juego"]), None)
        if pron is None:
            continue
        if pron["gl"] is None or pron["gv"] is None:
            pred = "—"
        else:
            pred = f"{pron['gl']}-{pron['gv']}"
        if con_puntos:
            pts = calcular_puntos(pron, partido)
            filas.append((nombre_por_id.get(pid, pid), pred, 0 if pts is None else pts))
        else:
            filas.append((nombre_por_id.get(pid, pid), pred, None))
    if con_puntos:
        filas.sort(key=lambda f: (-f[2], f[0]))   # mas puntos primero
    else:
        filas.sort(key=lambda f: f[0])            # alfabetico
    return filas


def _tabla_pronos_html(filas, con_puntos):
    cuerpo = ""
    for nombre, pred, pts in filas:
        if con_puntos:
            clase = "b3" if pts == 3 else "b2" if pts == 2 else "b0"
            celda = f"<td><span class='badge {clase}'>{pts}</span></td>"
            cuerpo += f"<tr><td class='izq'>{nombre}</td><td>{pred}</td>{celda}</tr>"
        else:
            cuerpo += f"<tr><td class='izq'>{nombre}</td><td>{pred}</td></tr>"
    encab = ("<th class='izq'>Jugador</th><th>Pronóstico</th><th>Pts</th>"
             if con_puntos else "<th class='izq'>Jugador</th><th>Pronóstico</th>")
    return ("<div style='overflow-x:auto'><table class='qtab'><thead><tr>"
            + encab + "</tr></thead><tbody>" + cuerpo + "</tbody></table></div>")


def _comunidad_html(partido, pronosticos):
    """Gráfico de barras: hacia qué LADO se inclinó el grupo (local/empate/visitante)."""
    cl = cd = cv = 0
    total = 0
    for _pid, lista in pronosticos.items():
        pron = next((x for x in lista if x["juego"] == partido["juego"]), None)
        if pron is None or pron["gl"] is None or pron["gv"] is None:
            continue
        total += 1
        if pron["gl"] > pron["gv"]:
            cl += 1
        elif pron["gl"] < pron["gv"]:
            cv += 1
        else:
            cd += 1
    if total == 0:
        return "<div class='legend' style='color:#6b7280'>Nadie pronosticó este partido.</div>"

    real = None
    if partido["jugado"] and partido["gl_real"] is not None and partido["gv_real"] is not None:
        if partido["gl_real"] > partido["gv_real"]:
            real = "local"
        elif partido["gl_real"] < partido["gv_real"]:
            real = "away"
        else:
            real = "draw"

    def item(lado, etiqueta, cnt, clase):
        pct = round(cnt * 100 / total)
        gano = " gano" if real == lado else ""
        chip = " <span class='realchip'>✓ resultado</span>" if real == lado else ""
        return (f"<div class='comitem{gano}'><div class='comhead'>"
                f"<span class='comname'>{etiqueta}{chip}</span>"
                f"<span class='comnum'>{pct}% ({cnt})</span></div>"
                f"<div class='comtrack'><div class='comfill {clase}' "
                f"style='width:{pct}%'></div></div></div>")

    return (item("local", f"Gana {eq(partido['local'])}", cl, "cf-local")
            + item("draw", "Empate", cd, "cf-draw")
            + item("away", f"Gana {eq(partido['visitante'])}", cv, "cf-away"))


def _bloque_partido(partido, pronosticos, nombre_por_id, con_puntos, titulo):
    """Un partido como <details> con 2 sub-secciones: La comunidad y Pronósticos."""
    filas = _filas_pronos(partido, pronosticos, nombre_por_id, con_puntos)
    sub_com = ("<details class='sub'><summary>📊 Tendencia del grupo</summary>"
               f"<div class='subbody'>{_comunidad_html(partido, pronosticos)}</div></details>")
    sub_pro = ("<details class='sub'><summary>📝 Pronósticos</summary>"
               f"<div class='subbody'>{_tabla_pronos_html(filas, con_puntos)}</div></details>")
    return (f"<details class='deta'><summary>{titulo}</summary>"
            f"<div class='detbody'>{sub_com}{sub_pro}</div></details>")


# --------------------------------------------------------------------------
# PANTALLA 4: PUNTOS POR JUEGO (publico: ver pronosticos de todos por partido)
# --------------------------------------------------------------------------
def pantalla_puntos_por_juego(jugadores, pronosticos, partidos):
    st.markdown("<div class='welcome'>🎯 Puntos por juego</div>", unsafe_allow_html=True)

    # Dos modos: "Por partido" (lo de siempre) y "Consolidado" (matriz nueva).
    modo = st.radio(
        "Modo de vista",
        ["Por partido", "Consolidado"],
        horizontal=True,
        label_visibility="collapsed",
        key="modo_puntos",
    )
    if modo == "Consolidado":
        _vista_consolidada(jugadores, pronosticos, partidos)
    else:
        _vista_por_partido(jugadores, pronosticos, partidos)


def _vista_por_partido(jugadores, pronosticos, partidos):
    """Vista original: cada partido jugado como desplegable con los pronosticos."""
    st.markdown("<div class='legend' style='margin:0 0 10px'>Toca un partido jugado para ver "
                "qué pronosticó y cuántos puntos sacó cada quien.</div>", unsafe_allow_html=True)

    nombre_por_id = {j["id"]: j["nombre"] for j in jugadores}
    jugados = [p for p in partidos
               if p["jugado"] and p["gl_real"] is not None and p["gv_real"] is not None]
    if not jugados:
        st.markdown("<div class='summary'>Aún no hay partidos jugados.</div>",
                    unsafe_allow_html=True)
        return

    bloques = ""
    for p in sorted(jugados, key=lambda x: x["juego"]):
        titulo = (f"Juego {p['juego']} · {eq(p['local'])} "
                  f"{p['gl_real']}-{p['gv_real']} {eq(p['visitante'])}")
        bloques += _bloque_partido(p, pronosticos, nombre_por_id, True, titulo)
    st.markdown(bloques, unsafe_allow_html=True)


# --------------------------------------------------------------------------
# VISTA CONSOLIDADA: matriz jugadores x partidos (con scroll horizontal y
# primera columna fija). Usa clases CSS propias (.matrix-wrap/.mtab) para no
# afectar el resto de la app.
# --------------------------------------------------------------------------
LEYENDA_MATRIZ = (
    "<div class='mleyenda'>"
    "<span><i class='mchip mchip-3'></i> Marcador exacto</span>"
    "<span><i class='mchip mchip-2'></i> Resultado correcto</span>"
    "<span><i class='mchip mchip-0'></i> Fallo</span></div>"
)


def css_matriz():
    """Estilos SOLO de la matriz consolidada. El scroll queda confinado a
    .matrix-wrap; la primera columna (.scol) se queda fija al desplazar."""
    st.markdown("""
<style>
.matrix-wrap{ background:#fff; border-radius:16px; padding:6px;
  box-shadow:0 12px 30px rgba(0,0,0,.22);
  overflow-x:auto; -webkit-overflow-scrolling:touch; max-width:100%; }
.mleyenda{ display:flex; flex-wrap:wrap; gap:14px; margin:0 0 10px;
  color:#dff0e5; font-size:12.5px; }
.mleyenda span{ display:inline-flex; align-items:center; gap:6px; }
.mchip{ width:16px; height:16px; border-radius:4px; display:inline-block;
  border:1px solid rgba(0,0,0,.12); }
.mchip-3{ background:#cdeccf; } .mchip-2{ background:#fbe7b6; } .mchip-0{ background:#eceff2; }

.mtab{ border-collapse:separate; border-spacing:0; font-size:13px; }
.mtab th, .mtab td{ padding:7px 8px; text-align:center; white-space:nowrap;
  border-bottom:1px solid #eef0ee; }
.mtab thead th{ background:var(--green-deep); color:#fff; font-weight:600;
  font-size:11px; vertical-align:middle; }
.mtab thead .mh{ display:flex; gap:3px; justify-content:center; align-items:center;
  margin-bottom:2px; }
.mtab thead .mh .flag{ height:12px; margin:0; }
.mtab thead .mh-res{ font-family:'Poppins',sans-serif; font-weight:700; font-size:12px;
  color:var(--gold); }
.mtab thead .mh-res.napend{ color:#9fb4a6; }

/* Primera columna FIJA (puntos + jugador) */
.mtab th.scol, .mtab td.scol{ position:sticky; left:0; z-index:2; text-align:left;
  width:160px; min-width:160px; white-space:normal; box-shadow:1px 0 0 #e3eae5; }
.mtab td.scol{ background:#fff; color:#13211b; }
.mtab tbody tr:nth-child(even) td.scol{ background:#f7faf8; }
.mtab thead th.scol{ z-index:3; background:var(--green-deep); }
.mtab .m-pts{ display:inline-block; min-width:24px; font-family:'Poppins',sans-serif;
  font-weight:800; color:var(--green-deep); margin-right:6px; }
.mtab td.scol .nm{ font-weight:600; }

/* Celdas de pronostico, coloreadas por puntos */
.mtab td.c3{ background:#cdeccf; color:#13211b; font-weight:700; }
.mtab td.c2{ background:#fbe7b6; color:#13211b; }
.mtab td.c0{ background:#eceff2; color:#8a939b; }
.mtab td.cna{ background:#fff; color:#c2c8cf; }
.mtab tbody tr:last-child td{ border-bottom:0; }
</style>
""", unsafe_allow_html=True)


def _matriz_consolidada_html(jugadores, pronosticos, partidos, columnas):
    """Arma la tabla matriz: filas = jugadores (orden por puntos, total a la
    izquierda); columnas = partidos; cada celda = pronostico coloreado."""
    tabla = generar_leaderboard(jugadores, pronosticos, partidos)
    jug_por_id = {j["id"]: j for j in jugadores}

    # Encabezado: una columna por partido (banderas + resultado real o '—').
    ths = "<th class='scol'>Jugador</th>"
    for p in columnas:
        jugado = p["jugado"] and p["gl_real"] is not None and p["gv_real"] is not None
        if jugado:
            res = f"<div class='mh-res'>{p['gl_real']}-{p['gv_real']}</div>"
        else:
            res = "<div class='mh-res napend'>—</div>"
        ths += (f"<th><div class='mh'>{bandera(p['local'])}{bandera(p['visitante'])}</div>"
                f"{res}</th>")

    filas = ""
    for f in tabla:
        pid = f["id"]
        jug = jug_por_id.get(pid, {"nombre": f["nombre"]})
        cabeza = (f"<td class='scol'><span class='m-pts'>{f['puntos']}</span>"
                  f"{avatar_html(jug, 20)}<span class='nm'>{f['nombre']}</span></td>")
        pron_por_juego = {x["juego"]: x for x in pronosticos.get(pid, [])}
        celdas = ""
        for p in columnas:
            pron = pron_por_juego.get(p["juego"])
            if pron is None or pron["gl"] is None or pron["gv"] is None:
                pred = "—"
            else:
                pred = f"{pron['gl']}-{pron['gv']}"
            jugado = p["jugado"] and p["gl_real"] is not None and p["gv_real"] is not None
            if not jugado:
                clase = "cna"                       # no jugado: sin color
            elif pron is None:
                clase = "c0"                         # jugado pero no pronostico: fallo
            else:
                pts = calcular_puntos(pron, p)
                clase = "c3" if pts == 3 else "c2" if pts == 2 else "c0"
            celdas += f"<td class='{clase}'>{pred}</td>"
        filas += f"<tr>{cabeza}{celdas}</tr>"

    return (f"<div class='matrix-wrap'><table class='mtab'><thead><tr>{ths}</tr></thead>"
            f"<tbody>{filas}</tbody></table></div>")


def _vista_consolidada(jugadores, pronosticos, partidos):
    """Matriz de todos los pronosticos, con filtro por jornada."""
    css_matriz()
    st.markdown("<div class='legend' style='margin:0 0 10px'>Matriz de todos los pronósticos. "
                "Desliza horizontalmente para ver más partidos; la columna del jugador queda "
                "fija.</div>", unsafe_allow_html=True)

    # Filtro por jornada. 'TODAS' = solo partidos jugados (la matriz crece sola).
    fechas = sorted({p["fecha"] for p in partidos if p["fecha"]})
    sel = st.selectbox(
        "Filtrar por jornada",
        ["TODAS"] + fechas,
        format_func=lambda x: "Todas las jornadas (jugados)" if x == "TODAS" else fecha_bonita(x),
        key="jornada_consolidado",
    )

    if sel == "TODAS":
        columnas = [p for p in partidos
                    if p["jugado"] and p["gl_real"] is not None and p["gv_real"] is not None]
        columnas.sort(key=lambda p: p["juego"])
        if not columnas:
            st.markdown("<div class='summary'>Aún no hay partidos jugados para consolidar.</div>",
                        unsafe_allow_html=True)
            return
    else:
        columnas = [p for p in partidos if p["fecha"] == sel]
        columnas.sort(key=lambda p: (hora_local(p.get("utc_date")) or datetime.min, p["juego"]))
        if not columnas:
            st.markdown("<div class='summary'>No hay partidos en esa jornada.</div>",
                        unsafe_allow_html=True)
            return

    st.markdown(LEYENDA_MATRIZ, unsafe_allow_html=True)
    st.markdown(_matriz_consolidada_html(jugadores, pronosticos, partidos, columnas),
                unsafe_allow_html=True)


# --------------------------------------------------------------------------
# PANTALLA 5: JUEGOS DEL DIA (partidos de hoy + pronostico de cada jugador)
# --------------------------------------------------------------------------
def pantalla_juegos_del_dia(jugadores, pronosticos, partidos):
    st.markdown("<div class='welcome'>📆 Juegos del día</div>", unsafe_allow_html=True)
    nombre_por_id = {j["id"]: j["nombre"] for j in jugadores}

    hoy = hoy_local()
    fechas = sorted({d for d in (fecha_local_de(p) for p in partidos) if d})
    if not fechas:
        st.markdown("<div class='summary'>No hay partidos programados.</div>",
                    unsafe_allow_html=True)
        return

    if hoy in fechas:
        objetivo, es_hoy = hoy, True
    else:
        siguientes = [d for d in fechas if d > hoy]
        objetivo, es_hoy = (siguientes[0] if siguientes else fechas[-1]), False

    cabecera = "⚽ Partidos de hoy" if es_hoy else "⏭️ Próximos partidos"
    st.markdown(f"<div class='diahdr'>{cabecera}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='diasub'>{fecha_bonita(objetivo.isoformat())}</div>",
                unsafe_allow_html=True)

    juegos = [p for p in partidos if fecha_local_de(p) == objetivo]
    juegos.sort(key=lambda p: (hora_local(p.get("utc_date")) or datetime.min, p["juego"]))

    bloques = ""
    for p in juegos:
        hora_txt = hora_ampm(p.get("utc_date")) or "--:--"
        jugado = p["jugado"] and p["gl_real"] is not None and p["gv_real"] is not None
        if jugado:
            etiqueta = (f"🕒 {hora_txt}  ·  {eq(p['local'])} "
                        f"{p['gl_real']}-{p['gv_real']} {eq(p['visitante'])}")
        else:
            etiqueta = f"🕒 {hora_txt}  ·  {eq(p['local'])} vs {eq(p['visitante'])}"
        bloques += _bloque_partido(p, pronosticos, nombre_por_id, jugado, etiqueta)
    st.markdown(bloques, unsafe_allow_html=True)


# --------------------------------------------------------------------------
# APP PRINCIPAL (decide que mostrar)
# --------------------------------------------------------------------------
def main():
    css_base()

    restaurar_sesion()  # si la URL trae sesion valida, la recupera (sobrevive al refresco)

    if not st.session_state.get("logueado"):
        css_login()
        pantalla_login()
        return

    css_app()
    jugadores, pronosticos, partidos = cargar_datos(_firma_datos())
    pid = st.session_state.jugador_id
    nombre = next((j["nombre"] for j in jugadores if j["id"] == pid), pid)

    # Barra superior fija (head grande con logo AV). El boton "Salir" va en una
    # columna a la derecha (st.button real, en flujo normal -> clickeable seguro).
    st.markdown(barra_superior(nombre), unsafe_allow_html=True)
    _, col_salir = st.columns([5, 1])
    with col_salir:
        if st.button("⎋ Salir", key="logout_btn", use_container_width=True):
            for k in ("logueado", "jugador_id", "usuario"):
                st.session_state.pop(k, None)
            olvidar_url()  # borra la sesion de la URL para que no vuelva a entrar solo
            st.rerun()

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "⚽ Mi Perfil", "🏆 Leaderboard", "📅 Resultados",
        "🎯 Puntos por juego", "📆 Juegos del día"])
    with tab1:
        pantalla_perfil(jugadores, pronosticos, partidos)
    with tab2:
        pantalla_leaderboard(jugadores, pronosticos, partidos)
    with tab3:
        pantalla_resultados(partidos)
    with tab4:
        pantalla_puntos_por_juego(jugadores, pronosticos, partidos)
    with tab5:
        pantalla_juegos_del_dia(jugadores, pronosticos, partidos)


if __name__ == "__main__":
    main()
