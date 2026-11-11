"""Punto de entrada del pipeline ETL."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from src.pipeline import DEFAULT_SOURCE_URL, run_pipeline


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Descarga, limpia y exporta el dataset Titanic a Parquet."
    )
    parser.add_argument("--source-url", default=DEFAULT_SOURCE_URL)
    parser.add_argument("--raw-path", type=Path, default=Path("data/raw/titanic.csv"))
    parser.add_argument(
        "--output-path",
        type=Path,
        default=Path("data/processed/titanic_clean.parquet"),
    )
    parser.add_argument(
        "--report-path",
        type=Path,
        default=Path("data/processed/quality_report.json"),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")

    try:
        report = run_pipeline(
            source_url=args.source_url,
            raw_path=args.raw_path,
            output_path=args.output_path,
            report_path=args.report_path,
        )
    except Exception as exc:  # El mensaje queda claro para una ejecución por consola.
        logging.error("El pipeline no pudo completarse: %s", exc)
        return 1

    logging.info("Pipeline finalizado correctamente.")
    logging.info("Filas de entrada: %s", report["rows_input"])
    logging.info("Duplicados eliminados: %s", report["duplicates_removed"])
    logging.info("Valores nulos de salida: %s", report["nulls_output"])
    logging.info("Archivo generado: %s", args.output_path.resolve())
    return 0


if __name__ == "__main__":
    sys.exit(main())
