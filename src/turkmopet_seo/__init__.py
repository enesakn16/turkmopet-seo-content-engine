"""Türkmopet catalog SEO analysis tools."""

from .adapters import read_platform_catalog_csv
from .audit import AuditIssue, AuditResult, ProductRecord, Severity, audit_product
from .catalog import (
    CatalogAuditItem,
    CatalogAuditReport,
    CatalogImportError,
    audit_catalog,
    read_catalog_csv,
    write_audit_csv,
)
from .suggestions import (
    FieldSuggestion,
    ProductSuggestion,
    suggest_catalog_improvements,
    suggest_product_improvements,
    write_suggestions_csv,
)
from .summary import (
    CatalogGroupSummary,
    CatalogPriorityItem,
    CatalogSummary,
    summarize_catalog,
    write_group_summary_csv,
    write_priority_csv,
)

__all__ = [
    "AuditIssue",
    "AuditResult",
    "CatalogAuditItem",
    "CatalogAuditReport",
    "CatalogGroupSummary",
    "CatalogImportError",
    "CatalogPriorityItem",
    "CatalogSummary",
    "FieldSuggestion",
    "ProductRecord",
    "ProductSuggestion",
    "Severity",
    "audit_catalog",
    "audit_product",
    "read_catalog_csv",
    "read_platform_catalog_csv",
    "suggest_catalog_improvements",
    "suggest_product_improvements",
    "summarize_catalog",
    "write_audit_csv",
    "write_group_summary_csv",
    "write_priority_csv",
    "write_suggestions_csv",
]
