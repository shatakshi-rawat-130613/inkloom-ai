"""Fails if frontend/src/api/types.ts drifts from backend enums and schemas."""

import re
from enum import StrEnum
from pathlib import Path

import pytest
from pydantic import BaseModel

from app import enums, schemas

TS_PATH = Path(__file__).resolve().parents[2] / "frontend" / "src" / "api" / "types.ts"

ENUMS: list[type[StrEnum]] = [
    enums.ContentType,
    enums.SubmissionStatus,
    enums.OverallStatus,
    enums.FindingType,
    enums.Severity,
    enums.FindingCategory,
    enums.FindingSource,
    enums.AIStatus,
    enums.ReviewDecision,
    enums.SubmissionAction,
]

MODELS: list[type[BaseModel]] = [
    schemas.ErrorBody,
    schemas.ErrorResponse,
    schemas.Guideline,
    schemas.Fact,
    schemas.Term,
    schemas.BrandSummary,
    schemas.BrandDetail,
    schemas.Finding,
    schemas.SeverityCounts,
    schemas.AnalysisRunSummary,
    schemas.AnalysisRun,
    schemas.ContentVersion,
    schemas.HumanReview,
    schemas.AuditLogEntry,
    schemas.SubmissionListItem,
    schemas.SubmissionDetail,
    schemas.SubmissionCreate,
    schemas.VersionCreate,
    schemas.ReviewRequestCreate,
    schemas.ReviewCreate,
    schemas.HealthResponse,
]


def _strip_comments(src: str) -> str:
    src = re.sub(r"/\*.*?\*/", "", src, flags=re.S)
    return re.sub(r"//[^\n]*", "", src)


@pytest.fixture(scope="module")
def ts_source() -> str:
    return _strip_comments(TS_PATH.read_text())


def _ts_union(src: str, name: str) -> set[str]:
    match = re.search(rf"export type {name}\s*=\s*(.+?)(?=\nexport |\Z)", src, flags=re.S)
    assert match, f"type {name} missing from types.ts"
    return set(re.findall(r"'([^']+)'", match.group(1)))


def _ts_interface(src: str, name: str) -> tuple[dict[str, bool], str | None]:
    match = re.search(rf"export interface {name}(?:\s+extends\s+(\w+))?\s*\{{(.*?)\n\}}", src, flags=re.S)
    assert match, f"interface {name} missing from types.ts"
    fields = {m.group(1): bool(m.group(2)) for m in re.finditer(r"^\s*(\w+)(\?)?:", match.group(2), flags=re.M)}
    return fields, match.group(1)


def _ts_fields(src: str, name: str) -> dict[str, bool]:
    fields, parent = _ts_interface(src, name)
    return {**(_ts_fields(src, parent) if parent else {}), **fields}


@pytest.mark.parametrize("enum_cls", ENUMS, ids=lambda e: e.__name__)
def test_enum_values_match(ts_source, enum_cls):
    assert _ts_union(ts_source, enum_cls.__name__) == {m.value for m in enum_cls}


@pytest.mark.parametrize("model", MODELS, ids=lambda m: m.__name__)
def test_interface_fields_match(ts_source, model):
    ts_fields = _ts_fields(ts_source, model.__name__)
    assert set(ts_fields) == set(model.model_fields), model.__name__
    # Optional (?) in TS exactly when the backend field has a default.
    for name, info in model.model_fields.items():
        has_default = not info.is_required()
        is_response = not issubclass(model, schemas._Strict)
        if is_response:
            assert ts_fields[name] is False, f"{model.__name__}.{name}: response fields are never omitted"
        else:
            assert ts_fields[name] is has_default, f"{model.__name__}.{name}: optional mismatch"


def test_max_body_chars_matches(ts_source):
    match = re.search(r"MAX_BODY_CHARS\s*=\s*([\d_]+)", ts_source)
    assert match and int(match.group(1).replace("_", "")) == schemas.MAX_BODY_CHARS
