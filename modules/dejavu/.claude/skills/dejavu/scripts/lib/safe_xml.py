"""XML parsing hardened for a stdlib-only skill.

`defusedxml` would be the usual answer, but this directory must run wherever
Claude Code runs with no install step, so a third-party dependency is not
available. The two attacks that matter for `xml.etree.ElementTree` — entity
expansion (billion laughs) and external entity references (XXE) — both require
a document type declaration. Atom feeds from arXiv never carry one, so
refusing any document containing `<!DOCTYPE` or `<!ENTITY` closes both vectors
outright rather than trying to bound them.

A size cap is applied as well, so a merely enormous (rather than malicious)
response can't exhaust memory.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET

# arXiv's largest observed search response is a few hundred KB; 25 MB is far
# above any legitimate feed and far below anything that would hurt.
MAX_XML_BYTES = 25 * 1024 * 1024

_DOCTYPE = re.compile(r"<!\s*(DOCTYPE|ENTITY)", re.IGNORECASE)


class UnsafeXMLError(ValueError):
    """The document declares a DTD or entities, which this parser refuses."""


def fromstring(xml_text: str) -> ET.Element:
    if len(xml_text.encode("utf-8", errors="ignore")) > MAX_XML_BYTES:
        raise UnsafeXMLError(
            f"XML response exceeds {MAX_XML_BYTES} bytes; refusing to parse."
        )
    # Only inspect the prolog: a DTD is only legal before the root element, and
    # scanning the whole body would reject documents that merely discuss DTDs.
    prolog = xml_text[:4096]
    if _DOCTYPE.search(prolog):
        raise UnsafeXMLError(
            "XML response contains a DOCTYPE or ENTITY declaration; refusing to "
            "parse it (entity-expansion and external-entity risk)."
        )
    return ET.fromstring(xml_text)


ParseError = ET.ParseError
