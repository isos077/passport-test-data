# ============================================================
# PASSPORT TEST IMAGE GENERATOR
# Archivo: app/image_generator.py
#
# Objetivo:
# Leer output/expected_results.json
# y generar una imagen sintetica por cada escenario.
#
# BASELINE OCR:
# - Fondo blanco
# - Texto negro
# - MRZ en la parte inferior
# - Fuente monoespaciada normal para MRZ
# - Sin blur
# - Sin rotacion
# - Sin modificaciones de contraste
#
# NOTA (Fase 2/3):
# build_passport_image() genera la imagen EN MEMORIA (PIL.Image)
# sin escribir a disco. create_test_passport_image() sigue
# escribiendo a disco para no romper el flujo CLI existente.
# La app web (main.py) usa build_passport_image() directamente.
# ============================================================


# ------------------------------------------------------------
# 1. IMPORTS
# ------------------------------------------------------------

# json permite leer expected_results.json.
import json

# Path permite trabajar con rutas de archivos.
from pathlib import Path

# Pillow permite crear imagenes,
# dibujar texto, lineas y figuras.
from PIL import Image, ImageDraw, ImageFont


# ------------------------------------------------------------
# 2. RUTAS DEL PROYECTO
# ------------------------------------------------------------

# __file__ representa este archivo.
#
# resolve() obtiene su ruta absoluta.
CURRENT_FILE = Path(__file__).resolve()


# .parent obtiene la carpeta app/.
APP_FOLDER = CURRENT_FILE.parent


# Subimos otro nivel para obtener:
#
# passport-test-data/
PROJECT_ROOT = APP_FOLDER.parent


# Ruta del archivo generado previamente:
#
# output/expected_results.json
EXPECTED_RESULTS_FILE = (
    PROJECT_ROOT
    / "output"
    / "expected_results.json"
)


# Carpeta donde guardaremos las imagenes:
#
# output/images/
IMAGES_FOLDER = (
    PROJECT_ROOT
    / "output"
    / "images"
)


# ------------------------------------------------------------
# 3. FUENTES
# ------------------------------------------------------------

# Carpeta con fuentes de licencia libre (DejaVu) empaquetadas
# dentro del proyecto. Sirven como respaldo cuando las fuentes
# de macOS no existen (por ejemplo, al correr en Render/Linux).
BUNDLED_FONTS_FOLDER = APP_FOLDER / "fonts"

# Cada rol de fuente tiene una lista de candidatos ordenada:
# primero se intenta la fuente nativa de macOS (misma que fue
# validada con el scanner), y si no existe se usa la fuente
# empaquetada equivalente.
#
# Courier New es monoespaciada. Esto es importante para la MRZ.
#
# Orden de candidatos para cada rol:
# 1) macOS: fuente real, para desarrollo local en Mac.
# 2) Linux/Render: fuente REAL de Microsoft instalada durante el
#    build de Docker via ttf-mscorefonts-installer (ver Dockerfile).
#    Es la misma Arial/Courier New, con licencia correcta (EULA de
#    Microsoft "Core Fonts for the Web"), no una alternativa parecida.
# 3) Respaldo de ultimo recurso (Liberation Sans/Mono), solo si por
#    algun motivo la instalacion de mscorefonts fallo en el build.
MSCOREFONTS_FOLDER = Path("/usr/share/fonts/truetype/msttcorefonts")

MONO_FONT_CANDIDATES = [
    Path("/System/Library/Fonts/Supplemental/Courier New.ttf"),
    MSCOREFONTS_FOLDER / "Courier_New.ttf",
    BUNDLED_FONTS_FOLDER / "LiberationMono-Regular.ttf",
]

MONO_BOLD_FONT_CANDIDATES = [
    Path("/System/Library/Fonts/Supplemental/Courier New Bold.ttf"),
    MSCOREFONTS_FOLDER / "Courier_New_Bold.ttf",
    BUNDLED_FONTS_FOLDER / "LiberationMono-Bold.ttf",
]

# Arial sera utilizada para:
#
# - titulos
# - labels
# - valores visibles
NORMAL_FONT_CANDIDATES = [
    Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
    MSCOREFONTS_FOLDER / "Arial.ttf",
    BUNDLED_FONTS_FOLDER / "LiberationSans-Regular.ttf",
]


# ------------------------------------------------------------
# 4. CARGAR EXPECTED RESULTS
# ------------------------------------------------------------

