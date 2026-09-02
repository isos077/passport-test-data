# ============================================================
# PASSPORT TEST DATA GENERATOR
# Archivo: app/mrz.py
#
# Objetivo:
# Generar y validar una MRZ TD3 para documentos sintéticos.
#
# Una MRZ TD3 tiene:
# - 2 líneas
# - 44 caracteres por línea
# - Check digits definidos por ICAO
# ============================================================


# ------------------------------------------------------------
# 1. PESOS PARA CALCULAR CHECK DIGITS
# ------------------------------------------------------------

# ICAO utiliza el patrón:
#
# 7, 3, 1, 7, 3, 1...
#
# durante el cálculo de los check digits.
WEIGHTS = [7, 3, 1]


# ------------------------------------------------------------
# 2. VALORES NUMÉRICOS DE LOS CARACTERES MRZ
# ------------------------------------------------------------

# Cada carácter permitido dentro de la MRZ
# necesita un valor numérico.
CHAR_VALUES = {

    # Números:
    #
    # "0" = 0
    # "1" = 1
    # ...
    # "9" = 9
    **{str(i): i for i in range(10)},

    # Letras:
    #
    # A = 10
    # B = 11
    # ...
    # Z = 35
    **{chr(ord("A") + i): 10 + i for i in range(26)},

    # El símbolo "<" funciona como filler.
    #
    # Para los cálculos tiene valor 0.
    "<": 0
}


# ------------------------------------------------------------
# 3. CALCULAR CHECK DIGIT
# ------------------------------------------------------------

def calculate_check_digit(value: str) -> str:

    # Variable donde acumularemos
    # todas las multiplicaciones.
    total = 0

    # enumerate() nos permite obtener:
    #
    # index -> posición
    # char  -> carácter
    for index, char in enumerate(value):

        # Convertimos el carácter
        # en su valor numérico.
        char_value = CHAR_VALUES[char]

        # Elegimos el peso correspondiente:
        #
        # index 0 -> 7
        # index 1 -> 3
        # index 2 -> 1
        # index 3 -> 7
        #
        # y así sucesivamente.
        weight = WEIGHTS[index % 3]

        # Multiplicamos:
        #
        # valor del carácter × peso
        #
        # y lo acumulamos.
        total += char_value * weight

    # El check digit es el módulo 10
    # del resultado total.
    return str(total % 10)


# ------------------------------------------------------------
# 4. NORMALIZAR TEXTO
# ------------------------------------------------------------

def normalize_text(value: str) -> str:

    # Convertimos todo a mayúsculas.
    value = value.upper()

    # Reemplazamos espacios por "<".
    value = value.replace(" ", "<")

    # Devolvemos el texto.
    return value


# ------------------------------------------------------------
# 5. COMPLETAR CAMPOS
# ------------------------------------------------------------

def pad(value: str, length: int) -> str:

    # Cortamos el texto si supera
    # la longitud permitida.
    value = value[:length]

    # Completamos por la derecha con "<"
    # hasta alcanzar la longitud requerida.
    value = value.ljust(length, "<")

    # Devolvemos el resultado.
    return value


# ------------------------------------------------------------
# 6. GENERAR MRZ TD3
# ------------------------------------------------------------

