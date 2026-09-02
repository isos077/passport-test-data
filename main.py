# ============================================================
# PASSPORT TEST DATA GENERATOR - WEB APP
# Archivo: main.py
#
# Objetivo (Fase 2 del plan documentado):
# Exponer el generador existente (app/mrz.py, app/image_generator.py)
# como una aplicacion web con FastAPI, sin duplicar logica.
#
# GET  /          -> formulario HTML (escenario existente o datos custom)
# POST /generate  -> genera MRZ, valida, genera PNG EN MEMORIA y lo entrega
#
# Ejecutar localmente:
#   uvicorn main:app --reload
#   abrir http://127.0.0.1:8000
#
# En produccion (Render) no se escribe nada a disco: la imagen se
# genera en un BytesIO y se entrega directo en la respuesta HTTP.
# ============================================================


# ------------------------------------------------------------
# 1. IMPORTS
# ------------------------------------------------------------

import io
import json
from pathlib import Path

from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, StreamingResponse

# Reutilizamos la logica ya existente y probada.
from app.mrz import generate_td3_mrz, validate_td3_mrz
from app.image_generator import build_passport_image


# ------------------------------------------------------------
# 2. RUTAS DEL PROYECTO
# ------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent

# scenarios/passports.json sigue siendo la fuente de verdad
# para los escenarios predefinidos.
PASSPORTS_FILE = PROJECT_ROOT / "scenarios" / "passports.json"


# ------------------------------------------------------------
# 3. APP
# ------------------------------------------------------------

app = FastAPI(title="Passport Test Data Generator")


# ------------------------------------------------------------
# 4. CARGAR ESCENARIOS PREDEFINIDOS
# ------------------------------------------------------------

