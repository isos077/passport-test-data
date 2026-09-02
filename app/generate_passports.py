# ============================================================
# PASSPORT TEST DATA GENERATOR
# Archivo: app/generate_passports.py
#
# Objetivo:
# Leer los pasaportes sintéticos desde:
#
# scenarios/passports.json
#
# generar sus MRZ,
# validarlas
# y guardar los expected results.
# ============================================================


# ------------------------------------------------------------
# 1. IMPORTS
# ------------------------------------------------------------

# Librería estándar para trabajar con JSON.
import json


# Path permite manejar rutas.
from pathlib import Path


# Importamos las funciones creadas
# dentro de mrz.py.
from mrz import (
    generate_td3_mrz,
    validate_td3_mrz
)


# ------------------------------------------------------------
# 2. RUTAS DEL PROYECTO
# ------------------------------------------------------------

# Ruta absoluta del archivo actual.
CURRENT_FILE = Path(__file__).resolve()


# Carpeta:
#
# app/
APP_FOLDER = CURRENT_FILE.parent


# Carpeta raíz:
#
# passport-test-data/
PROJECT_ROOT = APP_FOLDER.parent


# Ruta hacia:
#
# scenarios/passports.json
PASSPORTS_FILE = (
    PROJECT_ROOT
    / "scenarios"
    / "passports.json"
)


# Ruta hacia:
#
# output/expected_results.json
EXPECTED_RESULTS_FILE = (
    PROJECT_ROOT
    / "output"
    / "expected_results.json"
)


# ------------------------------------------------------------
# 3. CARGAR PASAPORTES
# ------------------------------------------------------------

