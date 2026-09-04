# ============================================================
# Dockerfile - Passport Test Data Generator
#
# Por que Docker (en vez del runtime nativo "python" de Render):
# el runtime nativo no permite instalar paquetes del sistema
# operativo (apt-get) durante el build. Necesitamos eso para
# instalar las fuentes REALES de Microsoft (Arial, Courier New)
# via el paquete oficial de Debian "ttf-mscorefonts-installer".
#
# Por que esto y no copiar los .ttf de macOS al repo:
# Arial y Courier New tienen licencia de Apple/Monotype y no se
# pueden redistribuir copiando los archivos del Mac a un repo de
# git. "ttf-mscorefonts-installer" es el mecanismo legitimo: en
# build time descarga los instaladores .exe originales publicados
# por Microsoft bajo su propia EULA ("Core Fonts for the Web") y
# los convierte a TrueType. Es la misma fuente real de Windows/
# macOS, no una alternativa parecida (como Liberation).
#
# Si el build no logra descargar mscorefonts (los mirrors de
# SourceForge a veces fallan), la app sigue funcionando: cae al
# respaldo Liberation Sans/Mono ya incluido en app/fonts/. Ver el
# log "[fonts] ..." al iniciar el servicio en Render para confirmar
# cual fuente se esta usando realmente.
# ============================================================

FROM python:3.12-slim

# Evita prompts interactivos de debconf durante el build.
ENV DEBIAN_FRONTEND=noninteractive

# 1) Aceptamos de antemano la EULA de Microsoft para
#    ttf-mscorefonts-installer (equivalente a aceptarla a mano
#    con dpkg-reconfigure, pero de forma no interactiva).
RUN echo "ttf-mscorefonts-installer msttcorefonts/accepted-mscorefonts-eula select true" \
    | debconf-set-selections

# 2) Instalamos las fuentes reales de Microsoft. El paquete
#    descarga los archivos originales desde mirrors de SourceForge,
#    que a veces fallan de forma intermitente, por eso reintentamos
#    varias veces. Si aun asi falla, NO se detiene el build (el
#    resultado del bloque completo es exitoso de todas formas):
#    la app ya tiene el respaldo Liberation para no dejar el
#    despliegue roto por un mirror caido.
RUN apt-get update && \
    apt-get install -y --no-install-recommends wget cabextract && \
    ( \
        for i in 1 2 3 4 5; do \
            apt-get install -y --no-install-recommends ttf-mscorefonts-installer && break; \
            echo "[fonts] intento $i de instalar ttf-mscorefonts-installer fallo, reintentando en 5s..."; \
            sleep 5; \
        done \
    ); \
    fc-cache -f >/dev/null 2>&1 || true; \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copiamos requirements primero para aprovechar la cache de Docker.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos el resto del proyecto.
COPY . .

EXPOSE 8000

# Render define $PORT en tiempo de ejecucion.
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
