# Pipeline de ingesta y limpieza de datos

Pre-entrega de Data Science II. El proyecto implementa un pipeline ETL modular que descarga un dataset público, aplica reglas de calidad y genera un archivo Parquet listo para análisis o Machine Learning.

## Fuente de datos

Se utiliza el dataset **Titanic** mantenido por el repositorio público `seaborn-data`:

- CSV directo: <https://raw.githubusercontent.com/mwaskom/seaborn-data/master/titanic.csv>
- Repositorio de la fuente: <https://github.com/mwaskom/seaborn-data>

El CSV original no se versiona para mantener el repositorio liviano. Cada ejecución lo descarga nuevamente en `data/raw/`, carpeta excluida mediante `.gitignore`.

## Estructura

```text
.
├── main.py
├── requirements.txt
├── src/
│   ├── __init__.py
│   ├── pipeline.py
│   └── transformations.py
└── data/
    ├── raw/                    # CSV descargado; no se sube a GitHub
    └── processed/
        ├── titanic_clean.parquet
        └── quality_report.json
```

## Instalación

Requisitos: Python 3.10 o superior y Git.

```bash
git clone https://github.com/Matukp/preentrega-pipeline-etl.git
cd preentrega-pipeline-etl
python -m venv .venv
```

Activación en Windows:

```powershell
.venv\Scripts\Activate.ps1
```

Activación en macOS o Linux:

```bash
source .venv/bin/activate
```

Instalar dependencias:

```bash
python -m pip install -r requirements.txt
```

## Ejecución

```bash
python main.py
```

Al terminar se generan:

- `data/processed/titanic_clean.parquet`: dataset limpio y tipado.
- `data/processed/quality_report.json`: métricas de filas, nulos, duplicados y memoria.

Los parámetros pueden cambiarse desde la línea de comandos:

```bash
python main.py --source-url URL --raw-path data/raw/source.csv --output-path data/processed/output.parquet
```

## Etapas del pipeline

### 1. Extracción

`src/pipeline.py` descarga el CSV mediante una petición HTTP con timeout y validación del código de respuesta. Luego Pandas lo lee con tipos explícitos (`int8`, `float32`, `boolean` y `category`) para reducir el consumo de memoria.

### 2. Transformación

La función independiente `clean_titanic()` de `src/transformations.py`:

1. normaliza nombres de columnas a `snake_case`;
2. elimina filas completamente duplicadas antes y después de la imputación;
3. descarta registros sin variable objetivo (`survived`);
4. imputa `age` con la mediana del grupo `pclass` + `sex` y una mediana global de respaldo;
5. imputa `fare` con su mediana;
6. completa variables categóricas con la moda o `Unknown`;
7. crea `family_size` e `is_child`;
8. optimiza los tipos y valida que no queden nulos.

La mediana se usa en variables numéricas porque es menos sensible a valores extremos. La moda conserva una categoría existente en campos como el puerto de embarque, mientras que `Unknown` evita inventar una cubierta específica.

### 3. Carga

El resultado se escribe como Parquet con el motor PyArrow y compresión Snappy. Parquet es más eficiente que CSV para Machine Learning porque:

- almacena los datos por columnas;
- conserva los tipos de datos;
- admite compresión eficiente;
- permite leer solo las columnas necesarias;
- suele reducir tiempo de lectura y espacio en disco.

## Controles de calidad

La ejecución verificada del proyecto comprueba que:

- el Parquet se puede leer nuevamente;
- no quedan valores nulos;
- no quedan duplicados exactos;
- las columnas calculadas existen;
- los tipos optimizados se conservan.

El detalle numérico de cada ejecución queda registrado en `data/processed/quality_report.json`.

En la ejecución incluida en este repositorio se procesaron 891 filas, se eliminaron 114 duplicados, se obtuvieron 777 registros finales y el resultado quedó con 0 valores nulos y 0 duplicados exactos.
