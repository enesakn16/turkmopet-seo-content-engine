"""Türkmopet catalog SEO analysis tools."""

from .adapters import read_platform_catalog_csv
from .audit import AuditIssue, AuditResult, ProductRecord, Severity, audit_product
from .cannibalization import (
    CannibalizationConflict,
    CannibalizationPage,
    detect_cannibalization,
    write_cannibalization_csv,
)
from .catalog import (
    CatalogAuditItem,
    CatalogAuditReport,
    CatalogImportError,
    audit_catalog,
    read_catalog_csv,
    write_audit_csv,
)
from .history import (
    ManifestComparison,
    ManifestComparisonError,
    MetricDelta,
    compare_run_manifests,
    read_run_manifest,
    write_manifest_comparison,
)
from .search_console import (
    ProductSearchOpportunity,
    SearchConsoleImportError,
    SearchConsoleRow,
    prioritize_search_opportunities,
    read_search_console_csv,
    write_search_opportunities_csv,
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
    "CannibalizationConflict",
    "CannibalizationPage",
    "CatalogAuditItem",
    "CatalogAuditReport",
    "CatalogGroupSummary",
    "CatalogImportError",
    "CatalogPriorityItem",
    "CatalogSummary",
    "FieldSuggestion",
    "ManifestComparison",
    "ManifestComparisonError",
    "MetricDelta",
    "ProductRecord",
    "ProductSearchOpportunity",
    "ProductSuggestion",
    "SearchConsoleImportError",
    "SearchConsoleRow",
    "Severity",
    "audit_catalog",
    "audit_product",
    "compare_run_manifests",
    "detect_cannibalization",
    "prioritize_search_opportunities",
    "read_catalog_csv",
    "read_platform_catalog_csv",
    "read_run_manifest",
    "read_search_console_csv",
    "suggest_catalog_improvements",
    "suggest_product_improvements",
    "summarize_catalog",
    "write_audit_csv",
    "write_cannibalization_csv",
    "write_group_summary_csv",
    "write_manifest_comparison",
    "write_priority_csv",
    "write_search_opportunities_csv",
    "write_suggestions_csv",
]
