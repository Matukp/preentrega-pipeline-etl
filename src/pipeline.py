"""Funciones de extracción, transformación y carga del pipeline."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
import requests

from .transformations import clean_titanic

DEFAULT_SOURCE_URL = (
    "https://raw.githubusercontent.com/mwaskom/seaborn-data/master/titanic.csv"
)

SOURCE_DTYPES: dict[str, str] = {
    "survived": "int8",
    "pclass": "int8",
    "sex": "category",
    "age": "float32",
    "sibsp": "int8",
    "parch": "int8",
    "fare": "float32",
    "embarked": "category",
    "class": "category",
    "who": "category",
    "adult_male": "boolean",
    "deck": "category",
    "embark_town": "category",
    "alive": "category",
    "alone": "boolean",
}


def download_source(source_url: str, destination: Path) -> Path:
    """Descarga el CSV y deja un mensaje claro ante errores de red o HTTP."""

    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")

    try:
        response = requests.get(source_url, timeout=30)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise RuntimeError(f"No se pudo descargar la fuente: {exc}") from exc

    temporary.write_bytes(response.content)
    temporary.replace(destination)
    return destination


def extract_data(source_url: str, raw_path: Path) -> pd.DataFrame:
    """Extrae el CSV público y aplica tipos explícitos para ahorrar memoria."""

    source_path = download_source(source_url, raw_path)
    return pd.read_csv(source_path, dtype=SOURCE_DTYPES, low_memory=False)


def load_parquet(data: pd.DataFrame, output_path: Path) -> None:
    """Carga el resultado en Parquet con compresión Snappy."""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = output_path.with_suffix(".tmp.parquet")
    data.to_parquet(
        temporary,
        engine="pyarrow",
        compression="snappy",
        index=False,
    )
    temporary.replace(output_path)


def save_quality_report(report: dict[str, Any], report_path: Path) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = report_path.with_suffix(".tmp.json")
    temporary.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(report_path)


def run_pipeline(
    source_url: str,
    raw_path: Path,
    output_path: Path,
    report_path: Path,
) -> dict[str, Any]:
    """Orquesta las etapas de extracción, transformación y carga."""

    raw_data = extract_data(source_url, raw_path)
    clean_data, report = clean_titanic(raw_data)
    load_parquet(clean_data, output_path)
    save_quality_report(report, report_path)
    return report
