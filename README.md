# Passport Test Data Generator

Genera documentos sinteticos de prueba con MRZ TD3 para validar
funcionalidades de escaneo/OCR de pasaportes, sin usar documentos
personales reales.

Test Data (JSON) -> MRZ TD3 + check digits -> Validacion -> Imagen PNG -> Scanner/OCR

## Estructura

```
passport-test-data/
├── app/
│   ├── mrz.py               # genera y valida la MRZ TD3
│   ├── generate_passports.py  # CLI: construye output/expected_results.json
│   ├── image_generator.py   # genera las imagenes PNG (disco o en memoria)
│   └── fonts/                # DejaVu Sans / DejaVu Sans Mono (fallback Linux/Render)
├── scenarios/
│   └── passports.json       # fuente de verdad de los escenarios
├── output/                   # generado, no se versiona
├── main.py                   # app web FastAPI (Fase 2)
├── requirements.txt
└── render.yaml                # blueprint de despliegue en Render (Fase 3)
```

## Uso local (linea de comandos)

```bash
source .venv/bin/activate
python app/generate_passports.py
python app/image_generator.py
```

## Uso local (app web)

```bash
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Abrir http://127.0.0.1:8000 — permite elegir un escenario existente de
`scenarios/passports.json` o introducir datos personalizados, y genera
la imagen directamente en el navegador (sin escribir a disco).

## Despliegue en Render

1. Sube el proyecto a un repositorio de GitHub (ver `git log` / `git remote`
   mas abajo si ya se inicializo localmente).
2. En https://dashboard.render.com -> **New** -> **Blueprint**, apunta al
   repo: Render detecta `render.yaml` y configura el servicio solo.
   - Alternativa manual (**New** -> **Web Service**):
     - Build Command: `pip install -r requirements.txt`
     - Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
3. Render expone una URL publica (`https://passport-test-data.onrender.com`
   o similar) con la misma app web.

`scenarios/passports.json` viaja dentro del repo, asi que los escenarios
predefinidos estan disponibles también en producción. Las imagenes se
generan en memoria (BytesIO) — no se depende de almacenamiento persistente.

## Roadmap (Fase 4 — QA avanzado, pendiente)

- Escenarios negativos: MRZ invalida, documentos expirados.
- Robustez OCR: rotacion, blur, contraste/iluminacion.
- Comparacion automatica expected vs. resultado del scanner.
