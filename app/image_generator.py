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
MONO_FONT_CANDIDATES = [
    Path("/System/Library/Fonts/Supplemental/Courier New.ttf"),
    BUNDLED_FONTS_FOLDER / "DejaVuSansMono.ttf",
]

MONO_BOLD_FONT_CANDIDATES = [
    Path("/System/Library/Fonts/Supplemental/Courier New Bold.ttf"),
    BUNDLED_FONTS_FOLDER / "DejaVuSansMono-Bold.ttf",
]

# Arial sera utilizada para:
#
# - titulos
# - labels
# - valores visibles
NORMAL_FONT_CANDIDATES = [
    Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
    BUNDLED_FONTS_FOLDER / "DejaVuSans.ttf",
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
# 6. CONSTRUIR IMAGEN EN MEMORIA
# ------------------------------------------------------------

def build_passport_image(passport):

    # --------------------------------------------------------
    # DIMENSIONES
    # --------------------------------------------------------

    # Ancho.
    width = 1600

    # Alto.
    height = 1000


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
            30,
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
        (80, 60),
        "SYNTHETIC TEST DOCUMENT",
        fill="black",
        font=title_font
    )


    # --------------------------------------------------------
    # ADVERTENCIA
    # --------------------------------------------------------

    draw.text(
        (80, 120),
        "NOT A REAL PASSPORT",
        fill="black",
        font=label_font
    )


    # --------------------------------------------------------
    # TEST ID
    # --------------------------------------------------------

    draw.text(
        (1150, 70),
        f"Test ID: {passport['id']}",
        fill="black",
        font=label_font
    )


    # --------------------------------------------------------
    # COUNTRY
    # --------------------------------------------------------

    draw.text(
        (1150, 115),
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
    photo_top = 230

    # Posicion derecha.
    photo_right = 450

    # Posicion inferior.
    photo_bottom = 650


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
        (170, 420),
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
    y = 230

    # Separacion vertical.
    spacing = 105


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
    # correctamente por el scanner.


    # --------------------------------------------------------
    # LINEA SEPARADORA
    # --------------------------------------------------------

    draw.line(
        (
            80,
            750,
            1520,
            750
        ),
        fill="black",
        width=3
    )


    # --------------------------------------------------------
    # LABEL MRZ
    # --------------------------------------------------------

    draw.text(
        (90, 775),
        "MACHINE READABLE ZONE",
        fill="black",
        font=label_font
    )


    # --------------------------------------------------------
    # MRZ LINE 1
    # --------------------------------------------------------

    draw.text(
        (90, 830),
        passport["mrz"]["line1"],
        fill="black",
        font=mrz_font
    )


    # --------------------------------------------------------
    # MRZ LINE 2
    # --------------------------------------------------------

    draw.text(
        (90, 885),
        passport["mrz"]["line2"],
        fill="black",
        font=mrz_font
    )


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