def load_scenarios():

    if not PASSPORTS_FILE.exists():
        return []

    with open(PASSPORTS_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


# ------------------------------------------------------------
# 5. CONSTRUIR REGISTRO (MRZ + VALIDACION)
# ------------------------------------------------------------

def build_passport_record(data: dict) -> dict:
    """
    Toma los campos base de un pasaporte (de un escenario o de un
    formulario custom), genera su MRZ TD3, la valida y arma el
    diccionario que espera image_generator.build_passport_image().
    """

    # Normalizamos mayusculas para que el documento se vea consistente
    # sin importar como haya sido escrito el formulario.
    normalized = dict(data)
    for key in ("issuing_country", "nationality", "surname", "given_names", "passport_number", "sex"):
        if normalized.get(key):
            normalized[key] = str(normalized[key]).upper()

    line1, line2 = generate_td3_mrz(
        issuing_country=normalized["issuing_country"],
        surname=normalized["surname"],
        given_names=normalized["given_names"],
        passport_number=normalized["passport_number"],
        nationality=normalized["nationality"],
        birth_date=normalized["birth_date"],
        sex=normalized["sex"],
        expiration_date=normalized["expiration_date"],
    )

    validation = validate_td3_mrz(line1, line2)

    normalized.setdefault("id", normalized.get("passport_number", "CUSTOM"))
    normalized.setdefault("country", normalized.get("issuing_country", ""))
    normalized["mrz"] = {"line1": line1, "line2": line2}
    normalized["validation"] = validation

    return normalized


# ------------------------------------------------------------
# 6. FORMULARIO HTML
# ------------------------------------------------------------

def render_form(scenarios, error=None):

    options_html = "".join(
        f'<option value="{s["id"]}">{s["id"]} - {s.get("country", "")}</option>'
        for s in scenarios
    )

    error_html = f'<p style="color:#b00020;">{error}</p>' if error else ""

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="utf-8">
    <title>Passport Test Data Generator</title>
    <style>
        body {{ font-family: -apple-system, Arial, sans-serif; max-width: 640px; margin: 40px auto; color: #1a1a1a; }}
        h1 {{ font-size: 24px; }}
        h2 {{ font-size: 18px; margin-top: 32px; border-top: 1px solid #ddd; padding-top: 24px; }}
        table {{ border-collapse: collapse; width: 100%; }}
        td {{ padding: 6px 8px; }}
        td:first-child {{ width: 200px; color: #555; }}
        input, select {{ width: 100%; padding: 6px; box-sizing: border-box; }}
        button {{ margin-top: 16px; padding: 10px 18px; cursor: pointer; }}
        .warning {{ color: #b00020; font-size: 13px; }}
    </style>
</head>
<body>
    <h1>Passport Test Data Generator</h1>
    <p class="warning">Genera documentos SINTETICOS de prueba. No son pasaportes reales.</p>
    {error_html}

    <h2>Opcion 1: escenario existente</h2>
    <form action="/generate" method="post">
        <select name="scenario_id" required>
            <option value="" disabled selected>Selecciona un escenario</option>
            {options_html}
        </select>
        <button type="submit">Generate Image</button>
    </form>

    <h2>Opcion 2: datos personalizados</h2>
    <form action="/generate" method="post">
        <table>
            <tr><td>Issuing Country</td><td><input name="issuing_country" maxlength="3" placeholder="MEX" required></td></tr>
            <tr><td>Nationality</td><td><input name="nationality" maxlength="3" placeholder="MEX" required></td></tr>
            <tr><td>Surname</td><td><input name="surname" placeholder="GREEN" required></td></tr>
            <tr><td>Given Names</td><td><input name="given_names" placeholder="RACHEL" required></td></tr>
            <tr><td>Passport Number</td><td><input name="passport_number" placeholder="AB12345" required></td></tr>
            <tr><td>Birth Date (YYMMDD)</td><td><input name="birth_date" maxlength="6" placeholder="900701" required></td></tr>
            <tr><td>Sex</td><td>
                <select name="sex">
                    <option value="F">F</option>
                    <option value="M">M</option>
                    <option value="X">X</option>
                </select>
            </td></tr>
            <tr><td>Expiration Date (YYMMDD)</td><td><input name="expiration_date" maxlength="6" placeholder="301114" required></td></tr>
        </table>
        <button type="submit">Generate Passport</button>
    </form>
</body>
</html>"""


# ------------------------------------------------------------
# 7. ENDPOINTS
# ------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
def index():
    scenarios = load_scenarios()
    return render_form(scenarios)


@app.post("/generate")
def generate(
    scenario_id: str = Form(None),
    issuing_country: str = Form(None),
    nationality: str = Form(None),
    surname: str = Form(None),
    given_names: str = Form(None),
    passport_number: str = Form(None),
    birth_date: str = Form(None),
    sex: str = Form(None),
    expiration_date: str = Form(None),
):
    scenarios = load_scenarios()

    # --------------------------------------------------------
    # MODO 1: ESCENARIO EXISTENTE
    # --------------------------------------------------------
    if scenario_id:
        scenario = next((s for s in scenarios if s["id"] == scenario_id), None)

        if scenario is None:
            html = render_form(scenarios, error=f"Escenario '{scenario_id}' no encontrado.")
            return HTMLResponse(html, status_code=404)

        data = scenario

    # --------------------------------------------------------
    # MODO 2: DATOS PERSONALIZADOS
    # --------------------------------------------------------
    else:
        required = {
            "issuing_country": issuing_country,
            "nationality": nationality,
            "surname": surname,
            "given_names": given_names,
            "passport_number": passport_number,
            "birth_date": birth_date,
            "sex": sex,
            "expiration_date": expiration_date,
        }

        missing = [key for key, value in required.items() if not value]

        if missing:
            html = render_form(scenarios, error=f"Faltan campos: {', '.join(missing)}")
            return HTMLResponse(html, status_code=400)

        data = required

    # --------------------------------------------------------
    # GENERAR MRZ + VALIDAR + IMAGEN
    # --------------------------------------------------------
    record = build_passport_record(data)
    image = build_passport_image(record)

    # Generamos el PNG en memoria (sin tocar disco).
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)

    filename = f"{record['id']}.png"

    return StreamingResponse(
        buffer,
        media_type="image/png",
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )
