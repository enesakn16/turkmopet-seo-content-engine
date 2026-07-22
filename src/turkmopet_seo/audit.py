from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class Severity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class ProductRecord:
    name: str
    slug: str
    meta_title: str = ""
    meta_description: str = ""
    description: str = ""
    brand: str = ""
    category: str = ""


@dataclass(frozen=True, slots=True)
class AuditIssue:
    code: str
    severity: Severity
    field: str
    message: str


@dataclass(frozen=True, slots=True)
class AuditResult:
    score: int
    issues: tuple[AuditIssue, ...]

    @property
    def passed(self) -> bool:
        return not any(issue.severity == Severity.ERROR for issue in self.issues)


def _text(value: str) -> str:
    return " ".join((value or "").split())


def audit_product(product: ProductRecord) -> AuditResult:
    """Report SEO content issues without changing product name or slug."""
    issues: list[AuditIssue] = []

    if not _text(product.name):
        issues.append(AuditIssue("name.empty", Severity.ERROR, "name", "Ürün adı boş olamaz."))
    if not _text(product.slug):
        issues.append(AuditIssue("slug.empty", Severity.ERROR, "slug", "Slug boş olamaz."))

    title = _text(product.meta_title)
    if not title:
        issues.append(AuditIssue("meta_title.empty", Severity.ERROR, "meta_title", "Meta başlık boş olamaz."))
    elif len(title) < 30:
        issues.append(AuditIssue("meta_title.short", Severity.WARNING, "meta_title", "Meta başlık 30 karakterden kısa."))
    elif len(title) > 60:
        issues.append(AuditIssue("meta_title.long", Severity.WARNING, "meta_title", "Meta başlık 60 karakterden uzun."))

    meta = _text(product.meta_description)
    if not meta:
        issues.append(AuditIssue("meta_description.empty", Severity.ERROR, "meta_description", "Meta açıklama boş olamaz."))
    elif len(meta) < 90:
        issues.append(AuditIssue("meta_description.short", Severity.WARNING, "meta_description", "Meta açıklama 90 karakterden kısa."))
    elif len(meta) > 160:
        issues.append(AuditIssue("meta_description.long", Severity.WARNING, "meta_description", "Meta açıklama 160 karakterden uzun."))

    description = _text(product.description)
    if not description:
        issues.append(AuditIssue("description.empty", Severity.ERROR, "description", "Ürün açıklaması boş olamaz."))
    elif len(description) < 180:
        issues.append(AuditIssue("description.short", Severity.WARNING, "description", "Ürün açıklaması 180 karakterden kısa."))

    if title and product.name and _text(product.name).casefold() not in title.casefold():
        issues.append(AuditIssue("meta_title.missing_name", Severity.WARNING, "meta_title", "Meta başlık ürün adını içermiyor."))

    if product.brand and _text(product.brand).casefold() not in meta.casefold():
        issues.append(AuditIssue("meta_description.missing_brand", Severity.INFO, "meta_description", "Meta açıklama marka bilgisini içermiyor."))

    if product.category and _text(product.category).casefold() not in description.casefold():
        issues.append(AuditIssue("description.missing_category", Severity.INFO, "description", "Açıklama kategori bağlamını içermiyor."))

    penalty = 0
    for issue in issues:
        if issue.severity == Severity.ERROR:
            penalty += 25
        elif issue.severity == Severity.WARNING:
            penalty += 10
        else:
            penalty += 3

    return AuditResult(score=max(0, 100 - penalty), issues=tuple(issues))
