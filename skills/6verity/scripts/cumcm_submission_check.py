#!/usr/bin/env python3
"""CUMCM 2026 electronic-paper and supporting-material hard gate."""

from __future__ import annotations

import argparse
import hashlib
import html
import io
import re
import sys
import unicodedata
import zipfile
import zlib
import xml.etree.ElementTree as ET
from pathlib import Path


MIB = 1024 * 1024
MAX_ZIP_SCAN_BYTES = 256 * MIB
MAX_ZIP_MEMBER_BYTES = 64 * MIB
MAX_ZIP_COMPRESSION_RATIO = 200
SOURCE_SUFFIXES = {
    ".bat",
    ".c",
    ".cc",
    ".cmd",
    ".cpp",
    ".cs",
    ".do",
    ".f",
    ".f90",
    ".go",
    ".h",
    ".hpp",
    ".ipynb",
    ".java",
    ".jl",
    ".js",
    ".m",
    ".mlx",
    ".nb",
    ".ps1",
    ".py",
    ".r",
    ".rs",
    ".sas",
    ".scala",
    ".sh",
    ".sql",
    ".ts",
    ".wl",
}
TEXT_SUFFIXES = SOURCE_SUFFIXES | {
    ".bib",
    ".csv",
    ".json",
    ".md",
    ".tex",
    ".toml",
    ".tsv",
    ".txt",
    ".typ",
    ".xml",
    ".yaml",
    ".yml",
}
OOXML_SUFFIXES = {".docx", ".pptx", ".xlsx", ".xlsm"}
APPENDIX_HEADING_RE = re.compile(
    r"(?m)^[ \t]*附[ \t]*录"
    r"(?:"
    r"[ \t]*[A-Za-zＡ-Ｚａ-ｚ0-9一二三四五六七八九十]+(?:[ \t]+[^\r\n]{1,30})?"
    r"|[ \t]*[：:][ \t]*[^\r\n]{1,30}"
    r"|[ \t]+[^\r\n。！？；，,]{1,30}"
    r")?"
    r"[ \t]*$"
)


class Report:
    def __init__(self) -> None:
        self.failures: list[str] = []
        self.not_run: list[str] = []
        self.warnings: list[str] = []
        self.passes: list[str] = []

    def fail(self, message: str) -> None:
        self.failures.append(message)
        print(f"FAIL: {message}")

    def blocked(self, message: str) -> None:
        self.not_run.append(message)
        print(f"NOT_RUN: {message}")

    def warn(self, message: str) -> None:
        self.warnings.append(message)
        print(f"WARN: {message}")

    def ok(self, message: str) -> None:
        self.passes.append(message)
        print(f"PASS: {message}")

    def finish(self) -> int:
        print(
            "SUMMARY: "
            f"PASS={len(self.passes)} FAIL={len(self.failures)} "
            f"WARN={len(self.warnings)} NOT_RUN={len(self.not_run)}"
        )
        if self.failures:
            return 1
        if self.not_run:
            return 2
        print("PASS: CUMCM 2026 submission gate passed")
        return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check CUMCM 2026 electronic paper and supporting materials."
    )
    parser.add_argument("--paper-pdf", required=True, type=Path)
    parser.add_argument("--paper-source", required=True, type=Path)
    parser.add_argument("--support-archive", type=Path)
    parser.add_argument("--ai-usage", choices=("used", "not-used", "auto"), default="auto")
    parser.add_argument("--ai-details", type=Path)
    parser.add_argument("--forbidden-term", action="append", default=[])
    parser.add_argument(
        "--identity-terms-complete",
        action="store_true",
        help="Confirm that every known team/member/school/number/region identity value was supplied.",
    )
    parser.add_argument(
        "--support-manifest-reviewed",
        action="store_true",
        help="Confirm a manual archive-to-appendix manifest and required-source review.",
    )
    parser.add_argument(
        "--support-content-reviewed",
        action="store_true",
        help="Confirm manual identity review of archive names, content, and document metadata.",
    )
    parser.add_argument(
        "--ai-details-reviewed",
        action="store_true",
        help="Confirm human semantic review of all four required AI-details information groups.",
    )
    parser.add_argument("--body-page-limit", type=int, default=30)
    parser.add_argument("--paper-size-limit-mb", type=float, default=20.0)
    parser.add_argument("--support-size-limit-mb", type=float, default=20.0)
    return parser.parse_args()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def strip_source_comments(text: str, suffix: str) -> str:
    if suffix == ".tex":
        return "\n".join(re.sub(r"(?<!\\)%.*$", "", line) for line in text.splitlines())
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    return re.sub(r"(?m)//.*$", "", text)


def collect_source_text(main: Path, report: Report) -> str:
    if not main.is_file():
        report.fail("paper source does not exist")
        return ""
    if main.suffix not in {".tex", ".typ"}:
        report.fail("paper source must be main.tex or main.typ")
        return ""
    seen: set[Path] = set()
    collected: list[str] = []

    def visit(path: Path) -> None:
        resolved = path.resolve()
        if resolved in seen:
            return
        seen.add(resolved)
        if not path.is_file():
            report.fail("an included paper source file does not exist")
            return
        try:
            text = strip_source_comments(read_text(path), path.suffix)
        except (OSError, UnicodeDecodeError):
            report.fail("a paper source file is unreadable or is not valid UTF-8")
            return
        if not text.strip():
            report.fail("a paper source file is empty after comments are removed")
            return
        collected.append(text)
        if path.suffix == ".tex":
            braced_pattern = r"\\(?:input|include)\s*\{([^}]+)\}"
            bare_pattern = r"\\input[ \t]+([^\s%{}\\#]+)"
            for include in re.findall(braced_pattern, text):
                if "\\" in include or "#" in include:
                    report.blocked("dynamic LaTeX include could not be resolved automatically")
                    continue
                target = main.parent / include.strip()
                if target.suffix == "":
                    target = target.with_suffix(".tex")
                visit(target)
            for include in re.findall(bare_pattern, text):
                target = main.parent / include.strip()
                if target.suffix == "":
                    target = target.with_suffix(".tex")
                visit(target)
            without_literals = re.sub(braced_pattern, "", text)
            without_literals = re.sub(bare_pattern, "", without_literals)
            if re.search(r"\\(?:input|include)\b", without_literals):
                report.blocked("dynamic LaTeX include could not be resolved automatically")
        else:
            literal_pattern = (
                r'(?<![\w-])(?:#[ \t]*)?include'
                r'(?:\([ \t]*"([^"]+\.typ)"[ \t]*\)|[ \t]+"([^"]+\.typ)")'
            )
            literal_matches = list(re.finditer(literal_pattern, text))
            for match in literal_matches:
                include = match.group(1) or match.group(2)
                visit(path.parent / include)
            without_literals = re.sub(literal_pattern, "", text)
            if re.search(r"#[ \t]*include\b", without_literals):
                report.blocked("dynamic Typst include could not be resolved automatically")

    visit(main)
    return "\n".join(collected)


