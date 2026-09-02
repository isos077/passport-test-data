# ============================================================
# PASSPORT TEST DATA GENERATOR - WEB APP
# Archivo: main.py
#
# Objetivo (Fase 2 del plan documentado):
# Exponer el generador existente (app/mrz.py, app/image_generator.py)
# como una aplicacion web con FastAPI, sin duplicar logica.
#
# GET  /                -> formulario HTML (escenario existente o datos custom)
# POST /generate        -> genera MRZ, valida, genera PNG EN MEMORIA y lo entrega
# POST /scenarios/delete -> elimina un escenario guardado en scenarios/passports.json
#
# Ejecutar localmente:
#   uvicorn main:app --reload
#   abrir http://127.0.0.1:8000
#
# En produccion (Render) no se escribe la IMAGEN a disco: se genera
# en un BytesIO y se entrega directo en la respuesta HTTP. La lista
# de escenarios (scenarios/passports.json) si se lee/escribe a disco;
# en Render el filesystem es efimero, asi que los escenarios guardados
# o eliminados ahi se pierden en el proximo deploy/restart (en local
# son permanentes, igual que si editaras el JSON a mano).
# ============================================================


# ------------------------------------------------------------
# 1. IMPORTS
# ------------------------------------------------------------

import html
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
# 4. CARGAR / GUARDAR ESCENARIOS
# ------------------------------------------------------------

