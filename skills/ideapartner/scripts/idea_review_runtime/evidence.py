from __future__ import annotations

import json
import re
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from html import unescape
from typing import Any, Protocol

from .artifacts import utc_now
from .validation import EvidenceIntegrityError


SOURCE_TYPES = {
    "paper",
    "dataset",
    "benchmark",
    "repository",
    "official_docs",
    "first_party_report",
}


class SourceVerifier(Protocol):
    def verify(self, source: dict[str, Any]) -> dict[str, Any]: ...


def _clean_text(value: str) -> str:
    return " ".join(re.sub(r"[^a-z0-9]+", " ", value.casefold()).split())


def _title_matches(expected: str, actual: str) -> bool:
    expected_tokens = set(_clean_text(expected).split())
    actual_tokens = set(_clean_text(actual).split())
    if not expected_tokens or not actual_tokens:
        return False
    overlap = len(expected_tokens & actual_tokens) / len(expected_tokens)
    return overlap >= 0.6


def _http_json(url: str, timeout: float) -> tuple[dict[str, Any], str]:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "IdeaPartner/1.1 (+https://github.com/Markchenc/IdeaPartner)"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        final_url = response.geturl()
        body = response.read(2 * 1024 * 1024)
    value = json.loads(body.decode("utf-8"))
    if not isinstance(value, dict):
        raise ValueError("resolver returned a non-object JSON response")
    return value, final_url


def _http_text(url: str, timeout: float) -> tuple[str, str]:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "IdeaPartner/1.1 (+https://github.com/Markchenc/IdeaPartner)"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        final_url = response.geturl()
        body = response.read(2 * 1024 * 1024)
    return body.decode("utf-8", errors="replace"), final_url


class LiveSourceVerifier:
    """Resolve source identity; it does not judge semantic entailment."""

    def __init__(self, *, timeout: float = 10.0, enabled: bool = True) -> None:
        self.timeout = timeout
        self.enabled = enabled

    def verify(self, source: dict[str, Any]) -> dict[str, Any]:
        checked_at = utc_now()
        if not self.enabled:
            return {
                "status": "unverified",
                "method": "deferred",
                "checked_at": checked_at,
                "resolved_url": None,
                "detail": "Live source verification was deferred.",
            }

        identifiers = source.get("identifiers", {})
        try:
            if identifiers.get("doi"):
                return self._verify_doi(source, str(identifiers["doi"]), checked_at)
            if identifiers.get("arxiv"):
                return self._verify_arxiv(source, str(identifiers["arxiv"]), checked_at)
            if identifiers.get("openalex"):
                return self._verify_openalex(source, str(identifiers["openalex"]), checked_at)
            if source.get("url"):
                return self._verify_url(source, str(source["url"]), checked_at)
        except (urllib.error.URLError, TimeoutError, OSError, ValueError, ET.ParseError) as error:
            return {
                "status": "unreachable",
                "method": "resolver",
                "checked_at": checked_at,
                "resolved_url": None,
                "detail": f"{type(error).__name__}: {error}",
            }
        return {
            "status": "unverified",
            "method": "none",
            "checked_at": checked_at,
            "resolved_url": None,
            "detail": "No DOI, arXiv ID, OpenAlex ID, or HTTPS URL was supplied.",
        }

    def _verify_doi(self, source: dict[str, Any], doi: str, checked_at: str) -> dict[str, Any]:
        normalized = doi.removeprefix("https://doi.org/").removeprefix("http://doi.org/")
        url = f"https://api.crossref.org/works/{urllib.parse.quote(normalized, safe='/')}"
        data, final_url = _http_json(url, self.timeout)
        message = data.get("message", {})
        titles = message.get("title", []) if isinstance(message, dict) else []
        actual_title = titles[0] if titles else ""
        matches = _title_matches(source["title"], actual_title)
        return {
            "status": "verified" if matches else "metadata_mismatch",
            "method": "crossref-doi",
            "checked_at": checked_at,
            "resolved_url": final_url,
            "canonical_id": normalized,
            "matched_title": actual_title,
            "detail": "DOI resolved and title matched." if matches else "DOI resolved but title did not match.",
        }

    def _verify_arxiv(self, source: dict[str, Any], arxiv_id: str, checked_at: str) -> dict[str, Any]:
        normalized = arxiv_id.removeprefix("arXiv:").split("v", 1)[0]
        url = f"https://export.arxiv.org/api/query?id_list={urllib.parse.quote(normalized)}"
        body, final_url = _http_text(url, self.timeout)
        root = ET.fromstring(body)
        namespace = {"atom": "http://www.w3.org/2005/Atom"}
        entry = root.find("atom:entry", namespace)
        actual_title = "" if entry is None else " ".join((entry.findtext("atom:title", "", namespace)).split())
        matches = bool(entry is not None and _title_matches(source["title"], actual_title))
        return {
            "status": "verified" if matches else "metadata_mismatch",
            "method": "arxiv-api",
            "checked_at": checked_at,
            "resolved_url": final_url,
            "canonical_id": normalized,
            "matched_title": actual_title,
            "detail": "arXiv record resolved and title matched." if matches else "arXiv record was absent or its title did not match.",
        }

    def _verify_openalex(self, source: dict[str, Any], openalex_id: str, checked_at: str) -> dict[str, Any]:
        normalized = openalex_id.rsplit("/", 1)[-1]
        url = f"https://api.openalex.org/works/{urllib.parse.quote(normalized)}"
        data, final_url = _http_json(url, self.timeout)
        actual_title = str(data.get("display_name", ""))
        matches = _title_matches(source["title"], actual_title)
        return {
            "status": "verified" if matches else "metadata_mismatch",
            "method": "openalex-api",
            "checked_at": checked_at,
            "resolved_url": final_url,
            "canonical_id": normalized,
            "matched_title": actual_title,
            "detail": "OpenAlex record resolved and title matched." if matches else "OpenAlex record resolved but title did not match.",
        }

    def _verify_url(self, source: dict[str, Any], url: str, checked_at: str) -> dict[str, Any]:
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme != "https" or not parsed.hostname:
            return {
                "status": "unverified",
                "method": "https-url",
                "checked_at": checked_at,
                "resolved_url": None,
                "detail": "Only public HTTPS source URLs are resolved.",
            }
        hostname = parsed.hostname.casefold()
        if hostname in {"localhost", "127.0.0.1", "::1"} or hostname.endswith(".local"):
            return {
                "status": "unverified",
                "method": "https-url",
                "checked_at": checked_at,
                "resolved_url": None,
                "detail": "Local source URLs are not allowed.",
            }
        body, final_url = _http_text(url, self.timeout)
        title_match = re.search(r"<title[^>]*>(.*?)</title>", body, flags=re.IGNORECASE | re.DOTALL)
        actual_title = unescape(re.sub(r"<[^>]+>", " ", title_match.group(1))).strip() if title_match else ""
        metadata_matches = bool(actual_title and _title_matches(source["title"], actual_title))
        return {
            "status": "verified" if metadata_matches else "metadata_mismatch",
            "method": "https-url",
            "checked_at": checked_at,
            "resolved_url": final_url,
            "matched_title": actual_title,
            "detail": (
                "HTTPS resource resolved and its HTML title matched."
                if metadata_matches
                else "HTTPS resource resolved but its HTML title was absent or did not match."
            ),
        }