def check_size(path: Path, limit_mb: float, label: str, report: Report) -> bool:
    if not path.is_file():
        report.fail(f"{label} does not exist")
        return False
    size = path.stat().st_size
    limit = int(limit_mb * MIB)
    if size > limit:
        report.fail(f"{label} is {size / MIB:.2f} MiB, exceeds {limit_mb:g} MB limit")
        return False
    else:
        report.ok(f"{label} size {size / MIB:.2f} MiB <= {limit_mb:g} MB")
        return True


def open_pdf(path: Path, report: Report):
    parser_available = False
    try:
        import fitz  # type: ignore
        parser_available = True
    except ImportError:
        fitz = None

    if fitz is not None:
        try:
            return ("fitz", fitz.open(path))
        except Exception:
            pass

    try:
        from pypdf import PdfReader  # type: ignore
        parser_available = True
    except ImportError:
        PdfReader = None

    if PdfReader is not None:
        try:
            return ("pypdf", PdfReader(str(path)))
        except Exception:
            pass

    if parser_available:
        report.fail("electronic paper is unreadable or is not a valid PDF")
    else:
        report.blocked("PDF semantic checks require PyMuPDF or pypdf")
    return None


def fitz_page_lines(page) -> list[dict]:
    """Return visible text-line geometry without depending on private PyMuPDF APIs."""
    lines: list[dict] = []
    page_dict = page.get_text("dict")
    for block in page_dict.get("blocks", []):
        if block.get("type", 0) != 0:
            continue
        for line in block.get("lines", []):
            spans = line.get("spans", [])
            text = "".join(str(span.get("text", "")) for span in spans).strip()
            bbox = line.get("bbox")
            if not text or not bbox or len(bbox) < 4:
                continue
            lines.append(
                {
                    "text": text,
                    "bbox": tuple(float(value) for value in bbox[:4]),
                    "size": max((float(span.get("size", 0.0)) for span in spans), default=0.0),
                }
            )
    return lines


def pdf_data(path: Path, report: Report):
    opened = open_pdf(path, report)
    if not opened:
        return None
    backend, document = opened
    try:
        if backend == "fitz":
            pages = []
            extended_metadata: list[str] = []
            extended_metadata_complete = True
            for page in document:
                try:
                    annotations = page.annots()
                    if annotations is not None:
                        for annotation in annotations:
                            extended_metadata.extend(
                                str(value)
                                for value in (annotation.info or {}).values()
                                if value
                            )
                    widgets = page.widgets()
                    if widgets is not None:
                        for widget in widgets:
                            extended_metadata.extend(
                                str(value)
                                for value in (
                                    getattr(widget, "field_name", ""),
                                    getattr(widget, "field_label", ""),
                                    getattr(widget, "field_value", ""),
                                )
                                if value
                            )
                except Exception:
                    extended_metadata_complete = False
                pages.append(
                    {
                        "text": page.get_text("text"),
                        "width": float(page.rect.width),
                        "height": float(page.rect.height),
                        "words": page.get_text("words"),
                        "lines": fitz_page_lines(page),
                    }
                )
            try:
                xml_metadata = document.get_xml_metadata()
                if xml_metadata:
                    extended_metadata.append(xml_metadata)
            except Exception:
                extended_metadata_complete = False
            try:
                embedded_names = list(document.embfile_names())
                extended_metadata.extend(str(name) for name in embedded_names)
            except Exception:
                embedded_names = []
                extended_metadata_complete = False
            result = {
                "backend": backend,
                "pages": pages,
                "metadata": document.metadata or {},
                "extended_metadata": extended_metadata,
                "extended_metadata_complete": extended_metadata_complete,
                "embedded_names": embedded_names,
            }
            document.close()
            return result

        pages = []
        for page in document.pages:
            box = page.mediabox
            pages.append(
                {
                    "text": page.extract_text() or "",
                    "width": float(box.width),
                    "height": float(box.height),
                    "words": None,
                    "lines": None,
                }
            )
        metadata = {
            str(key).lstrip("/").lower(): str(value)
            for key, value in (document.metadata or {}).items()
        }
        return {
            "backend": backend,
            "pages": pages,
            "metadata": metadata,
            "extended_metadata": [],
            "extended_metadata_complete": False,
            "embedded_names": [],
        }
    except Exception:
        report.fail("electronic paper PDF could not be parsed completely")
        return None