def load_scenarios():

    if not PASSPORTS_FILE.exists():
        return []

    with open(PASSPORTS_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def save_scenarios(scenarios):

    PASSPORTS_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(PASSPORTS_FILE, "w", encoding="utf-8") as file:
        json.dump(scenarios, file, indent=4, ensure_ascii=False)


def add_scenario(scenarios, data):
    """
    Agrega un nuevo escenario y lo guarda en scenarios/passports.json.
    Lanza ValueError si ya existe un escenario con el mismo id/titulo.
    """

    if any(s["id"] == data["id"] for s in scenarios):
        raise ValueError(f"Ya existe un escenario guardado con el titulo '{data['id']}'.")

    scenarios.append(data)
    save_scenarios(scenarios)


def remove_scenario(scenarios, scenario_id):
    """Elimina un escenario por id. Regresa True si existia, False si no."""

    remaining = [s for s in scenarios if s["id"] != scenario_id]

    if len(remaining) == len(scenarios):
        return False

    save_scenarios(remaining)
    return True


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

def render_form(scenarios, error=None, message=None):

    options_html = "".join(
        f'<option value="{html.escape(s["id"])}">{html.escape(s["id"])} - {html.escape(s.get("country", ""))}</option>'
        for s in scenarios
    )

    rows_html = "".join(
        f"""<tr>
            <td>{html.escape(s["id"])}</td>
            <td>{html.escape(s.get("country", ""))}</td>
            <td>
                <form action="/scenarios/delete" method="post"
                      onsubmit="return confirm('Eliminar el escenario {html.escape(s["id"])}?');"
                      style="margin:0;">
                    <input type="hidden" name="scenario_id" value="{html.escape(s["id"])}">
                    <button type="submit" class="danger">Eliminar</button>
                </form>
            </td>
        </tr>"""
        for s in scenarios
    )

    if not rows_html:
        rows_html = '<tr><td colspan="3">No hay escenarios guardados todavia.</td></tr>'

    error_html = f'<p class="notice error">{html.escape(error)}</p>' if error else ""
    message_html = f'<p class="notice success">{html.escape(message)}</p>' if message else ""

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="utf-8">
    <title>Passport Test Data Generator</title>
    <style>
        body {{ font-family: -apple-system, Arial, sans-serif; max-width: 640px; margin: 40px auto; color: #1a1a1a; }}
        h1 {{ font-size: 24px; }}
        h2 {{ font-size: 18px; margin-top: 32px; border-top: 1px solid #ddd; padding-top: 24px; }}
        table {{ border-collapse: collapse; width: 100%; margin-top: 8px; }}
        th, td {{ border-bottom: 1px solid #eee; padding: 8px; text-align: left; font-size: 14px; }}
        table td:first-child, table th:first-child {{ width: 200px; }}
        input, select {{ width: 100%; padding: 6px; box-sizing: border-box; }}
        button {{ margin-top: 16px; padding: 10px 18px; cursor: pointer; }}
        button.danger {{ margin: 0; padding: 4px 10px; font-size: 13px; color: #b00020; }}
        .warning {{ color: #b00020; font-size: 13px; }}
        .notice {{ padding: 10px 14px; border-radius: 4px; font-size: 14px; }}
        .notice.error {{ color: #b00020; background: #fdecea; }}
        .notice.success {{ color: #1e7e34; background: #e9f7ef; }}
        .field-row td {{ padding: 6px 8px; border: none; }}
        .field-row td:first-child {{ color: #555; }}
    </style>
</head>
<body>
    <h1>Passport Test Data Generator</h1>
    <p class="warning">Genera documentos SINTETICOS de prueba. No son pasaportes reales.</p>
    {error_html}
    {message_html}

    <h2>Escenarios guardados</h2>
    <table>
        <thead><tr><th>ID</th><th>Country</th><th></th></tr></thead>
        <tbody>{rows_html}</tbody>
    </table>

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
            <tr class="field-row"><td>Issuing Country</td><td><input name="issuing_country" maxlength="3" placeholder="MEX" required></td></tr>
            <tr class="field-row"><td>Nationality</td><td><input name="nationality" maxlength="3" placeholder="MEX" required></td></tr>
            <tr class="field-row"><td>Surname</td><td><input name="surname" placeholder="GREEN" required></td></tr>
            <tr class="field-row"><td>Given Names</td><td><input name="given_names" placeholder="RACHEL" required></td></tr>
            <tr class="field-row"><td>Passport Number</td><td><input name="passport_number" placeholder="AB12345" required></td></tr>
            <tr class="field-row"><td>Birth Date (YYMMDD)</td><td><input name="birth_date" maxlength="6" placeholder="900701" required></td></tr>
            <tr class="field-row"><td>Sex</td><td>
                <select name="sex">
                    <option value="F">F</option>
                    <option value="M">M</option>
                    <option value="X">X</option>
                </select>
            </td></tr>
            <tr class="field-row"><td>Expiration Date (YYMMDD)</td><td><input name="expiration_date" maxlength="6" placeholder="301114" required></td></tr>
            <tr class="field-row"><td>Titulo (opcional)</td><td><input name="save_as" placeholder="Ej: MEX-006"></td></tr>
        </table>
        <p style="font-size:12px;color:#777;">Si escribes un titulo, este pasaporte se guarda como un nuevo escenario reutilizable (aparecera en la lista de arriba).</p>
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
    save_as: str = Form(None),
):
    scenarios = load_scenarios()

    # --------------------------------------------------------
    # MODO 1: ESCENARIO EXISTENTE
    # --------------------------------------------------------
    if scenario_id:
        scenario = next((s for s in scenarios if s["id"] == scenario_id), None)

        if scenario is None:
            html_body = render_form(scenarios, error=f"Escenario '{scenario_id}' no encontrado.")
            return HTMLResponse(html_body, status_code=404)

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
            html_body = render_form(scenarios, error=f"Faltan campos: {', '.join(missing)}")
            return HTMLResponse(html_body, status_code=400)

        data = required

        # ----------------------------------------------------
        # GUARDAR COMO NUEVO ESCENARIO (opcional)
        # ----------------------------------------------------
        if save_as and save_as.strip():
            new_entry = dict(required)
            for key in ("issuing_country", "nationality", "surname", "given_names", "passport_number", "sex"):
                if new_entry.get(key):
                    new_entry[key] = str(new_entry[key]).upper()

            new_entry["id"] = save_as.strip()
            new_entry["country"] = new_entry["issuing_country"]

            try:
                add_scenario(scenarios, new_entry)
            except ValueError as exc:
                html_body = render_form(scenarios, error=str(exc))
                return HTMLResponse(html_body, status_code=409)

            # Reutilizamos el escenario ya normalizado y guardado
            # para que la imagen use el titulo elegido como Test ID.
            data = new_entry

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


@app.post("/scenarios/delete", response_class=HTMLResponse)
def delete_scenario_endpoint(scenario_id: str = Form(...)):
    scenarios = load_scenarios()
    removed = remove_scenario(scenarios, scenario_id)

    if not removed:
        html_body = render_form(scenarios, error=f"Escenario '{scenario_id}' no encontrado.")
        return HTMLResponse(html_body, status_code=404)

    scenarios = load_scenarios()
    return render_form(scenarios, message=f"Escenario '{scenario_id}' eliminado.")