def normalize_and_verify_source(source: Any, verifier: SourceVerifier) -> dict[str, Any]:
    if not isinstance(source, dict):
        raise EvidenceIntegrityError("Every source must be an object")
    required = ("source_id", "source_type", "title", "authors", "year")
    missing = [key for key in required if key not in source]
    if missing:
        raise EvidenceIntegrityError(f"Source is missing required fields: {', '.join(missing)}")
    if not isinstance(source["source_id"], str) or not source["source_id"].strip():
        raise EvidenceIntegrityError("source_id must be a non-empty string")
    if not isinstance(source["source_type"], str) or source["source_type"] not in SOURCE_TYPES:
        allowed = ", ".join(sorted(SOURCE_TYPES))
        raise EvidenceIntegrityError(
            f"Source {source['source_id']} has unsupported source_type {source['source_type']!r}; allowed: {allowed}"
        )
    if not isinstance(source["title"], str) or not source["title"].strip():
        raise EvidenceIntegrityError(f"Source {source['source_id']} must have a title")
    if not isinstance(source["authors"], list):
        raise EvidenceIntegrityError(f"Source {source['source_id']} authors must be a list")
    identifiers = source.get("identifiers", {})
    if not isinstance(identifiers, dict):
        raise EvidenceIntegrityError(f"Source {source['source_id']} identifiers must be an object")
    if not any(identifiers.get(key) for key in ("doi", "arxiv", "openalex")) and not source.get("url"):
        raise EvidenceIntegrityError(
            f"Source {source['source_id']} requires a DOI, arXiv ID, OpenAlex ID, or HTTPS URL"
        )

    normalized = {
        "source_id": source["source_id"].strip(),
        "source_type": source["source_type"],
        "title": source["title"].strip(),
        "authors": [str(author) for author in source["authors"]],
        "year": source["year"],
        "url": source.get("url"),
        "identifiers": {
            key: str(value)
            for key, value in identifiers.items()
            if key in {"doi", "arxiv", "openalex", "semantic_scholar"} and value
        },
        "content_locator": source.get("content_locator"),
    }
    # Never trust a worker's self-declared verification field.
    normalized["verification"] = verifier.verify(normalized)
    return normalized


def normalize_and_verify_sources(sources: Any, verifier: SourceVerifier) -> list[dict[str, Any]]:
    if not isinstance(sources, list):
        raise EvidenceIntegrityError("sources must be a list")
    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    for source in sources:
        record = normalize_and_verify_source(source, verifier)
        source_id = record["source_id"]
        if source_id in seen:
            raise EvidenceIntegrityError(f"Duplicate source_id {source_id}")
        seen.add(source_id)
        normalized.append(record)
    return normalized


def merge_source_ledgers(*source_groups: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    ledger: dict[str, dict[str, Any]] = {}
    for group in source_groups:
        for source in group:
            source_id = source["source_id"]
            if source_id in ledger:
                comparable = ("source_type", "title", "authors", "year", "url", "identifiers")
                if any(ledger[source_id].get(key) != source.get(key) for key in comparable):
                    raise EvidenceIntegrityError(f"Conflicting metadata for source_id {source_id}")
                if ledger[source_id].get("verification", {}).get("status") != "verified":
                    ledger[source_id] = source
            else:
                ledger[source_id] = source
    return ledger