def pdf_text_from_bytes(data: bytes, report: Report, label: str) -> tuple[str | None, bool]:
    parser_available = False
    try:
        import fitz  # type: ignore
        parser_available = True
    except ImportError:
        fitz = None

    if fitz is not None:
        try:
            document = fitz.open(stream=data, filetype="pdf")
            page_texts = []
            has_images = False
            extended_metadata: list[str] = []
            coverage_incomplete = False
            for page in document:
                page_texts.append(page.get_text("text"))
                has_images = has_images or bool(page.get_images(full=True))
                try:
                    annotations = page.annots()
                    if annotations is not None:
                        for annotation in annotations:
                            extended_metadata.extend(
                                str(value)
                                for value in (annotation.info or {}).values()
                                if value
                            )
                    widgets = page.widgets()
                    if widgets is not None:
                        for widget in widgets:
                            extended_metadata.extend(
                                str(value)
                                for value in (
                                    getattr(widget, "field_name", ""),
                                    getattr(widget, "field_label", ""),
                                    getattr(widget, "field_value", ""),
                                )
                                if value
                            )
                except Exception:
                    coverage_incomplete = True
            text = "\n".join(page_texts)
            metadata_text = "\n".join(str(value) for value in (document.metadata or {}).values())
            try:
                xml_metadata = document.get_xml_metadata()
                if xml_metadata:
                    extended_metadata.append(xml_metadata)
            except Exception:
                coverage_incomplete = True
            try:
                embedded_names = list(document.embfile_names())
                extended_metadata.extend(str(name) for name in embedded_names)
                coverage_incomplete = coverage_incomplete or bool(embedded_names)
            except Exception:
                coverage_incomplete = True
            document.close()
            return (
                text + "\n" + metadata_text + "\n" + "\n".join(extended_metadata),
                has_images or coverage_incomplete,
            )
        except Exception:
            pass

    try:
        from pypdf import PdfReader  # type: ignore
        parser_available = True
    except ImportError:
        PdfReader = None

    if PdfReader is not None:
        try:
            reader = PdfReader(io.BytesIO(data))
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
            metadata_text = "\n".join(str(value) for value in (reader.metadata or {}).values())
            return text + "\n" + metadata_text, True
        except Exception:
            pass

    if parser_available:
        report.fail(f"{label} is unreadable or is not a valid PDF")
    else:
        report.blocked(f"{label} text extraction requires PyMuPDF or pypdf")
    return None, True


def has_center_footer_number(page: dict, expected: str) -> bool | None:
    words = page.get("words")
    if words is None:
        return None
    width = page["width"]
    height = page["height"]
    candidates = []
    for word in words:
        x0, y0, x1, _y1, text = word[:5]
        center = (x0 + x1) / 2
        normalized = re.sub(r"^[\s\-—–]+|[\s\-—–]+$", "", str(text))
        if (
            normalized == expected
            and y0 >= height * 0.925
            and abs(center - width / 2) <= width * 0.06
        ):
            candidates.append(word)
    if len(candidates) > 1:
        return None
    return len(candidates) == 1


def compact_visible_text(text: str) -> str:
    return re.sub(r"\s+", "", text)


def identity_term_in_text(text: str, term: str) -> bool:
    """Match identities after NFKC and same-line whitespace normalization."""
    normalized_text = unicodedata.normalize("NFKC", text).casefold()
    normalized_term = unicodedata.normalize("NFKC", term).casefold()
    if normalized_term in normalized_text:
        return True
    compact_term = re.sub(r"\s+", "", normalized_term)
    if not compact_term:
        return False
    return any(
        compact_term in re.sub(r"\s+", "", line)
        for line in normalized_text.splitlines()
    )


