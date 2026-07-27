from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from .audit import ProductRecord
from .catalog import CatalogAuditItem, CatalogAuditReport


@dataclass(frozen=True, slots=True)
class FieldSuggestion:
    field: str
    current_value: str
    suggested_value: str
    rationale: str
    auto_apply_safe: bool = False


@dataclass(frozen=True, slots=True)
class ProductSuggestion:
    row_number: int
    name: str
    slug: str
    score: int
    suggestions: tuple[FieldSuggestion, ...]


def _clean(value: str) -> str:
    return " ".join((value or "").split())


def _truncate(value: str, limit: int) -> str:
    value = _clean(value)
    if len(value) <= limit:
        return value
    shortened = value[: limit + 1].rsplit(" ", 1)[0].rstrip(" -|,.;:")
    return shortened if shortened else value[:limit].rstrip()


def _title_candidate(product: ProductRecord) -> str:
    name = _clean(product.name)
    brand = _clean(product.brand)
    category = _clean(product.category)

    parts = [name]
    if brand and brand.casefold() not in name.casefold():
        parts.append(brand)
    if category and category.casefold() not in name.casefold():
        parts.append(category)

    candidate = " | ".join(part for part in parts if part)
    return _truncate(candidate, 60)


def _meta_candidate(product: ProductRecord) -> str:
    name = _clean(product.name)
    brand = _clean(product.brand)
    category = _clean(product.category)

    context = " ".join(part for part in (brand, category) if part)
    if context:
        candidate = (
            f"{name}; {context} ürün grubunda yer alır. Teknik özellikler, "
            "uyumluluk ve kullanım bilgilerini ürün detaylarında inceleyin."
        )
    else:
        candidate = (
            f"{name} için teknik özellikler, uyumluluk ve kullanım bilgileri "
            "ürün detaylarında yer alır."
        )
    return _truncate(candidate, 160)


def _description_candidate(product: ProductRecord) -> str:
    brand = _clean(product.brand) or "marka"
    category = _clean(product.category) or "kategori"
    return (
        "Açıklamayı şu doğrulanabilir bölümlerle genişlet: teknik özellikler, "
        "uyumlu marka-model bilgisi, montaj/kullanım notları ve güvenlik uyarısı. "
        f"Metinde {brand} marka ve {category} kategori bağlamını açıkça belirt; "
        "kaynağı olmayan ölçü, sertifika veya uyumluluk iddiası ekleme."
    )


def suggest_product_improvements(item: CatalogAuditItem) -> ProductSuggestion:
    """Create review-only suggestions without changing product identity fields."""
    issue_codes = {issue.code for issue in item.result.issues}
    product = item.product
    suggestions: list[FieldSuggestion] = []

    if issue_codes & {
        "meta_title.empty",
        "meta_title.short",
        "meta_title.long",
        "meta_title.missing_name",
        "meta_title.duplicate",
    }:
        suggestions.append(
            FieldSuggestion(
                field="meta_title",
                current_value=product.meta_title,
                suggested_value=_title_candidate(product),
                rationale="Meta başlığı ürün adı bağlamını koruyarak 60 karakter sınırına yaklaştır.",
            )
        )

    if issue_codes & {
        "meta_description.empty",
        "meta_description.short",
        "meta_description.long",
        "meta_description.missing_brand",
        "meta_description.duplicate",
    }:
        suggestions.append(
            FieldSuggestion(
                field="meta_description",
                current_value=product.meta_description,
                suggested_value=_meta_candidate(product),
                rationale="Meta açıklamayı marka ve kategori bağlamıyla 160 karakter sınırında yeniden değerlendir.",
            )
        )

    if issue_codes & {
        "description.empty",
        "description.short",
        "description.missing_category",
    }:
        suggestions.append(
            FieldSuggestion(
                field="description",
                current_value=product.description,
                suggested_value=_description_candidate(product),
                rationale="Ürün açıklamasını yalnızca doğrulanabilir teknik ve uyumluluk bilgileriyle genişlet.",
            )
        )

    return ProductSuggestion(
        row_number=item.row_number,
        name=product.name,
        slug=product.slug,
        score=item.result.score,
        suggestions=tuple(suggestions),
    )


def suggest_catalog_improvements(
    report: CatalogAuditReport,
) -> tuple[ProductSuggestion, ...]:
    suggestions = (
        suggest_product_improvements(item)
        for item in report.items
        if item.result.issues
    )
    return tuple(item for item in suggestions if item.suggestions)


def write_suggestions_csv(
    suggestions: tuple[ProductSuggestion, ...],
    path: str | Path,
) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=(
                "row_number",
                "name",
                "slug",
                "score",
                "field",
                "current_value",
                "suggested_value",
                "rationale",
                "auto_apply_safe",
            ),
        )
        writer.writeheader()
        for product in suggestions:
            for suggestion in product.suggestions:
                writer.writerow(
                    {
                        "row_number": product.row_number,
                        "name": product.name,
                        "slug": product.slug,
                        "score": product.score,
                        "field": suggestion.field,
                        "current_value": suggestion.current_value,
                        "suggested_value": suggestion.suggested_value,
                        "rationale": suggestion.rationale,
                        "auto_apply_safe": suggestion.auto_apply_safe,
                    }
                )
