"""Transformaciones reutilizables para la limpieza del dataset."""

from __future__ import annotations

import re
from collections.abc import Iterable
from typing import Any

import pandas as pd


def normalize_column_names(columns: Iterable[object]) -> list[str]:
    """Convierte nombres de columnas a snake_case consistente."""

    normalized: list[str] = []
    for column in columns:
        name = str(column).strip().lower()
        name = re.sub(r"[^a-z0-9]+", "_", name)
        normalized.append(re.sub(r"_+", "_", name).strip("_"))
    return normalized


def _fill_mode(series: pd.Series, fallback: str = "Unknown") -> pd.Series:
    """Imputa una serie categórica con su moda o un valor de respaldo."""

    mode = series.mode(dropna=True)
    replacement = str(mode.iloc[0]) if not mode.empty else fallback
    return series.astype("string").fillna(replacement)


def optimize_dtypes(data: pd.DataFrame) -> pd.DataFrame:
    """Reduce el uso de memoria conservando tipos adecuados."""

    result = data.copy()
    integer_columns = ["survived", "pclass", "sibsp", "parch", "family_size"]
    float_columns = ["age", "fare"]
    category_columns = [
        "sex",
        "embarked",
        "class",
        "who",
        "deck",
        "embark_town",
        "alive",
    ]
    boolean_columns = ["adult_male", "alone", "is_child"]

    for column in integer_columns:
        if column in result:
            result[column] = pd.to_numeric(result[column], errors="raise").astype("int8")
    for column in float_columns:
        if column in result:
            result[column] = pd.to_numeric(result[column], errors="raise").astype("float32")
    for column in category_columns:
        if column in result:
            result[column] = result[column].astype("category")
    for column in boolean_columns:
        if column in result:
            result[column] = result[column].astype("bool")

    return result


def clean_titanic(data: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Elimina duplicados, imputa nulos y agrega variables útiles."""

    cleaned = data.copy()
    memory_before = int(cleaned.memory_usage(deep=True).sum())
    rows_input = int(len(cleaned))
    nulls_input = int(cleaned.isna().sum().sum())

    cleaned.columns = normalize_column_names(cleaned.columns)
    required = {"survived", "pclass", "sex", "age", "sibsp", "parch", "fare"}
    missing = required.difference(cleaned.columns)
    if missing:
        raise ValueError(f"Faltan columnas requeridas: {', '.join(sorted(missing))}")

    duplicates_before_cleaning = int(cleaned.duplicated().sum())
    cleaned = cleaned.drop_duplicates().copy()
    cleaned = cleaned.dropna(subset=["survived"])

    grouped_age = cleaned.groupby(["pclass", "sex"], observed=True)["age"].transform(
        "median"
    )
    cleaned["age"] = cleaned["age"].fillna(grouped_age)
    cleaned["age"] = cleaned["age"].fillna(cleaned["age"].median())
    cleaned["fare"] = cleaned["fare"].fillna(cleaned["fare"].median())

    for column in ("embarked", "embark_town"):
        if column in cleaned:
            cleaned[column] = _fill_mode(cleaned[column])

    if "deck" in cleaned:
        cleaned["deck"] = cleaned["deck"].astype("string").fillna("Unknown")

    # Respaldo defensivo para futuros cambios en la fuente pública.
    text_columns = cleaned.select_dtypes(include=["object", "string", "category"]).columns
    for column in text_columns:
        if cleaned[column].isna().any():
            cleaned[column] = cleaned[column].astype("string").fillna("Unknown")

    numeric_columns = cleaned.select_dtypes(include="number").columns
    for column in numeric_columns:
        if column != "survived" and cleaned[column].isna().any():
            cleaned[column] = cleaned[column].fillna(cleaned[column].median())

    cleaned["family_size"] = cleaned["sibsp"] + cleaned["parch"] + 1
    cleaned["is_child"] = cleaned["age"] < 18
    cleaned = optimize_dtypes(cleaned)

    # La imputación puede volver idénticas filas que antes diferían solo por un nulo.
    duplicates_after_imputation = int(cleaned.duplicated().sum())
    cleaned = cleaned.drop_duplicates().reset_index(drop=True)

    nulls_output = int(cleaned.isna().sum().sum())
    if nulls_output != 0:
        columns_with_nulls = cleaned.columns[cleaned.isna().any()].tolist()
        raise ValueError(f"Persisten valores nulos en: {columns_with_nulls}")

    report: dict[str, Any] = {
        "rows_input": rows_input,
        "rows_output": int(len(cleaned)),
        "duplicates_removed": duplicates_before_cleaning + duplicates_after_imputation,
        "duplicates_removed_before_imputation": duplicates_before_cleaning,
        "duplicates_removed_after_imputation": duplicates_after_imputation,
        "nulls_input": nulls_input,
        "nulls_output": nulls_output,
        "nulls_imputed_or_removed": nulls_input - nulls_output,
        "columns_output": int(len(cleaned.columns)),
        "memory_bytes_input": memory_before,
        "memory_bytes_output": int(cleaned.memory_usage(deep=True).sum()),
    }
    return cleaned, report