def find_appendix_heading(page: dict) -> tuple[re.Match[str] | None, bool]:
    """Find a defensible appendix heading; flag styled short-title ambiguity."""
    ambiguous = False
    for match in APPENDIX_HEADING_RE.finditer(page["text"]):
        candidate = compact_visible_text(match.group(0))
        if re.fullmatch(
            r"附录(?:[A-Za-zＡ-Ｚａ-ｚ0-9一二三四五六七八九十]+)?[：:]?",
            candidate,
        ):
            return match, ambiguous

        lines = page.get("lines")
        if not lines:
            ambiguous = True
            continue
        matching_lines = [
            line for line in lines if compact_visible_text(line["text"]) == candidate
        ]
        sizes = sorted(
            float(line["size"])
            for line in lines
            if line.get("text", "").strip() and float(line.get("size", 0.0)) > 0
        )
        median_size = sizes[len(sizes) // 2] if sizes else 0.0
        for line in matching_lines:
            x0, y0, x1, _y1 = line["bbox"]
            centered = abs((x0 + x1) / 2 - page["width"] / 2) <= page["width"] * 0.15
            in_heading_area = page["height"] * 0.04 <= y0 <= page["height"] * 0.75
            prominent = float(line.get("size", 0.0)) + 0.5 >= median_size
            if centered and in_heading_area and prominent:
                return match, ambiguous
        ambiguous = True
    return None, ambiguous


def appendix_shares_body_text(
    page: dict,
    heading_match: re.Match[str] | None = None,
) -> bool | None:
    words = page.get("words")
    if words is None:
        return None
    height = page["height"]
    heading_y = None
    if heading_match is not None and page.get("lines"):
        candidate = compact_visible_text(heading_match.group(0))
        for line in page["lines"]:
            if compact_visible_text(line["text"]) == candidate:
                heading_y = float(line["bbox"][1])
                break
    for index, word in enumerate(words):
        if heading_y is not None:
            break
        text = re.sub(r"\s+", "", str(word[4]))
        if re.fullmatch(r"附录(?:[A-Za-zＡ-Ｚａ-ｚ0-9一二三四五六七八九十]+)?[：:]?", text):
            heading_y = float(word[1])
            break
        if text == "附" and index + 1 < len(words):
            next_word = words[index + 1]
            if str(next_word[4]).strip() == "录" and abs(float(next_word[1]) - float(word[1])) < 3:
                heading_y = min(float(word[1]), float(next_word[1]))
                break
    if heading_y is None:
        return None
    for word in words:
        y0 = float(word[1])
        text = str(word[4]).strip()
        if (
            height * 0.075 <= y0 < heading_y - 2
            and y0 < height * 0.88
            and text
            and not re.fullmatch(r"[-—–\s]*\d+[-—–\s]*", text)
        ):
            return True
    return False


def spaced_heading_pattern(heading: str) -> str:
    return r"[ \t]*".join(re.escape(character) for character in heading)


def pdf_heading_position(text: str, heading: str) -> int | None:
    pattern = rf"(?m)^[ \t]*{spaced_heading_pattern(heading)}[ \t]*$"
    match = re.search(pattern, text)
    return match.start() if match else None


def source_heading_position(text: str, heading: str) -> int | None:
    label = spaced_heading_pattern(heading)
    patterns = (
        rf"\\(?:section|chapter)\*?[ \t]*\{{[ \t]*{label}[ \t]*\}}",
        rf"#[ \t]*heading[\s\S]{{0,200}}?\[[ \t]*{label}[ \t]*\]",
        rf"(?m)^[ \t]*(?:=+[ \t]+)?{label}[ \t]*$",
    )
    positions = []
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            positions.append(match.start())
    return min(positions) if positions else None


def check_source(source: str, ai_usage: str, report: Report) -> str:
    toc_patterns = (
        r"\\tableofcontents\b",
        r"\\@starttoc\s*\{toc\}",
        r"\\tocpage\b",
        r"#\s*outline\s*\(",
        r"#\s*toc-page\s*\(",
    )
    if any(re.search(pattern, source) for pattern in toc_patterns):
        report.warn(
            "paper source contains a table-of-contents command, but it may be inside an unused macro; "
            "the compiled PDF remains the hard no-contents check"
        )
    else:
        report.ok("paper source contains no table-of-contents command")

    english_abstract = re.compile(
        r"英文摘要|"
        r"\\section\*?\{\s*Abstract\s*\}|"
        r"^={1,6}\s+Abstract\s*$",
        re.I | re.M,
    )
    if english_abstract.search(source):
        report.fail("CUMCM paper contains an English abstract marker")
    else:
        report.ok("no English abstract marker detected")

    placeholder = re.search(
        r"【[^】]+】|"
        r"PLACEHOLDER|TODO|TBD|待补充|待续写|示例数据",
        source,
        re.I,
    )
    if placeholder:
        report.fail(f"template placeholder remains: {placeholder.group(0)[:80]}")

    ai_heading = source_heading_position(source, "AI工具使用声明")
    references = source_heading_position(source, "参考文献")
    if ai_heading is None:
        report.warn(
            "paper source does not expose a directly detectable AI declaration heading; "
            "the compiled PDF remains the hard ordering check"
        )
    elif references is not None and ai_heading > references:
        report.warn(
            "paper source heading order is ambiguous because macro definitions can precede calls; "
            "the compiled PDF remains the hard ordering check"
        )
    else:
        report.ok("AI tool declaration is positioned before references")

    compact_source = re.sub(r"\s+", "", source)
    exact_not_used = "本参赛队在竞赛过程中未使用任何AI工具。"
    used_prefix = "本参赛队在竞赛过程中使用了"
    used_detail = "详细使用情况见支撑材料"
    has_not_used = exact_not_used in compact_source
    has_used = used_prefix in compact_source and used_detail in compact_source
    if has_not_used and has_used:
        report.fail("paper source contains conflicting used-AI and no-AI declarations")
    inferred = ai_usage
    if ai_usage == "auto":
        if has_not_used and not has_used:
            inferred = "not-used"
        elif has_used and not has_not_used:
            inferred = "used"
        else:
            report.fail("cannot infer a valid official AI usage declaration")

    if inferred == "not-used" and not has_not_used:
        report.fail("AI usage is not-used but the official no-AI declaration is absent")
    if inferred == "used" and not has_used:
        report.fail("AI usage is used but the official used-AI declaration structure is incomplete")

    if not re.search(r"支撑材料文件(?:列表|清单)|本论文没有支撑材料", source):
        report.fail("appendix lacks a supporting-material file list or no-material declaration")
    else:
        report.ok("appendix contains supporting-material list/declaration")

    code_marker = re.search(
        r"(?:\\begin\{lstlisting\}|\\lstinputlisting\b|```|#\s*raw\s*\(|raw\s*\[)",
        source,
    )
    if not code_marker and "本论文没有用到程序" not in source:
        report.fail("appendix contains neither visible source code nor the official no-program declaration")
    else:
        report.ok("appendix contains code or the official no-program declaration")

    return inferred


def check_paper_pdf(
    data: dict,
    forbidden_terms: list[str],
    body_limit: int,
    ai_usage: str,
    report: Report,
) -> str:
    pages = data["pages"]
    if not pages:
        report.fail("paper PDF has no pages")
        return ""

    for index, page in enumerate(pages, 1):
        if abs(page["width"] - 595.28) > 5 or abs(page["height"] - 841.89) > 5:
            report.fail(
                f"paper page {index} is not A4: {page['width']:.1f} x {page['height']:.1f} pt"
            )
            break
    else:
        report.ok("all paper pages are A4")

    texts = [page["text"] for page in pages]
    all_text = "\n".join(texts)
    first_page = texts[0]
    if "摘要" not in first_page:
        report.fail("electronic paper first page is not the abstract page")
    else:
        report.ok("electronic paper starts with the abstract page")

    if "承诺书" in all_text or "编号专用页" in all_text:
        report.fail("electronic paper contains a commitment or numbering page")
    else:
        report.ok("electronic paper excludes commitment and numbering pages")

    toc_heading = re.compile(
        r"(?mi)^[ \t]*(?:目[ \t]*录"
        r"(?:[ \t]*(?:[：:/／|｜-][ \t]*)?(?:Table[ \t]+of[ \t]+)?Contents)?"
        r"[ \t]*[：:]?|(?:Table[ \t]+of[ \t]+)?Contents)[ \t]*$"
    )
    if any(toc_heading.search(text) for text in texts):
        report.fail("paper PDF contains a table-of-contents page or heading")
    else:
        report.ok("paper PDF contains no table-of-contents heading")

    appendix_match = None
    appendix_index = None
    ambiguous_appendix = False
    for index, page in enumerate(pages[1:], 1):
        match, ambiguous = find_appendix_heading(page)
        ambiguous_appendix = ambiguous_appendix or ambiguous
        if match:
            appendix_index = index
            appendix_match = match
            break
    if appendix_index is None or appendix_match is None:
        if ambiguous_appendix:
            report.blocked(
                "an appendix-like short title was found but its heading geometry was inconclusive; "
                "manual appendix/page-boundary review is required"
            )
        else:
            report.fail("paper PDF has no detectable appendix heading")
    else:
        prefix = texts[appendix_index][: appendix_match.start()]
        prefix = re.sub(r"(?m)^[ \t]*\d+[ \t]*$", "", prefix).strip()
        shared_body_page = appendix_shares_body_text(
            pages[appendix_index], appendix_match
        )
        if shared_body_page is None and prefix:
            report.blocked(
                "appendix/body page boundary could not be determined geometrically; manual page-count review is required"
            )
            shared_body_page = True
        elif shared_body_page is None:
            shared_body_page = False
        body_pages = appendix_index if shared_body_page else appendix_index - 1
        if shared_body_page:
            report.warn("appendix begins on a page that also contains body text; that page was counted as body")
        if body_pages < 1:
            report.fail("paper has no detectable body pages after the abstract")
        elif body_pages > body_limit:
            report.fail(f"paper body has {body_pages} pages, exceeds {body_limit}-page limit")
        else:
            report.ok(f"paper body page count {body_pages} <= {body_limit}")

    missing_footers: list[int] = []
    footer_unavailable = False
    for index, page in enumerate(pages):
        footer = has_center_footer_number(page, str(index + 1))
        if footer is None:
            footer_unavailable = True
            break
        if not footer:
            missing_footers.append(index + 1)
    if footer_unavailable:
        report.blocked("continuous centered footer page-number check requires PyMuPDF")
    elif missing_footers:
        report.fail(
            "continuous centered footer numbering is missing or incorrect on page(s): "
            + ", ".join(str(page) for page in missing_footers)
        )
    else:
        report.ok("all paper pages have continuous centered footer numbers starting at 1")

    metadata = {str(key).lower(): str(value).strip() for key, value in data.get("metadata", {}).items()}
    author = metadata.get("author", "")
    if author and author.lower() not in {"anonymous", "none"}:
        report.fail("paper PDF author metadata is not anonymous")
    else:
        report.ok("paper PDF author metadata is empty or anonymous")

    metadata_text = "\n".join(metadata.values())
    extended_metadata_text = "\n".join(
        str(value) for value in data.get("extended_metadata", [])
    )
    if data.get("embedded_names"):
        report.blocked(
            "paper PDF contains embedded files whose content requires manual identity review"
        )
    if not data.get("extended_metadata_complete", False):
        report.blocked(
            "paper PDF extended metadata, annotations, forms, and embedded-name scan was incomplete"
        )
    for term_index, term in enumerate(forbidden_terms, 1):
        if term and identity_term_in_text(all_text, term):
            report.fail(f"forbidden identity term #{term_index} appears in paper PDF")
        if term and identity_term_in_text(metadata_text, term):
            report.fail(f"forbidden identity term #{term_index} appears in paper PDF metadata")
        if term and identity_term_in_text(extended_metadata_text, term):
            report.fail(
                f"forbidden identity term #{term_index} appears in paper PDF extended metadata"
            )

    ai_position = pdf_heading_position(all_text, "AI工具使用声明")
    reference_position = pdf_heading_position(all_text, "参考文献")
    if ai_position is None:
        report.fail("paper PDF is missing AI工具使用声明")
    elif reference_position is None:
        report.fail("paper PDF is missing references heading")
    elif ai_position > reference_position:
        report.fail("paper PDF places AI工具使用声明 after references")
    else:
        report.ok("paper PDF places AI tool declaration before references")

    compact_pdf = re.sub(r"\s+", "", all_text)
    exact_not_used = "本参赛队在竞赛过程中未使用任何AI工具。"
    used_prefix = "本参赛队在竞赛过程中使用了"
    used_detail = "详细使用情况见支撑材料"
    has_not_used = exact_not_used in compact_pdf
    has_used = used_prefix in compact_pdf and used_detail in compact_pdf
    if has_not_used and has_used:
        report.fail("paper PDF contains conflicting used-AI and no-AI declarations")
    if ai_usage == "not-used" and not has_not_used:
        report.fail("paper PDF does not contain the official no-AI declaration")
    elif ai_usage == "used" and not has_used:
        report.fail("paper PDF used-AI declaration is incomplete or conflicts with the source")
    else:
        report.ok("paper PDF AI declaration agrees with the selected usage state")

    if not re.search(r"支撑材料文件(?:列表|清单)|本论文没有支撑材料", all_text):
        report.fail("paper PDF appendix lacks a supporting-material list/declaration")
    else:
        report.ok("paper PDF contains supporting-material list/declaration")

    return all_text


def decode_text_bytes(data: bytes) -> str | None:
    bom_encodings = (
        (b"\xff\xfe\x00\x00", "utf-32-le"),
        (b"\x00\x00\xfe\xff", "utf-32-be"),
        (b"\xff\xfe", "utf-16-le"),
        (b"\xfe\xff", "utf-16-be"),
    )
    for bom, encoding in bom_encodings:
        if data.startswith(bom):
            try:
                return data.decode(encoding)
            except UnicodeDecodeError:
                return None
    for encoding in ("utf-8-sig", "gb18030"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return None


def ooxml_text_from_bytes(
    data: bytes,
    suffix: str,
) -> tuple[str | None, bool, bool]:
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as package:
            chunks: list[str] = []
            partial = False
            resource_limited = False
            infos = package.infolist()
            normalized_names = {
                item.filename.replace("\\", "/").casefold() for item in infos
            }
            required_parts = {
                ".docx": {"[content_types].xml", "word/document.xml"},
                ".pptx": {"[content_types].xml", "ppt/presentation.xml"},
                ".xlsx": {"[content_types].xml", "xl/workbook.xml"},
                ".xlsm": {"[content_types].xml", "xl/workbook.xml"},
            }.get(suffix, set())
            if not required_parts.issubset(normalized_names):
                return None, True, False
            readable_infos = [
                item
                for item in infos
                if not item.is_dir() and item.filename.lower().endswith((".xml", ".rels"))
            ]
            remaining_budget = MAX_ZIP_SCAN_BYTES
            if sum(max(item.file_size, 0) for item in readable_infos) > MAX_ZIP_SCAN_BYTES:
                partial = True
                resource_limited = True
            for item in infos:
                name = item.filename
                if name.lower().endswith((".xml", ".rels")):
                    chunks.append(name)
                    if item.flag_bits & 0x1:
                        partial = True
                        resource_limited = True
                        continue
                    blocker = zip_member_scan_blocker(item, remaining_budget)
                    if blocker is not None:
                        partial = True
                        resource_limited = True
                        continue
                    raw_bytes = package.read(item)
                    remaining_budget -= item.file_size
                    raw = decode_text_bytes(raw_bytes)
                    if raw is None:
                        partial = True
                    else:
                        chunks.append(html.unescape(raw))
                    try:
                        root = ET.fromstring(raw_bytes)
                    except ET.ParseError:
                        partial = True
                        continue
                    visible_parts = [part for part in root.itertext() if part]
                    chunks.append("\n".join(visible_parts))
                    # Join formatting runs only inside logical text containers.
                    # Joining the whole XML tree would create false identities
                    # across separate Word/PPT paragraphs or spreadsheet cells.
                    for element in root.iter():
                        local_name = str(element.tag).rsplit("}", 1)[-1]
                        if local_name not in {"p", "si", "c"}:
                            continue
                        logical_text = "".join(part for part in element.itertext() if part)
                        if logical_text:
                            chunks.append(logical_text)
                elif not name.endswith("/"):
                    partial = True
            return "\n".join(chunks), partial, resource_limited
    except (OSError, RuntimeError, EOFError, zipfile.BadZipFile, zlib.error):
        return None, True, False


def support_member_text(
    name: str,
    data: bytes,
    report: Report,
) -> tuple[str | None, str]:
    suffix = Path(name).suffix.lower()
    if suffix in TEXT_SUFFIXES:
        text = decode_text_bytes(data)
        return text, "complete" if text is not None else "none"
    if suffix in OOXML_SUFFIXES:
        text, has_binary_parts, resource_limited = ooxml_text_from_bytes(data, suffix)
        if text is None:
            report.fail("a supporting-material Office document is unreadable")
            return None, "none"
        if resource_limited:
            report.blocked(
                "a supporting-material Office package exceeds safe nested ZIP scan limits"
            )
        if suffix == ".xlsm" or has_binary_parts:
            return text, "partial"
        return text, "complete"
    if suffix == ".pdf":
        text, has_images = pdf_text_from_bytes(data, report, "a supporting-material PDF")
        if text is None:
            return None, "none"
        return text, "partial" if has_images else "complete"
    return None, "none"


def check_ai_details_text(text: str | None, manually_reviewed: bool, report: Report) -> None:
    if text is None:
        return
    groups = {
        "tool name and version/model": (
            any(word in text for word in ("工具名称", "AI工具"))
            and any(word in text for word in ("版本", "型号", "模型"))
        ),
        "purpose and stage": (
            any(word in text for word in ("目的", "用途"))
            and any(word in text for word in ("环节", "阶段"))
        ),
        "prompt and process": "提示" in text and "过程" in text,
        "adoption and manual review": (
            "采纳" in text
            and any(word in text for word in ("人工修改", "核验", "验证", "审查"))
        ),
    }
    missing = [name for name, present in groups.items() if not present]
    if missing:
        if manually_reviewed:
            report.warn(
                "AI details use nonstandard field wording; recorded human semantic review overrides "
                "the keyword precheck"
            )
            report.ok("AI details content received recorded human semantic review")
            return
        report.fail("AI details PDF lacks required information groups: " + ", ".join(missing))
        return
    report.ok("AI details PDF contains structural markers for all four information groups")
    if manually_reviewed:
        report.ok("AI details content received recorded human semantic review")
    else:
        report.blocked(
            "AI details semantics require human review; record the evidence before adding "
            "--ai-details-reviewed"
        )


def logical_archive_items(names: list[str]) -> set[str]:
    items: set[str] = set()
    for name in names:
        parts = [part for part in name.replace("\\", "/").split("/") if part]
        if not parts:
            continue
        items.add(parts[0] + ("/" if len(parts) > 1 else ""))
    return items


def support_manifest_block(text: str) -> str | None:
    marker = re.search(r"支撑材料文件(?:列表|清单)[ \t]*[：:]?", text)
    if marker is None:
        return None
    tail = text[marker.end() :]
    stop_patterns = (
        r"\\(?:sub)*section\*?[ \t]*\{",
        r"(?m)^[ \t]*={1,6}[ \t]+",
        r"(?mi)^[ \t]*(?:[A-ZＡ-Ｚ][.．][ \t]*)?\d+(?:[.．]\d+)*[ \t]+"
        r"(?:源程序|程序代码|代码附录|补充推导|其他附录)",
        r"(?mi)^[ \t]*(?:源程序(?:代码)?|程序代码|代码附录|补充推导|其他附录)"
        r"[ \t]*[：:]?[ \t]*$",
        r"\\begin\{lstlisting\}|\\lstinputlisting\b|```|#\s*raw\s*\(",
    )
    stops = []
    next_appendix = APPENDIX_HEADING_RE.search(tail)
    if next_appendix:
        stops.append(next_appendix.start())
    for pattern in stop_patterns:
        match = re.search(pattern, tail)
        if match:
            stops.append(match.start())
    return tail[: min(stops)] if stops else tail


def manifest_lists_item(block: str, item: str) -> bool:
    normalized_block = unicodedata.normalize("NFKC", block).casefold()
    normalized_item = unicodedata.normalize("NFKC", item).casefold()
    if normalized_item.endswith("/"):
        folder = re.escape(normalized_item.rstrip("/"))
        return bool(
            re.search(rf"(?<![\w.-]){folder}[ 	]*[\\/]", normalized_block)
            or re.search(
                rf"(?<![\w.-]){folder}[ 	]*(?:目录|文件夹)(?![\w.-])",
                normalized_block,
            )
        )
    token = re.escape(normalized_item)
    return bool(re.search(rf"(?<![\w.-]){token}(?![\w.-])", normalized_block))


def zip_member_scan_blocker(item: zipfile.ZipInfo, remaining_budget: int) -> str | None:
    """Return a safe, filename-free reason why a ZIP member must not be expanded."""
    if item.file_size < 0 or item.compress_size < 0:
        return "ZIP contains a member with invalid size metadata"
    if item.file_size > MAX_ZIP_MEMBER_BYTES:
        return (
            "ZIP member expansion exceeds the automatic per-member scan limit "
            f"of {MAX_ZIP_MEMBER_BYTES / MIB:g} MiB"
        )
    if item.file_size > 0:
        if item.compress_size == 0:
            return "ZIP member has a nonzero expansion size but zero compressed size"
        ratio = item.file_size / item.compress_size
        if ratio > MAX_ZIP_COMPRESSION_RATIO:
            return (
                "ZIP member compression ratio exceeds the automatic scan limit "
                f"of {MAX_ZIP_COMPRESSION_RATIO}:1"
            )
    if item.file_size > remaining_budget:
        return (
            "ZIP cumulative expansion exceeds the automatic scan budget "
            f"of {MAX_ZIP_SCAN_BYTES / MIB:g} MiB"
        )
    return None


def appendix_segment(text: str) -> str | None:
    matches = list(APPENDIX_HEADING_RE.finditer(text))
    if matches:
        return text[matches[0].end() :]
    structured_patterns = (
        r"\\(?:section|chapter)\*?[ \t]*\{[ \t]*附[ \t]*录[^}]*\}",
        r"#[ \t]*heading[\s\S]{0,200}?\[[ \t]*附[ \t]*录[^]]*\]",
    )
    for pattern in structured_patterns:
        match = re.search(pattern, text)
        if match:
            return text[match.end() :]
    return None


def check_support(
    archive: Path | None,
    ai_usage: str,
    ai_details: Path | None,
    paper_text: str,
    forbidden_terms: list[str],
    size_limit_mb: float,
    manifest_reviewed: bool,
    content_reviewed: bool,
    ai_details_reviewed: bool,
    report: Report,
) -> None:
    manifest_text = appendix_segment(paper_text)
    if manifest_text is None:
        report.blocked("appendix manifest boundary could not be isolated automatically")
        manifest_text = paper_text
    no_support = "本论文没有支撑材料" in manifest_text
    no_program = "本论文没有用到程序" in manifest_text
    if archive is None:
        if no_support and no_program and ai_usage != "used":
            report.ok("paper declares no supporting materials")
        elif no_support and not no_program:
            report.fail("paper declares no supporting materials although a program was used")
        else:
            report.fail("supporting-material archive is required but was not supplied")
        return

    if no_support:
        report.fail("paper declares no supporting materials but an archive was supplied")
    if not archive.is_file():
        report.fail("supporting-material archive does not exist")
        return
    if archive.suffix.lower() not in {".zip", ".rar"}:
        report.fail("supporting materials must be a .zip or .rar archive")
        return
    if not check_size(archive, size_limit_mb, "supporting-material archive", report):
        return

    archive_names: list[str] = []
    archive_paths: list[str] = []
    member_texts: list[str] = []
    uninspectable_members = 0
    partially_inspected_members = 0
    ai_bytes: bytes | None = None
    ai_member_count = 0
    if archive.suffix.lower() == ".zip" and archive.is_file():
        try:
            with zipfile.ZipFile(archive) as zipped:
                infos = zipped.infolist()
                archive_paths = [item.filename for item in infos]
                archive_names = [item.filename for item in infos if not item.is_dir()]
                if not archive_names:
                    report.fail("ZIP supporting-material archive contains no files")
                normalized_paths = [name.replace("\\", "/").casefold() for name in archive_paths]
                if len(normalized_paths) != len(set(normalized_paths)):
                    report.fail("ZIP contains duplicate member paths")
                encrypted_members = [item for item in infos if item.flag_bits & 0x1]
                if encrypted_members:
                    report.fail(
                        f"ZIP contains {len(encrypted_members)} encrypted member(s) that cannot be validated"
                    )
                if zipped.comment:
                    decoded = decode_text_bytes(zipped.comment)
                    if decoded is None:
                        uninspectable_members += 1
                    else:
                        member_texts.append(decoded)
                for item in infos:
                    if item.comment:
                        decoded = decode_text_bytes(item.comment)
                        if decoded is None:
                            uninspectable_members += 1
                        else:
                            member_texts.append(decoded)
                    if item.extra:
                        decoded = decode_text_bytes(item.extra)
                        if decoded is None:
                            uninspectable_members += 1
                        else:
                            member_texts.append(decoded)
                matches = [
                    item
                    for item in infos
                    if not item.is_dir() and Path(item.filename).name == "AI工具使用详情.pdf"
                ]
                ai_member_count = len(matches)
                if ai_member_count > 1:
                    report.fail("ZIP contains more than one AI工具使用详情.pdf")
                remaining_budget = MAX_ZIP_SCAN_BYTES
                total_expansion = sum(
                    item.file_size for item in infos if not item.is_dir() and item.file_size > 0
                )
                zip_scan_complete = True
                if total_expansion > MAX_ZIP_SCAN_BYTES:
                    report.blocked(
                        "ZIP declared cumulative expansion exceeds the automatic scan budget; "
                        "members will only be inspected within the safe budget"
                    )
                    zip_scan_complete = False
                for item in infos:
                    if item.is_dir():
                        continue
                    if item.flag_bits & 0x1:
                        uninspectable_members += 1
                        zip_scan_complete = False
                        continue
                    blocker = zip_member_scan_blocker(item, remaining_budget)
                    if blocker is not None:
                        report.blocked(blocker)
                        uninspectable_members += 1
                        zip_scan_complete = False
                        continue
                    data = zipped.read(item)
                    remaining_budget -= item.file_size
                    if ai_member_count == 1 and item is matches[0]:
                        ai_bytes = data
                    text, coverage = support_member_text(item.filename, data, report)
                    if text is not None:
                        member_texts.append(text)
                    if coverage == "none":
                        uninspectable_members += 1
                    elif coverage == "partial":
                        partially_inspected_members += 1
                if zip_scan_complete:
                    report.ok("ZIP supporting-material contents are readable within safe scan limits")
        except (OSError, KeyError, RuntimeError, EOFError, zipfile.BadZipFile, zlib.error):
            report.fail("cannot read ZIP supporting-material archive")
    elif archive.suffix.lower() == ".rar":
        if manifest_reviewed and content_reviewed:
            report.ok("RAR manifest, names, content, and metadata received recorded manual review")
        else:
            report.blocked(
                "RAR inspection requires recorded manual evidence before adding both "
                "--support-manifest-reviewed and --support-content-reviewed"
            )

    combined_member_text = "\n".join(member_texts)
    for term_index, term in enumerate(forbidden_terms, 1):
        if term and (
            identity_term_in_text(archive.name, term)
            or any(identity_term_in_text(name, term) for name in archive_paths)
        ):
            report.fail(
                f"forbidden identity term #{term_index} appears in a supporting-material path"
            )
        if term and identity_term_in_text(combined_member_text, term):
            report.fail(
                f"forbidden identity term #{term_index} appears in supporting-material content"
            )

    if archive.suffix.lower() == ".zip" and archive_names:
        manifest_block = support_manifest_block(manifest_text)
        unresolved_items = (
            [
                item
                for item in logical_archive_items(archive_names)
                if not manifest_lists_item(manifest_block, item)
            ]
            if manifest_block is not None
            else list(logical_archive_items(archive_names))
        )
        if (manifest_block is None or unresolved_items) and not manifest_reviewed:
            report.blocked(
                f"{len(unresolved_items)} top-level archive item(s) could not be reconciled "
                "inside the bounded appendix file-list block; review them before adding "
                "--support-manifest-reviewed"
            )
        else:
            report.ok("support archive and appendix manifest were reconciled")

        source_files = [name for name in archive_names if Path(name).suffix.lower() in SOURCE_SUFFIXES]
        if no_program and source_files:
            report.fail("paper declares no program use but the support archive contains source files")
        elif not no_program and not source_files and not manifest_reviewed:
            report.blocked(
                "required runnable source was not recognized automatically; review it before adding "
                "--support-manifest-reviewed"
            )
        elif not no_program:
            report.ok("support archive contains recognized source code or received manifest review")

        review_needed = uninspectable_members + partially_inspected_members
        if review_needed:
            if content_reviewed:
                report.ok(
                    f"{review_needed} partially or non-inspectable archive item(s) received recorded manual identity review"
                )
            else:
                report.blocked(
                    f"{review_needed} partially or non-inspectable archive item(s) require identity and metadata review "
                    "before adding --support-content-reviewed"
                )
        else:
            report.ok("all ZIP member content was inspectable for supplied identity terms")

    if ai_usage != "used":
        if ai_member_count:
            report.fail("no-AI submission unexpectedly contains AI工具使用详情.pdf")
        if ai_details is not None:
            report.warn("AI details file was supplied although AI usage is not-used")
        return

    external_bytes: bytes | None = None
    if ai_details is not None:
        if ai_details.name != "AI工具使用详情.pdf":
            report.fail("AI details file must be named AI工具使用详情.pdf")
        if not ai_details.is_file():
            report.fail("AI details file does not exist")
        elif ai_details.stat().st_size > MAX_ZIP_MEMBER_BYTES:
            report.blocked(
                "external AI details file exceeds the safe automatic read limit"
            )
        else:
            external_bytes = ai_details.read_bytes()

    details_bytes: bytes | None = None
    if archive.suffix.lower() == ".zip":
        if ai_member_count == 0:
            report.fail("used-AI ZIP must contain exactly one AI工具使用详情.pdf")
        elif ai_member_count > 1:
            pass
        elif ai_bytes is None:
            report.blocked(
                "AI工具使用详情.pdf is present but could not be expanded within safe automatic scan limits"
            )
        else:
            details_bytes = ai_bytes
            report.ok("used-AI ZIP contains exactly one AI工具使用详情.pdf")
            if external_bytes is not None:
                if hashlib.sha256(external_bytes).digest() != hashlib.sha256(ai_bytes).digest():
                    report.fail("external AI details file differs from the copy inside the ZIP")
                else:
                    report.ok("external AI details file matches the ZIP member")
    elif archive.suffix.lower() == ".rar":
        if not manifest_reviewed:
            report.blocked(
                "AI details presence inside RAR requires manifest review and --support-manifest-reviewed"
            )
        if external_bytes is None:
            report.blocked("RAR AI details semantics require an extracted --ai-details file")
        else:
            details_bytes = external_bytes

    details_text = None
    if details_bytes is not None:
        details_text, _has_images = pdf_text_from_bytes(
            details_bytes, report, "AI工具使用详情.pdf"
        )
    check_ai_details_text(details_text, ai_details_reviewed, report)


def main() -> int:
    args = parse_args()
    report = Report()
    try:
        forbidden_terms = [term.strip() for term in args.forbidden_term if term.strip()]
        if args.identity_terms_complete and forbidden_terms:
            report.ok("known identity-term list was confirmed complete and is non-empty")
        elif args.identity_terms_complete:
            report.fail("identity-term completeness cannot be confirmed with an empty term list")
        else:
            report.blocked(
                "identity terms were not confirmed complete; pass every known identity value "
                "with --forbidden-term and then add --identity-terms-complete"
            )

        paper_size_ok = check_size(
            args.paper_pdf,
            args.paper_size_limit_mb,
            "electronic paper",
            report,
        )
        source = collect_source_text(args.paper_source, report)
        inferred_ai = check_source(source, args.ai_usage, report) if source else args.ai_usage

        data = pdf_data(args.paper_pdf, report) if paper_size_ok else None
        paper_text = (
            check_paper_pdf(
                data,
                forbidden_terms,
                args.body_page_limit,
                inferred_ai,
                report,
            )
            if data
            else ""
        )

        check_support(
            args.support_archive,
            inferred_ai,
            args.ai_details,
            paper_text or source,
            forbidden_terms,
            args.support_size_limit_mb,
            args.support_manifest_reviewed,
            args.support_content_reviewed,
            args.ai_details_reviewed,
            report,
        )
    except Exception as exc:
        report.blocked(
            "submission checker encountered an internal error: " + type(exc).__name__
        )
    return report.finish()


if __name__ == "__main__":
    sys.exit(main())