def load_passports():

    # Abrimos passports.json.
    with open(
        PASSPORTS_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        # Convertimos JSON a Python.
        passports = json.load(file)
        #print("#########passports",passports)
    # Regresamos la lista.
    return passports


# ------------------------------------------------------------
# 4. GENERAR MRZ PARA UN PASAPORTE
# ------------------------------------------------------------

def generate_passport_mrz(passport):

    # Llamamos a la lógica central.
    line1, line2 = generate_td3_mrz(

        issuing_country=
            passport["issuing_country"],

        surname=
            passport["surname"],

        given_names=
            passport["given_names"],

        passport_number=
            passport["passport_number"],

        nationality=
            passport["nationality"],

        birth_date=
            passport["birth_date"],

        sex=
            passport["sex"],

        expiration_date=
            passport["expiration_date"],
    )

    # Regresamos ambas líneas.
    return line1, line2


# ------------------------------------------------------------
# 5. MOSTRAR RESULTADOS EN CONSOLA
# ------------------------------------------------------------

def generate_all_passports(passports):

    # Recorremos todos los escenarios.
    for passport in passports:

        # Generamos MRZ.
        line1, line2 = generate_passport_mrz(
            passport
        )

        # Validamos MRZ.
        validation = validate_td3_mrz(
            line1,
            line2
        )

        # Separador visual.
        print("=" * 60)

        # ID.
        print(
            "Test ID:",
            passport["id"]
        )

        # País.
        print(
            "Country:",
            passport["country"]
        )

        print()

        # Línea 1.
        print("MRZ Line 1:")
        print(line1)

        print()

        # Línea 2.
        print("MRZ Line 2:")
        print(line2)

        print()

        # Longitudes.
        print(
            "Length line 1:",
            len(line1)
        )

        print(
            "Length line 2:",
            len(line2)
        )

        print()

        # ----------------------------------------------------
        # RESULTADOS DE VALIDACIÓN
        # ----------------------------------------------------

        print("Validation:")

        print(
            "Line 1 length valid:",
            validation[
                "line1_length_valid"
            ]
        )

        print(
            "Line 2 length valid:",
            validation[
                "line2_length_valid"
            ]
        )

        print(
            "Passport check valid:",
            validation[
                "passport_check_valid"
            ]
        )

        print(
            "Birth check valid:",
            validation[
                "birth_check_valid"
            ]
        )

        print(
            "Expiration check valid:",
            validation[
                "expiration_check_valid"
            ]
        )

        print(
            "Personal check valid:",
            validation[
                "personal_check_valid"
            ]
        )

        print(
            "Composite check valid:",
            validation[
                "composite_check_valid"
            ]
        )

        print(
            "MRZ VALID:",
            validation[
                "mrz_valid"
            ]
        )

        print()


# ------------------------------------------------------------
# 6. CONSTRUIR EXPECTED RESULTS
# ------------------------------------------------------------

def build_expected_results(passports):

    # Lista vacía donde almacenaremos
    # los resultados finales.
    results = []

    # Recorremos cada pasaporte.
    for passport in passports:

        # Generamos las líneas MRZ.
        line1, line2 = generate_passport_mrz(
            passport
        )

        # Validamos la MRZ.
        validation = validate_td3_mrz(
            line1,
            line2
        )


        # ----------------------------------------------------
        # CREAR RESULTADO
        # ----------------------------------------------------

        result = {

            # ID interno.
            "id":
                passport["id"],

            # País descriptivo.
            "country":
                passport["country"],

            # País emisor.
            "issuing_country":
                passport[
                    "issuing_country"
                ],

            # Nacionalidad.
            "nationality":
                passport[
                    "nationality"
                ],

            # Apellido.
            "surname":
                passport["surname"],

            # Nombres.
            "given_names":
                passport[
                    "given_names"
                ],

            # Número.
            "passport_number":
                passport[
                    "passport_number"
                ],

            # Fecha nacimiento.
            "birth_date":
                passport[
                    "birth_date"
                ],

            # Sexo.
            "sex":
                passport["sex"],

            # Fecha expiración.
            "expiration_date":
                passport[
                    "expiration_date"
                ],


            # ------------------------------------------------
            # MRZ
            # ------------------------------------------------

            "mrz": {

                "line1":
                    line1,

                "line2":
                    line2
            },


            # ------------------------------------------------
            # EXPECTED
            # ------------------------------------------------

            "expected": {

                # Longitud real.
                "line1_length":
                    len(line1),

                "line2_length":
                    len(line2),

                # Validación simple de longitud.
                "valid_td3_length": (
                    len(line1) == 44
                    and
                    len(line2) == 44
                ),

                # Validación de línea 1.
                "line1_length_valid":
                    validation[
                        "line1_length_valid"
                    ],

                # Validación de línea 2.
                "line2_length_valid":
                    validation[
                        "line2_length_valid"
                    ],

                # Check digit del pasaporte.
                "passport_check_valid":
                    validation[
                        "passport_check_valid"
                    ],

                # Check digit de nacimiento.
                "birth_check_valid":
                    validation[
                        "birth_check_valid"
                    ],

                # Check digit de expiración.
                "expiration_check_valid":
                    validation[
                        "expiration_check_valid"
                    ],

                # Check digit de optional data.
                "personal_check_valid":
                    validation[
                        "personal_check_valid"
                    ],

                # Check digit compuesto.
                "composite_check_valid":
                    validation[
                        "composite_check_valid"
                    ],

                # Resultado final.
                "mrz_valid":
                    validation[
                        "mrz_valid"
                    ]
            }
        }

        # Agregamos el resultado
        # a la lista.
        results.append(
            result
        )

    # Regresamos la lista completa.
    return results


# ------------------------------------------------------------
# 7. GUARDAR EXPECTED RESULTS
# ------------------------------------------------------------

def save_expected_results(results):

    # Creamos output/ si por alguna razón
    # todavía no existe.
    EXPECTED_RESULTS_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    # Abrimos archivo en modo escritura.
    with open(
        EXPECTED_RESULTS_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        # Convertimos Python -> JSON.
        json.dump(
            results,
            file,
            indent=4,
            ensure_ascii=False
        )

    # Confirmación.
    print("=" * 60)

    print(
        "Expected results saved in:"
    )

    print(
        EXPECTED_RESULTS_FILE
    )


# ------------------------------------------------------------
# 8. MAIN
# ------------------------------------------------------------

def main():

    # Paso 1:
    # cargar escenarios.
    passports = load_passports()

    # Paso 2:
    # generar y validar en consola.
    generate_all_passports(
        passports
    )

    # Paso 3:
    # construir resultado esperado.
    expected_results = (
        build_expected_results(
            passports
        )
    )

    # Paso 4:
    # guardar JSON.
    save_expected_results(
        expected_results
    )


# ------------------------------------------------------------
# 9. PUNTO DE ENTRADA
# ------------------------------------------------------------

if __name__ == "__main__":

    # Ejecutamos main().
    main()