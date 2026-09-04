# ============================================================
# GENERADOR DE VARIANTES DE PRUEBA (diagnostico iOS)
# Archivo: app/generate_ios_test_images.py
#
# Problema: en Android el scanner lee bien, en iOS no detecta
# ni el documento ni la MRZ.
#
# Este script genera, para UN escenario, 5 variantes -- cada una
# aislando una sola hipotesis -- para identificar cual es la causa
# real antes de aplicar el cambio de forma permanente:
#
#   baseline   -> identica a la imagen actual (control, sin cambios)
#   margin     -> agrega fondo/margen gris alrededor del documento
#                 (simula una foto real sobre una superficie)
#   td3_ratio  -> ajusta el lienzo a la proporcion real de un TD3
#                 (125mm x 88mm) en vez de la actual (1600x1000)
#   dpi        -> agrega metadata de DPI (300) al PNG
#   all        -> combina las tres
#
# Uso:
#   python app/generate_ios_test_images.py [SCENARIO_ID]
#
# Si no se indica SCENARIO_ID, usa el primer escenario disponible
# en output/expected_results.json.
# ============================================================

import sys

from image_generator import (
    load_expected_results,
    build_passport_image,
    PROJECT_ROOT,
)

OUTPUT_FOLDER = PROJECT_ROOT / "output" / "images_ios_test"

VARIANTS = {
    "baseline":  {"background_margin": 0,   "td3_ratio": False, "dpi": None},
    "margin":    {"background_margin": 120, "td3_ratio": False, "dpi": None},
    "td3_ratio": {"background_margin": 0,   "td3_ratio": True,  "dpi": None},
    "dpi":       {"background_margin": 0,   "td3_ratio": False, "dpi": (300, 300)},
    "all":       {"background_margin": 120, "td3_ratio": True,  "dpi": (300, 300)},
}


def main():

    passports = load_expected_results()

    if not passports:
        print("No hay escenarios en output/expected_results.json.")
        print("Corre primero: python app/generate_passports.py")
        return

    scenario_id = sys.argv[1] if len(sys.argv) > 1 else passports[0]["id"]

    passport = next(
        (p for p in passports if p["id"] == scenario_id),
        None
    )

    if passport is None:
        print(f"Escenario '{scenario_id}' no encontrado en expected_results.json.")
        return

    OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)

    print(f"Generando variantes de prueba para: {passport['id']} ({passport['country']})")
    print()

    for name, options in VARIANTS.items():

        image = build_passport_image(
            passport,
            background_margin=options["background_margin"],
            td3_ratio=options["td3_ratio"],
        )

        output_file = OUTPUT_FOLDER / f"{passport['id']}_{name}.png"

        if options["dpi"]:
            image.save(output_file, dpi=options["dpi"])
        else:
            image.save(output_file)

        print(
            f"  {name:12s} -> {output_file.name}"
            f"  (tamano: {image.size[0]}x{image.size[1]}, dpi: {options['dpi'] or 'default'})"
        )

    print()
    print(f"Listo. Las 5 variantes estan en: {OUTPUT_FOLDER}")
    print("Pasalas a tu iPhone y prueba cada una con el scanner.")
    print("Dime cual(es) SI detectan el documento/MRZ para saber cual era la causa.")


if __name__ == "__main__":
    main()