def generate_td3_mrz(
    issuing_country: str,
    surname: str,
    given_names: str,
    passport_number: str,
    nationality: str,
    birth_date: str,
    sex: str,
    expiration_date: str,
):

    # Normalizamos códigos de país.
    issuing_country = issuing_country.upper()
    nationality = nationality.upper()

    # Normalizamos sexo.
    sex = sex.upper()

    # Normalizamos apellido.
    surname = normalize_text(surname)

    # Normalizamos nombres.
    given_names = normalize_text(given_names)


    # ========================================================
    # LÍNEA 1
    # ========================================================

    # La estructura del nombre dentro de MRZ es:
    #
    # APELLIDO<<NOMBRES
    name_field = f"{surname}<<{given_names}"

    # Línea 1:
    #
    # P<
    # país emisor
    # nombre
    line1 = (
        "P<"
        + issuing_country
        + pad(name_field, 39)
    )


    # ========================================================
    # LÍNEA 2
    # ========================================================

    # El número de pasaporte ocupa 9 caracteres.
    passport_field = pad(
        passport_number.upper(),
        9
    )

    # Calculamos su check digit.
    passport_check = calculate_check_digit(
        passport_field
    )

    # Check digit de fecha de nacimiento.
    birth_check = calculate_check_digit(
        birth_date
    )

    # Check digit de fecha de expiración.
    expiration_check = calculate_check_digit(
        expiration_date
    )

    # Campo optional data / personal number.
    #
    # Para nuestro test utilizamos 14 fillers.
    personal_number = "<" * 14

    # Check digit de optional data.
    personal_check = calculate_check_digit(
        personal_number
    )

    # Construimos la línea 2
    # todavía sin el último check digit.
    line2_without_final_check = (
        passport_field
        + passport_check
        + nationality
        + birth_date
        + birth_check
        + sex
        + expiration_date
        + expiration_check
        + personal_number
        + personal_check
    )


    # --------------------------------------------------------
    # CHECK DIGIT COMPUESTO
    # --------------------------------------------------------

    # El check digit final utiliza
    # determinados segmentos de la línea 2.
    composite_data = (
        line2_without_final_check[0:10]
        + line2_without_final_check[13:20]
        + line2_without_final_check[21:43]
    )

    # Calculamos el check digit final.
    final_check = calculate_check_digit(
        composite_data
    )

    # Completamos la línea 2.
    line2 = (
        line2_without_final_check
        + final_check
    )

    # Regresamos ambas líneas.
    return line1, line2


# ------------------------------------------------------------
# 7. VALIDAR MRZ TD3
# ------------------------------------------------------------

