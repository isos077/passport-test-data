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
# Si el build no logra descargar mscorefonts (por ejemplo si un
# mirror de SourceForge falla), la app sigue funcionando: cae al
# respaldo Liberation Sans/Mono ya incluido en app/fonts/. Ver el
# log "[fonts] ..." al iniciar el servicio en Render para confirmar
# cual fuente se esta usando realmente.
# ============================================================

FROM python:3.12-slim

# Evita prompts interactivos de debconf durante el build.
ENV DEBIAN_FRONTEND=noninteractive

# 1) ttf-mscorefonts-installer NO esta en el componente "main" de
#    Debian (esta en "contrib", porque descarga contenido con
#    licencia de Microsoft). La imagen base python:3.12-slim solo
#    trae "main" habilitado, asi que sin este paso "apt-get install
#    ttf-mscorefonts-installer" falla de inmediato con "Unable to
#    locate package" (esto fue justo lo que paso en el primer
#    intento de deploy: 5 fallos casi instantaneos, no por mirrors
#    caidos sino porque el paquete ni se encontraba).
RUN if [ -f /etc/apt/sources.list.d/debian.sources ]; then \
        sed -i 's/^Components: main$/Components: main contrib/' /etc/apt/sources.list.d/debian.sources; \
    fi; \
    if [ -f /etc/apt/sources.list ]; then \
        sed -i -E '/^deb[ \t]/{/contrib/!s/$/ contrib/}' /etc/apt/sources.list; \
    fi

# 2) Aceptamos de antemano la EULA de Microsoft para
#    ttf-mscorefonts-installer (equivalente a aceptarla a mano
#    con dpkg-reconfigure, pero de forma no interactiva).
RUN echo "ttf-mscorefonts-installer msttcorefonts/accepted-mscorefonts-eula select true" \
    | debconf-set-selections

# 3) Instalamos las fuentes reales de Microsoft. Una vez que el
#    paquete SI se encuentra (paso 1), el propio instalador descarga
#    los archivos originales desde mirrors de SourceForge, que a
#    veces fallan de forma intermitente por red, por eso reintentamos
#    varias veces. Si aun asi falla, NO se detiene el build (el
#    resultado del bloque completo es exitoso de todas formas):
#    la app ya tiene el respaldo Liberation para no dejar el
#    despliegue roto por un mirror caido.
#    "apt-cache policy" antes de instalar queda en el log del build
#    como diagnostico: si dice "Candidate: (none)" el paquete sigue
#    sin encontrarse (revisar el paso 1); si muestra una version,
#    el problema (si persiste) es la descarga, no la ubicacion.
RUN apt-get update && \
    apt-get install -y --no-install-recommends wget cabextract && \
    apt-cache policy ttf-mscorefonts-installer && \
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
