from __future__ import annotations

import csv
from pathlib import Path
from typing import Mapping

from .audit import ProductRecord
from .catalog import CatalogImportError


_PLATFORM_ALIASES: dict[str, dict[str, tuple[str, ...]]] = {
    "shopify": {
        "name": ("Title",),
        "slug": ("Handle",),
        "meta_title": ("SEO Title",),
        "meta_description": ("SEO Description",),
        "description": ("Body (HTML)",),
        "brand": ("Vendor",),
        "category": ("Product Category", "Type"),
    },
    "ikas": {
        "name": ("name", "productName", "Ürün Adı", "Urun Adi"),
        "slug": ("slug", "seoSlug", "URL", "Seo URL"),
        "meta_title": ("metaTitle", "seoTitle", "Meta Başlık", "Meta Baslik"),
        "meta_description": (
            "metaDescription",
            "seoDescription",
            "Meta Açıklama",
            "Meta Aciklama",
        ),
        "description": ("description", "Açıklama", "Aciklama"),
        "brand": ("brand", "brandName", "Marka"),
        "category": ("category", "categoryName", "Kategori"),
    },
}


def _normalized_header(value: str) -> str:
    return " ".join(value.strip().split()).casefold()


def _resolve_columns(
    fieldnames: tuple[str, ...],
    aliases: Mapping[str, tuple[str, ...]],
) -> dict[str, str]:
    available = {_normalized_header(name): name for name in fieldnames}
    resolved: dict[str, str] = {}
    missing: list[str] = []

    for target, candidates in aliases.items():
        source = next(
            (available[_normalized_header(candidate)] for candidate in candidates if _normalized_header(candidate) in available),
            None,
        )
        if source is None:
            missing.append(target)
        else:
            resolved[target] = source

    if missing:
        raise CatalogImportError(
            "Platform dışa aktarımında eşlenemeyen alanlar: " + ", ".join(sorted(missing))
        )
    return resolved


def read_platform_catalog_csv(
    path: str | Path,
    platform: str,
) -> tuple[ProductRecord, ...]:
    """Read a Shopify or İkas CSV export into the stable ProductRecord schema."""
    platform_key = platform.strip().casefold()
    try:
        aliases = _PLATFORM_ALIASES[platform_key]
    except KeyError as exc:
        supported = ", ".join(sorted(_PLATFORM_ALIASES))
        raise CatalogImportError(
            f"Desteklenmeyen platform: {platform}. Desteklenenler: {supported}"
        ) from exc

    csv_path = Path(path)
    try:
        handle = csv_path.open("r", encoding="utf-8-sig", newline="")
    except OSError as exc:
        raise CatalogImportError(f"Katalog dosyası açılamadı: {csv_path}") from exc

    with handle:
        reader = csv.DictReader(handle)
        fieldnames = tuple(reader.fieldnames or ())
        if not fieldnames:
            raise CatalogImportError("Platform dışa aktarımında başlık satırı bulunamadı.")
        columns = _resolve_columns(fieldnames, aliases)

        products: list[ProductRecord] = []
        for row in reader:
            if not any((value or "").strip() for value in row.values()):
                continue
            products.append(
                ProductRecord(
                    name=(row.get(columns["name"]) or "").strip(),
                    slug=(row.get(columns["slug"]) or "").strip(),
                    meta_title=(row.get(columns["meta_title"]) or "").strip(),
                    meta_description=(row.get(columns["meta_description"]) or "").strip(),
                    description=(row.get(columns["description"]) or "").strip(),
                    brand=(row.get(columns["brand"]) or "").strip(),
                    category=(row.get(columns["category"]) or "").strip(),
                )
            )

    return tuple(products)