def validate_td3_mrz(line1: str, line2: str) -> dict:

    # --------------------------------------------------------
    # VALIDAR LONGITUD
    # --------------------------------------------------------

    # Cada línea TD3 debe tener exactamente
    # 44 caracteres.
    line1_length_valid = len(line1) == 44
    line2_length_valid = len(line2) == 44


    # --------------------------------------------------------
    # VALIDACIÓN DEFENSIVA
    # --------------------------------------------------------

    # Si la línea 2 no tiene 44 caracteres,
    # no podemos acceder de forma segura a
    # todas las posiciones esperadas.
    #
    # Regresamos inmediatamente un resultado inválido.
    if not line2_length_valid:

        return {
            "line1_length_valid": line1_length_valid,
            "line2_length_valid": line2_length_valid,
            "passport_check_valid": False,
            "birth_check_valid": False,
            "expiration_check_valid": False,
            "personal_check_valid": False,
            "composite_check_valid": False,
            "mrz_valid": False
        }


    # --------------------------------------------------------
    # EXTRAER NÚMERO DE PASAPORTE
    # --------------------------------------------------------

    # Posiciones 0 hasta 8.
    passport_number = line2[0:9]

    # Posición 9.
    passport_check_digit = line2[9]


    # --------------------------------------------------------
    # EXTRAER FECHA DE NACIMIENTO
    # --------------------------------------------------------

    # Posiciones 13 hasta 18.
    birth_date = line2[13:19]

    # Posición 19.
    birth_check_digit = line2[19]


    # --------------------------------------------------------
    # EXTRAER FECHA DE EXPIRACIÓN
    # --------------------------------------------------------

    # Posiciones 21 hasta 26.
    expiration_date = line2[21:27]

    # Posición 27.
    expiration_check_digit = line2[27]


    # --------------------------------------------------------
    # EXTRAER OPTIONAL DATA
    # --------------------------------------------------------

    # Posiciones 28 hasta 41.
    personal_number = line2[28:42]

    # Posición 42.
    personal_check_digit = line2[42]


    # --------------------------------------------------------
    # EXTRAER CHECK DIGIT FINAL
    # --------------------------------------------------------

    # Posición 43.
    composite_check_digit = line2[43]


    # --------------------------------------------------------
    # RECALCULAR CHECK DIGIT DEL PASAPORTE
    # --------------------------------------------------------

    expected_passport_check = calculate_check_digit(
        passport_number
    )


    # --------------------------------------------------------
    # RECALCULAR CHECK DIGIT DE NACIMIENTO
    # --------------------------------------------------------

    expected_birth_check = calculate_check_digit(
        birth_date
    )


    # --------------------------------------------------------
    # RECALCULAR CHECK DIGIT DE EXPIRACIÓN
    # --------------------------------------------------------

    expected_expiration_check = calculate_check_digit(
        expiration_date
    )


    # --------------------------------------------------------
    # RECALCULAR CHECK DIGIT DE OPTIONAL DATA
    # --------------------------------------------------------

    expected_personal_check = calculate_check_digit(
        personal_number
    )


    # --------------------------------------------------------
    # RECALCULAR CHECK DIGIT COMPUESTO
    # --------------------------------------------------------

    composite_data = (
        line2[0:10]
        + line2[13:20]
        + line2[21:43]
    )

    expected_composite_check = calculate_check_digit(
        composite_data
    )


    # --------------------------------------------------------
    # COMPARAR CHECK DIGITS
    # --------------------------------------------------------

    passport_check_valid = (
        passport_check_digit
        == expected_passport_check
    )

    birth_check_valid = (
        birth_check_digit
        == expected_birth_check
    )

    expiration_check_valid = (
        expiration_check_digit
        == expected_expiration_check
    )

    personal_check_valid = (
        personal_check_digit
        == expected_personal_check
    )

    composite_check_valid = (
        composite_check_digit
        == expected_composite_check
    )


    # --------------------------------------------------------
    # VALIDACIÓN GENERAL
    # --------------------------------------------------------

    # all() devuelve True únicamente
    # si TODOS los valores son True.
    mrz_valid = all([
        line1_length_valid,
        line2_length_valid,
        passport_check_valid,
        birth_check_valid,
        expiration_check_valid,
        personal_check_valid,
        composite_check_valid
    ])


    # --------------------------------------------------------
    # REGRESAR RESULTADOS
    # --------------------------------------------------------

    return {

        "line1_length_valid":
            line1_length_valid,

        "line2_length_valid":
            line2_length_valid,

        "passport_check_valid":
            passport_check_valid,

        "birth_check_valid":
            birth_check_valid,

        "expiration_check_valid":
            expiration_check_valid,

        "personal_check_valid":
            personal_check_valid,

        "composite_check_valid":
            composite_check_valid,

        "mrz_valid":
            mrz_valid
    }


# ------------------------------------------------------------
# 8. PRUEBA DIRECTA
# ------------------------------------------------------------

if __name__ == "__main__":

    # Generamos un ejemplo mexicano.
    line1, line2 = generate_td3_mrz(
        issuing_country="MEX",
        surname="GARCIA",
        given_names="MARIA ELENA",
        passport_number="X1234567",
        nationality="MEX",
        birth_date="920417",
        sex="F",
        expiration_date="310920",
    )

    # Mostramos las líneas.
    print(line1)
    print(line2)

    # Mostramos sus longitudes.
    print()
    print(
        "Length line 1:",
        len(line1)
    )

    print(
        "Length line 2:",
        len(line2)
    )

    # Ejecutamos el validador.
    validation = validate_td3_mrz(
        line1,
        line2
    )

    # Mostramos los resultados.
    print()
    print("Validation:")

    for key, value in validation.items():
        print(
            key,
            "=",
            value
        )