def load_expected_results():

    # Abrimos expected_results.json
    # en modo lectura.
    with open(
        EXPECTED_RESULTS_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        # json.load() convierte el JSON
        # en estructuras de Python.
        passports = json.load(file)

    # Regresamos la lista.
    return passports


# ------------------------------------------------------------
# 5. CARGAR UNA FUENTE
# ------------------------------------------------------------

def load_font(font_candidates, size):

    # Recorremos los candidatos en orden de preferencia.
    for font_path in font_candidates:

        # Verificamos que la fuente exista.
        if font_path.exists():

            # Cargamos la fuente TrueType.
            return ImageFont.truetype(
                str(font_path),
                size
            )

    # Si ninguna existe, utilizamos
    # la fuente por defecto de Pillow.
    return ImageFont.load_default()


# ------------------------------------------------------------
# 5b. DIAGNOSTICO: QUE FUENTE SE USO REALMENTE
# ------------------------------------------------------------

# Se ejecuta una sola vez, al iniciar el proceso (al importar este
# modulo), e imprime en los logs cual archivo de fuente se resolvio
# para cada rol. Util para confirmar en los logs de Render si se
# esta usando la fuente real de Microsoft (mscorefonts) o si cayo
# al respaldo Liberation por algun problema durante el build.
def _log_resolved_fonts():

    roles = {
        "Arial/Normal (titulos, labels, valores)": NORMAL_FONT_CANDIDATES,
        "Courier New (MRZ)": MONO_FONT_CANDIDATES,
        "Courier New Bold": MONO_BOLD_FONT_CANDIDATES,
    }

    print("[fonts] Fuentes resueltas al iniciar el proceso:")

    for role, candidates in roles.items():

        resolved = None

        for font_path in candidates:
            if font_path.exists():
                resolved = font_path
                break

        if resolved:
            print(f"[fonts]   {role}: {resolved}")
        else:
            print(f"[fonts]   {role}: NINGUNA encontrada, usando default de Pillow")


_log_resolved_fonts()


# ------------------------------------------------------------
# 6. CONSTRUIR IMAGEN EN MEMORIA
# ------------------------------------------------------------

def build_passport_image(passport, *, background_margin=0, td3_ratio=False):
    """
    Construye la imagen del pasaporte sintetico.

    Parametros nuevos (para diagnosticar el problema de deteccion en
    iOS: ahi no se detecta ni el documento ni la MRZ, aunque en Android
    si funciona):

    background_margin -- pixeles de fondo gris alrededor del documento,
        simulando una foto real del documento sobre una superficie.
        0 (default) = comportamiento identico al original (sin margen),
        que es el que ya esta validado en Android.

    td3_ratio -- si es True, ajusta el alto del lienzo para que la
        proporcion ancho:alto coincida con una pagina de datos TD3 real
        (125mm x 88mm). False (default) = mantiene el alto original
        (1000px), igual que el comportamiento ya validado en Android.

    Con ambos parametros en su valor default, el resultado es
    exactamente el mismo que antes de este cambio.
    """

    # --------------------------------------------------------
    # DIMENSIONES
    # --------------------------------------------------------

    # Ancho.
    width = 1600

    # Alto.
    #
    # Por default usamos 1000 (el ya validado en Android). Si
    # td3_ratio=True, lo recalculamos para que coincida con la
    # proporcion real de una pagina de datos TD3 (125mm x 88mm).
    if td3_ratio:
        height = round(width * 88 / 125)
    else:
        height = 1000

    # Factor de escala vertical: todas las coordenadas Y de este
    # documento fueron afinadas para height=1000. Si height cambia
    # (td3_ratio=True), escalamos proporcionalmente para que el
    # layout se mantenga igual de proporcionado.
    scale = height / 1000

    def y_at(value):
        return round(value * scale)


    # --------------------------------------------------------
    # CREAR LIENZO
    # --------------------------------------------------------

    # Creamos una imagen RGB.
    #
    # Fondo:
    #
    # white
    image = Image.new(
        "RGB",
        (width, height),
        "white"
    )


    # ImageDraw permite dibujar
    # sobre nuestra imagen.
    draw = ImageDraw.Draw(image)


    # --------------------------------------------------------
    # CARGAR FUENTES
    # --------------------------------------------------------

    # Fuente grande para el titulo.
    title_font = load_font(
        NORMAL_FONT_CANDIDATES,
        46
    )


    # Fuente para labels.
    label_font = load_font(
        NORMAL_FONT_CANDIDATES,
        26
    )


    # Fuente para valores.
    value_font = load_font(
        NORMAL_FONT_CANDIDATES,
        34
    )


    # IMPORTANTE:
    #
    # MRZ utiliza Courier New NORMAL.
    #
    # No estamos utilizando Bold.
    mrz_font = load_font(
        MONO_FONT_CANDIDATES,
        34
    )


    # --------------------------------------------------------
    # BORDE EXTERIOR
    # --------------------------------------------------------

    draw.rectangle(
        (
            30,
            y_at(30),
            width - 30,
            height - 30
        ),
        outline="black",
        width=3
    )


    # ========================================================
    # CABECERA
    # ========================================================

    # --------------------------------------------------------
    # TITULO
    # --------------------------------------------------------

    draw.text(
        (80, y_at(60)),
        "SYNTHETIC TEST DOCUMENT",
        fill="black",
        font=title_font
    )


    # --------------------------------------------------------
    # ADVERTENCIA
    # --------------------------------------------------------

    draw.text(
        (80, y_at(120)),
        "NOT A REAL PASSPORT",
        fill="black",
        font=label_font
    )


    # --------------------------------------------------------
    # TEST ID
    # --------------------------------------------------------

    draw.text(
        (1150, y_at(70)),
        f"Test ID: {passport['id']}",
        fill="black",
        font=label_font
    )


    # --------------------------------------------------------
    # COUNTRY
    # --------------------------------------------------------

    draw.text(
        (1150, y_at(115)),
        f"Country: {passport['country']}",
        fill="black",
        font=label_font
    )


    # ========================================================
    # FOTO SINTETICA
    # ========================================================

    # Posicion izquierda.
    photo_left = 90

    # Posicion superior.
    photo_top = y_at(230)

    # Posicion derecha.
    photo_right = 450

    # Posicion inferior.
    photo_bottom = y_at(650)


    # Dibujamos el rectangulo
    # que representa una fotografia.
    draw.rectangle(
        (
            photo_left,
            photo_top,
            photo_right,
            photo_bottom
        ),
        outline="black",
        width=4
    )


    # Texto dentro del placeholder.
    draw.text(
        (170, y_at(420)),
        "TEST PHOTO",
        fill="black",
        font=label_font
    )


    # ========================================================
    # DATOS PERSONALES
    # ========================================================

    # Posicion horizontal principal.
    x = 530

    # Posicion vertical inicial.
    y = y_at(230)

    # Separacion vertical.
    spacing = y_at(105)


    # --------------------------------------------------------
    # SURNAME
    # --------------------------------------------------------

    draw.text(
        (x, y),
        "SURNAME",
        fill="black",
        font=label_font
    )

    draw.text(
        (x, y + 35),
        passport["surname"],
        fill="black",
        font=value_font
    )

    # Bajamos al siguiente bloque.
    y += spacing


    # --------------------------------------------------------
    # GIVEN NAMES
    # --------------------------------------------------------

    draw.text(
        (x, y),
        "GIVEN NAMES",
        fill="black",
        font=label_font
    )

    draw.text(
        (x, y + 35),
        passport["given_names"],
        fill="black",
        font=value_font
    )

    # Bajamos.
    y += spacing


    # --------------------------------------------------------
    # PASSPORT NUMBER
    # --------------------------------------------------------

    draw.text(
        (x, y),
        "PASSPORT NUMBER",
        fill="black",
        font=label_font
    )

    draw.text(
        (x, y + 35),
        passport["passport_number"],
        fill="black",
        font=value_font
    )


    # --------------------------------------------------------
    # NATIONALITY
    # --------------------------------------------------------

    # Utilizamos una segunda columna.
    draw.text(
        (980, y),
        "NATIONALITY",
        fill="black",
        font=label_font
    )

    draw.text(
        (980, y + 35),
        passport["nationality"],
        fill="black",
        font=value_font
    )


    # Bajamos.
    y += spacing


    # --------------------------------------------------------
    # DATE OF BIRTH
    # --------------------------------------------------------

    draw.text(
        (x, y),
        "DATE OF BIRTH",
        fill="black",
        font=label_font
    )

    draw.text(
        (x, y + 35),
        passport["birth_date"],
        fill="black",
        font=value_font
    )


    # --------------------------------------------------------
    # SEX
    # --------------------------------------------------------

    draw.text(
        (980, y),
        "SEX",
        fill="black",
        font=label_font
    )

    draw.text(
        (980, y + 35),
        passport["sex"],
        fill="black",
        font=value_font
    )


    # Bajamos.
    y += spacing


    # --------------------------------------------------------
    # EXPIRATION DATE
    # --------------------------------------------------------

    draw.text(
        (x, y),
        "EXPIRATION DATE",
        fill="black",
        font=label_font
    )

    draw.text(
        (x, y + 35),
        passport["expiration_date"],
        fill="black",
        font=value_font
    )


    # ========================================================
    # MRZ
    # ========================================================

    # IMPORTANTE:
    #
    # La MRZ va en la parte INFERIOR de la imagen.
    #
    # Esta es la configuracion que fue reconocida
    # correctamente por el scanner (en Android).


    # --------------------------------------------------------
    # LINEA SEPARADORA
    # --------------------------------------------------------

    draw.line(
        (
            80,
            y_at(750),
            1520,
            y_at(750)
        ),
        fill="black",
        width=3
    )


    # --------------------------------------------------------
    # LABEL MRZ
    # --------------------------------------------------------

    draw.text(
        (90, y_at(775)),
        "MACHINE READABLE ZONE",
        fill="black",
        font=label_font
    )


    # --------------------------------------------------------
    # MRZ LINE 1
    # --------------------------------------------------------

    draw.text(
        (90, y_at(830)),
        passport["mrz"]["line1"],
        fill="black",
        font=mrz_font
    )


    # --------------------------------------------------------
    # MRZ LINE 2
    # --------------------------------------------------------

    draw.text(
        (90, y_at(885)),
        passport["mrz"]["line2"],
        fill="black",
        font=mrz_font
    )


    # ========================================================
    # FONDO / MARGEN (simula una foto real del documento)
    # ========================================================

    # Si background_margin=0 (default), no se toca nada: el
    # resultado es identico al comportamiento ya validado.
    if background_margin:

        # Gris neutro, simulando una superficie/mesa detras del
        # documento -- le da al detector de bordes de iOS algo
        # con que distinguir "documento" de "fondo".
        canvas = Image.new(
            "RGB",
            (width + 2 * background_margin, height + 2 * background_margin),
            (190, 190, 190)
        )

        canvas.paste(image, (background_margin, background_margin))

        image = canvas


    # ========================================================
    # REGRESAR IMAGEN
    # ========================================================

    return image


# ------------------------------------------------------------
# 7. CREAR IMAGEN Y GUARDARLA EN DISCO
# ------------------------------------------------------------

def create_test_passport_image(passport):

    # Creamos output/images/
    # si todavia no existe.
    IMAGES_FOLDER.mkdir(
        parents=True,
        exist_ok=True
    )

    # Construimos la imagen en memoria.
    image = build_passport_image(passport)

    # Nombre del archivo:
    #
    # MEX-001.png
    # MEX-002.png
    # USA-001.png
    # etc.
    output_file = (
        IMAGES_FOLDER
        / f"{passport['id']}.png"
    )


    # Guardamos la imagen PNG.
    image.save(
        output_file
    )


    # Mostramos resultado.
    print(
        "Image generated:",
        output_file
    )


# ------------------------------------------------------------
# 8. GENERAR TODAS LAS IMAGENES
# ------------------------------------------------------------

def generate_all_images(passports):

    # Recorremos todos los pasaportes
    # existentes en expected_results.json.
    for passport in passports:

        # Generamos una imagen.
        create_test_passport_image(
            passport
        )


# ------------------------------------------------------------
# 9. MAIN
# ------------------------------------------------------------

def main():

    # Cargamos expected_results.json.
    passports = load_expected_results()


    # Mostramos cuantos escenarios encontramos.
    print(
        "Passports found:",
        len(passports)
    )

    print()


    # Generamos las imagenes.
    generate_all_images(
        passports
    )


    # Resumen final.
    print()

    print(
        "Total images generated:",
        len(passports)
    )


# ------------------------------------------------------------
# 10. PUNTO DE ENTRADA
# ------------------------------------------------------------

if __name__ == "__main__":

    # Ejecutamos el programa.
    main()
