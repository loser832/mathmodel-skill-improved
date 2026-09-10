#!/usr/bin/env bash
set -u

usage() {
  cat <<'EOF'
Usage:
  writing_check.sh [paper-dir]
  writing_check.sh --paper-dir DIR [options]

Options:
  --root-dir DIR          Project root. Defaults to the parent of paper-dir.
  --main FILE            Paper entry file. Supports both Typst (main.typ) and LaTeX (main.tex). Defaults to <paper-dir>/main.typ, then main.tex.
  --sections-dir DIR     Section directory. Defaults to <paper-dir>/sections when it exists.
  --references FILE      Reference file. Defaults to <paper-dir>/references.typ when it exists.
  --figures-dir DIR      Figure directory. Defaults to <root-dir>/figures when it exists.
  --results-file FILE    Result summary file. Defaults to <root-dir>/reports/RESULTS_REPORT.md when it exists.
  --problem-analysis FILE
                          Problem analysis file, used only for soft consistency checks.
  --all-results FILE     Aggregated JSON result file. Defaults to <figures-dir>/all_results.json.
  --quality-profile NAME Writing quality profile: general (default) or cumcm.
  --problem-title TEXT   Original problem title for verbatim-title comparison.
  --internal-term TEXT   Extra internal workflow term to reject in paper body. Repeatable.
  --no-internal-check    Skip internal workflow filename leak check.
  -h, --help             Show this help.

The script intentionally accepts paths from the caller. Defaults are convenience
fallbacks only; the verification skill should infer the project layout and pass
the actual files it wants checked.
EOF
}

PAPER_DIR="${PAPER_DIR:-}"
ROOT_DIR="${ROOT_DIR:-}"
MAIN_FILE="${MAIN_FILE:-}"
SECTIONS_DIR="${SECTIONS_DIR:-}"
REFERENCES_FILE="${REFERENCES_FILE:-}"
FIGURES_DIR="${FIGURES_DIR:-}"
RESULTS_FILE="${RESULTS_FILE:-}"
PROBLEM_ANALYSIS_FILE="${PROBLEM_ANALYSIS_FILE:-}"
ALL_RESULTS_FILE="${ALL_RESULTS_FILE:-}"
QUALITY_PROFILE="${QUALITY_PROFILE:-general}"
PROBLEM_TITLE="${PROBLEM_TITLE:-}"
NO_INTERNAL_CHECK="${NO_INTERNAL_CHECK:-0}"
EXTRA_INTERNAL_TERMS=()
POSITIONAL=()

while [ "$#" -gt 0 ]; do
  case "$1" in
    --paper-dir)
      PAPER_DIR="${2:-}"
      shift 2
      ;;
    --root-dir)
      ROOT_DIR="${2:-}"
      shift 2
      ;;
    --main)
      MAIN_FILE="${2:-}"
      shift 2
      ;;
    --sections-dir)
      SECTIONS_DIR="${2:-}"
      shift 2
      ;;
    --references)
      REFERENCES_FILE="${2:-}"
      shift 2
      ;;
    --figures-dir)
      FIGURES_DIR="${2:-}"
      shift 2
      ;;
    --results-file)
      RESULTS_FILE="${2:-}"
      shift 2
      ;;
    --problem-analysis)
      PROBLEM_ANALYSIS_FILE="${2:-}"
      shift 2
      ;;
    --all-results)
      ALL_RESULTS_FILE="${2:-}"
      shift 2
      ;;
    --quality-profile)
      QUALITY_PROFILE="${2:-}"
      shift 2
      ;;
    --problem-title)
      PROBLEM_TITLE="${2:-}"
      shift 2
      ;;
    --internal-term)
      EXTRA_INTERNAL_TERMS+=("${2:-}")
      shift 2
      ;;
    --no-internal-check)
      NO_INTERNAL_CHECK=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    --)
      shift
      while [ "$#" -gt 0 ]; do
        POSITIONAL+=("$1")
        shift
      done
      ;;
    -*)
      echo "ERROR: unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
    *)
      POSITIONAL+=("$1")
      shift
      ;;
  esac
done

if [ -z "$PAPER_DIR" ] && [ "${#POSITIONAL[@]}" -gt 0 ]; then
  PAPER_DIR="${POSITIONAL[0]}"
fi

if [ -z "$PAPER_DIR" ]; then
  if [ -f "main.typ" ] || [ -f "main.tex" ]; then
    PAPER_DIR="."
  else
    CANDIDATE="$(find . -maxdepth 3 -type f \( -name main.typ -o -name main.tex \) -print 2>/dev/null | head -n 1 || true)"
    if [ -n "$CANDIDATE" ]; then
      PAPER_DIR="$(dirname "$CANDIDATE")"
    else
      PAPER_DIR="paper"
    fi
  fi
fi

if [ -z "$ROOT_DIR" ]; then
  if [ "$PAPER_DIR" = "." ]; then
    ROOT_DIR="."
  else
    ROOT_DIR="$(cd "$PAPER_DIR/.." 2>/dev/null && pwd || dirname "$PAPER_DIR")"
  fi
fi

if [ -z "$MAIN_FILE" ]; then
  if [ -f "$PAPER_DIR/main.typ" ]; then
    MAIN_FILE="$PAPER_DIR/main.typ"
  elif [ -f "$PAPER_DIR/main.tex" ]; then
    MAIN_FILE="$PAPER_DIR/main.tex"
  fi
fi

if [ -z "$SECTIONS_DIR" ] && [ -d "$PAPER_DIR/sections" ]; then
  SECTIONS_DIR="$PAPER_DIR/sections"
fi

if [ -z "$REFERENCES_FILE" ]; then
  if [ -f "$PAPER_DIR/references.typ" ]; then
    REFERENCES_FILE="$PAPER_DIR/references.typ"
  elif [ -f "$PAPER_DIR/references.tex" ]; then
    REFERENCES_FILE="$PAPER_DIR/references.tex"
  fi
fi

if [ -z "$FIGURES_DIR" ] && [ -d "$ROOT_DIR/figures" ]; then
  FIGURES_DIR="$ROOT_DIR/figures"
fi

if [ -z "$RESULTS_FILE" ]; then
  if [ -f "$ROOT_DIR/reports/RESULTS_REPORT.md" ]; then
    RESULTS_FILE="$ROOT_DIR/reports/RESULTS_REPORT.md"
  elif [ -f "$ROOT_DIR/RESULTS_REPORT.md" ]; then
    RESULTS_FILE="$ROOT_DIR/RESULTS_REPORT.md"
  elif [ -f "$ROOT_DIR/RESULTS_REPORT" ]; then
    RESULTS_FILE="$ROOT_DIR/RESULTS_REPORT"
  fi
fi

if [ -z "$PROBLEM_ANALYSIS_FILE" ] && [ -f "$ROOT_DIR/PROBLEM_ANALYSIS.md" ]; then
  PROBLEM_ANALYSIS_FILE="$ROOT_DIR/PROBLEM_ANALYSIS.md"
fi

if [ -z "$ALL_RESULTS_FILE" ] && [ -n "$FIGURES_DIR" ] && [ -f "$FIGURES_DIR/all_results.json" ]; then
  ALL_RESULTS_FILE="$FIGURES_DIR/all_results.json"
fi

export PAPER_DIR ROOT_DIR MAIN_FILE SECTIONS_DIR REFERENCES_FILE FIGURES_DIR
export RESULTS_FILE PROBLEM_ANALYSIS_FILE ALL_RESULTS_FILE NO_INTERNAL_CHECK
export QUALITY_PROFILE PROBLEM_TITLE
if [ "${#EXTRA_INTERNAL_TERMS[@]}" -gt 0 ]; then
  EXTRA_INTERNAL_TERMS_STR="$(printf '%s\n' "${EXTRA_INTERNAL_TERMS[@]}")"
else
  EXTRA_INTERNAL_TERMS_STR=""
fi
export EXTRA_INTERNAL_TERMS_STR

python3 - <<'PY'
import json
import os
import re
import sys
from pathlib import Path

exit_code = 0

def fail(msg):
    global exit_code
    print(f"FAIL: {msg}")
    exit_code = 1

def warn(msg):
    print(f"WARN: {msg}")

def info(msg):
    print(f"INFO: {msg}")

def opt_path(name):
    value = os.environ.get(name, "").strip()
    return Path(value) if value else None

paper = Path(os.environ["PAPER_DIR"])
root = Path(os.environ["ROOT_DIR"])
main = Path(os.environ["MAIN_FILE"])
sections_dir = opt_path("SECTIONS_DIR")
refs = opt_path("REFERENCES_FILE")
figures_dir = opt_path("FIGURES_DIR")
results_file = opt_path("RESULTS_FILE")
problem_analysis = opt_path("PROBLEM_ANALYSIS_FILE")
all_results = opt_path("ALL_RESULTS_FILE")
quality_profile = os.environ.get("QUALITY_PROFILE", "general").strip().lower()
problem_title = os.environ.get("PROBLEM_TITLE", "").strip()
no_internal_check = os.environ.get("NO_INTERNAL_CHECK") == "1"
extra_internal_terms = [
    item for item in os.environ.get("EXTRA_INTERNAL_TERMS_STR", "").splitlines()
    if item.strip()
]

def read(path):
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="ignore")

def rel(path):
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except Exception:
        return str(path)

def extract_calls(text, name):
    calls = []
    pattern = re.compile(r"#" + re.escape(name) + r"\s*\(")
    for match in pattern.finditer(text):
        open_pos = text.find("(", match.start())
        depth = 0
        in_string = False
        escape = False
        for idx in range(open_pos, len(text)):
            ch = text[idx]
            if in_string:
                if escape:
                    escape = False
                elif ch == "\\":
                    escape = True
                elif ch == '"':
                    in_string = False
                continue
            if ch == '"':
                in_string = True
            elif ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth == 0:
                    calls.append((match.start(), idx + 1, text[open_pos + 1:idx]))
                    break
    return calls

def remove_spans(text, spans):
    if not spans:
        return text
    parts = []
    last = 0
    for start, end, _ in spans:
        parts.append(text[last:start])
        last = end
    parts.append(text[last:])
    return "".join(parts)

def unique_paths(paths):
    seen = set()
    out = []
    for path in paths:
        key = str(path.resolve()) if path.exists() else str(path)
        if key not in seen:
            out.append(path)
            seen.add(key)
    return out

def section_sort_key(path):
    match = re.match(r"^(\d+)[_-](.*)$", path.name)
    if match:
        return (0, int(match.group(1)), match.group(2))
    return (1, path.name)

def extract_latex_braced_args(text, command, arg_count):
    """Return top-level braced arguments for the first LaTeX command call."""
    pattern = re.compile(r"\\" + re.escape(command) + r"\s*")
    for match in pattern.finditer(text):
        args = []
        pos = match.end()
        valid = True
        for _ in range(arg_count):
            while pos < len(text) and text[pos].isspace():
                pos += 1
            if pos >= len(text) or text[pos] != "{":
                valid = False
                break
            depth = 0
            start = pos + 1
            escaped = False
            for idx in range(pos, len(text)):
                ch = text[idx]
                if escaped:
                    escaped = False
                    continue
                if ch == "\\":
                    escaped = True
                    continue
                if ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        args.append(text[start:idx])
                        pos = idx + 1
                        break
            else:
                valid = False
                break
        if valid and len(args) == arg_count:
            return args
    return []

def clean_source_text(text):
    text = re.sub(r"%.*", " ", text)
    text = re.sub(r"//.*", " ", text)
    text = re.sub(r"\\[A-Za-z@]+\*?(?:\[[^\]]*\])?", " ", text)
    text = re.sub(r"[#\\{}\[\]$]", " ", text)
    return re.sub(r"\s+", " ", text).strip()

def code_block_is_large(block):
    nonblank = [line for line in block.splitlines() if line.strip()]
    return len(nonblank) >= 20 or len(block) >= 1000

info(f"paper dir: {paper}")
info(f"root dir: {root}")
info(f"main file: {main}")
if sections_dir:
    info(f"sections dir: {sections_dir}")
if figures_dir:
    info(f"figures dir: {figures_dir}")
if results_file:
    info(f"results file: {results_file}")

if not paper.exists():
    fail(f"paper directory not found: {paper}")

if not main.exists():
    fail(f"missing main paper file: {main}")
    sys.exit(exit_code)

# Detect engine by main file extension
is_latex = main.suffix == ".tex"
is_typst = main.suffix == ".typ"
engine_name = "LaTeX" if is_latex else "Typst"
info(f"detected engine: {engine_name} (main suffix: {main.suffix})")

if quality_profile not in {"general", "cumcm"}:
    fail(f"unknown quality profile: {quality_profile}; expected general or cumcm")
else:
    info(f"writing quality profile: {quality_profile}")

main_text = read(main)

# Section file extension matches engine
section_ext = "*.tex" if is_latex else "*.typ"
if sections_dir and sections_dir.exists():
    section_files = sorted(sections_dir.glob(section_ext), key=section_sort_key)
elif paper.exists():
    excluded = {main.resolve()}
    if refs:
        excluded.add(refs.resolve())
    section_files = [
        path for path in sorted(paper.rglob(section_ext), key=section_sort_key)
        if path.resolve() not in excluded
    ]
    if section_files:
        warn(f"sections dir not supplied/found; using other {section_ext} files under paper dir as body sections")
else:
    section_files = []

info(f"section file count: {len(section_files)}")
if not section_files:
    warn(f"no separate section {section_ext} files detected; treating paper as a single-file {engine_name} document")

# Include/input detection: Typst uses #include("..."), LaTeX uses \input{...} or \include{...}
if is_typst:
    include_re = re.compile(r'#include\(\s*"([^"]+\.typ)"\s*\)')
    includes = include_re.findall(main_text)
else:
    include_re = re.compile(r'\\(?:input|include)\s*\{([^}]+)\}')
    raw_includes = [inc.strip() for inc in include_re.findall(main_text)]
    # LaTeX \input{name} may omit .tex extension; normalize by appending .tex if missing
    includes = [inc if inc.endswith(".tex") else inc + ".tex" for inc in raw_includes]
include_paths = [(main.parent / inc).resolve() for inc in includes]
include_names = [Path(inc).name for inc in includes]

info(f"main include count: {len(includes)}")
seen = set()
for name in include_names:
    if name in seen:
        fail(f"duplicate {engine_name} include: {name}")
    seen.add(name)

for inc, path in zip(includes, include_paths):
    if not path.exists():
        fail(f"included {engine_name} file does not exist: {inc}")

actual_names = [path.name for path in section_files]
if includes:
    included_set = set(include_names)
    for name in actual_names:
        if name not in included_set and not name.startswith("A_"):
            warn(f"body section file not included by main: {name}")
else:
    warn(f"main has no include/input calls; skip include order checks")

def leading_number(name):
    match = re.match(r"^(\d+)[_-]", name)
    return int(match.group(1)) if match else None

numbers = [leading_number(name) for name in include_names if leading_number(name) is not None]
if numbers and numbers != sorted(numbers):
    fail(f"section include order is not ascending: {numbers}")
if numbers:
    expected = list(range(min(numbers), max(numbers) + 1))
    missing = [num for num in expected if num not in numbers]
    if missing:
        warn(f"numbered section sequence has gaps: {missing}")

if problem_analysis and problem_analysis.exists():
    pa = read(problem_analysis)
    problem_hits = re.findall(r"(?:子问题|问题)\s*[一二三四五六七八九十0-9]+", pa)
    expected_problem_count = len(set(problem_hits))
    paper_problem_sections = [name for name in include_names or actual_names if re.search(r"problem|问题|q\d", name, re.I)]
    if expected_problem_count and paper_problem_sections and len(paper_problem_sections) < min(expected_problem_count, 3):
        warn(
            "paper problem sections may be fewer than analysis subproblems: "
            f"paper={len(paper_problem_sections)}, analysis={expected_problem_count}"
        )
else:
    info("problem analysis file not supplied/found; skip subproblem count check")

placeholder_re = re.compile(
    r"PLACEHOLDER|TODO|TBD|XXX|待补充|待续写|这里补|示例数据|待完善|"
    r"【[^】]+】"
)
default_internal_terms = [
    "RESULTS_REPORT",
    "ANALYSIS_MODELING_REPORT.md",
    "PROBLEM_ANALYSIS.md",
    "CLAUDE.md",
    "figures/*.json",
    "_tmp/",
]
internal_terms = default_internal_terms + extra_internal_terms
if results_file:
    internal_terms.append(results_file.name)
if problem_analysis:
    internal_terms.append(problem_analysis.name)
if all_results:
    internal_terms.append(all_results.name)
internal_terms = sorted(set(term for term in internal_terms if term))
internal_re = re.compile("|".join(re.escape(term) for term in internal_terms)) if internal_terms else None

typ_files = unique_paths([main] + section_files + ([refs] if refs and refs.exists() else []) + sorted(paper.glob(section_ext)))
file_texts = []
combined = []
section_titles = []

for path in typ_files:
    if not path.exists():
        continue
    text = read(path)
    file_texts.append((path, text))
    combined.append(text)
    path_rel = rel(path)

    if placeholder_re.search(text):
        fail(f"placeholder text remains in {path_rel}")

    is_appendix = path.name.startswith("A_") or "appendix" in path.name.lower()
    if not no_internal_check and internal_re and internal_re.search(text):
        if is_appendix:
            warn(f"internal workflow term appears in appendix: {path_rel}")
        else:
            fail(f"internal workflow term leaked into paper text: {path_rel}")

    if path in section_files:
        body = text.strip()
        info(f"section length: {path.name} {len(body)} chars")
        if len(body) < 800 and not path.name.startswith("A_"):
            warn(f"section is short: {path.name} ({len(body)} chars)")

        # Auxiliary sections (appendix code, abstracts, appendices) may
        # legitimately omit a level-1 heading because the title is rendered
        # by main.typ/main.tex directly.
        lower_name = path.name.lower()
        is_aux_section = (
            path.name.startswith("A_")
            or lower_name.startswith("abstract")
            or lower_name.startswith("appendices")
        )

        if is_typst:
            # Typst heading check: `= Title` (space after =)
            malformed_headings = [
                line.strip()
                for line in text.splitlines()
                if re.match(r"^={1,6}(?![=\s]).+", line)
            ]
            for line in malformed_headings[:5]:
                fail(f"Typst heading is missing a space after '=' in {path.name}: {line[:80]}")
            heading = re.search(r"(?m)^=\s+.+", text)
            if not heading and not is_aux_section:
                fail(f"section has no level-1 Typst heading: {path.name}")
            if heading:
                title = heading.group(0).lstrip("= ").strip()
                section_titles.append((path.name, title))
                if re.search(r"problem\d+|q\d", path.name, re.I) and not re.search(r"问题|Problem|Question", title, re.I):
                    warn(f"problem section title may not match filename: {path.name} -> {title}")
            if re.search(r"(?m)^={3,}\s+", text):
                warn(f"deep heading level appears in section: {path.name}")
            list_count = len(re.findall(r"#(?:enum|list)\s*\(", text))
            if list_count >= 3:
                warn(f"many lists in section, consider prose: {path.name} ({list_count})")
            figure_calls = extract_calls(text, "figure")
            text_without_figures = remove_spans(text, figure_calls)
            if len(figure_calls) >= 2 and len(text_without_figures.strip()) < 1000:
                warn(f"many figures but little surrounding prose: {path.name}")

            if not is_appendix:
                fenced_blocks = re.findall(r"```.*?```", text, re.S)
                raw_blocks = [body for _, _, body in extract_calls(text, "raw") if "block:" in body]
                for block in fenced_blocks + raw_blocks:
                    if code_block_is_large(block):
                        fail(f"large code block appears in paper body; move complete code to appendix/support files: {path.name}")
                        break
        else:
            # LaTeX heading check: \section{...}
            section_headings = re.findall(r"\\section\{([^}]*)\}", text)
            subsection_headings = re.findall(r"\\subsection\{([^}]*)\}", text)
            if not section_headings and not subsection_headings and not is_aux_section:
                fail(f"section has no \\section{{}} heading: {path.name}")
            for title in section_headings:
                section_titles.append((path.name, title))
                if re.search(r"problem\d+|q\d", path.name, re.I) and not re.search(r"问题|Problem|Question", title, re.I):
                    warn(f"problem section title may not match filename: {path.name} -> {title}")
            list_count = len(re.findall(r"\\begin\{(?:itemize|enumerate)\}", text))
            if list_count >= 3:
                warn(f"many lists in section, consider prose: {path.name} ({list_count})")
            figure_env_count = len(re.findall(r"\\begin\{figure\}", text))
            if figure_env_count >= 2 and len(text) < 2000:
                warn(f"many figures but little surrounding prose: {path.name}")

            if not is_appendix:
                code_blocks = [
                    match.group(2)
                    for match in re.finditer(
                        r"\\begin\{(lstlisting|verbatim|minted)\}.*?\n(.*?)\\end\{\1\}",
                        text,
                        re.S,
                    )
                ]
                for block in code_blocks:
                    if code_block_is_large(block):
                        fail(f"large code block appears in paper body; move complete code to appendix/support files: {path.name}")
                        break

paper_text = "\n".join(combined)

if section_titles:
    info("section title order:")
    for idx, (name, title) in enumerate(section_titles, 1):
        info(f"  {idx}. {name} -> {title}")
    titles = [title for _, title in section_titles]
    if len(titles) != len(set(titles)):
        fail("duplicate level-1 section titles detected")

# Structural quality recommendations are not submission-format rules. They
# remain warnings so a justified competition-specific structure is not rejected.
body_text = "\n".join(
    text
    for path, text in file_texts
    if path in section_files and not path.name.startswith("A_")
)
if not re.search(r"研究意义|研究价值|实际意义|practical significance|research significance", body_text, re.I):
    warn("writing quality: research significance/value is not explicit")
if not re.search(r"文献综述|研究现状|相关工作|国内外研究|literature review|related work", body_text, re.I):
    warn("writing quality: literature review/related work is not explicit")
if not re.search(r"结论|总结|conclusion", body_text, re.I):
    warn("writing quality: no explicit conclusion section detected")
if not re.search(r"建议|启示|recommendation", body_text, re.I):
    warn("writing quality: no explicit recommendation/implication detected")

# Title, abstract and keyword checks. The CUMCM profile adds advisory checks
# from writing guidance; they are separate from official submission hard gates.
if is_latex:
    title_args = extract_latex_braced_args(main_text, "papertitle", 1)
    abstract_args = extract_latex_braced_args(main_text, "abstractcn", 2)
    paper_title = clean_source_text(title_args[0]) if title_args else ""
    abstract_text = abstract_args[0] if len(abstract_args) == 2 else ""
    keyword_text = clean_source_text(abstract_args[1]) if len(abstract_args) == 2 else ""
else:
    title_match = re.search(r"#paper-title\s*\[\[(.*?)\]\]", main_text, re.S)
    abstract_match = re.search(
        r"#abstract-cn\s*\[\s*\[(.*?)\]\s*\]\s*\[\s*\[(.*?)\]\s*\]",
        main_text,
        re.S,
    )
    paper_title = clean_source_text(title_match.group(1)) if title_match else ""
    abstract_text = abstract_match.group(1) if abstract_match else ""
    keyword_text = clean_source_text(abstract_match.group(2)) if abstract_match else ""

if quality_profile == "cumcm":
    if not paper_title:
        warn("CUMCM writing quality: paper title could not be extracted for review")
    if problem_title and paper_title:
        norm_paper = re.sub(r"[\W_]+", "", paper_title, flags=re.UNICODE).lower()
        norm_problem = re.sub(r"[\W_]+", "", problem_title, flags=re.UNICODE).lower()
        if norm_paper and norm_paper == norm_problem:
            warn("CUMCM writing quality: paper title repeats the supplied problem title verbatim")
    elif not problem_title:
        info("problem title not supplied; verbatim-title comparison NOT_RUN")

    if not abstract_text:
        warn("CUMCM writing quality: abstract could not be extracted for review")
    else:
        if re.search(r"#figure\s*\(|#table\s*\(|\\(?:begin\{(?:figure|table|tabular)|includegraphics)", abstract_text):
            warn("CUMCM writing quality: abstract contains a figure or table construct")
        if re.search(r"```|#raw\s*\(|\\begin\{(?:lstlisting|verbatim|minted)\}", abstract_text):
            warn("CUMCM writing quality: abstract contains a code block")
        if re.search(r"\\begin\{(?:equation|align|gather|multline)\*?\}|\\\[|(?m:^\s*\$[^$\n]{20,}\$\s*$)", abstract_text):
            warn("CUMCM writing quality: abstract contains display/complex mathematics; review manually")

    if not keyword_text:
        warn("CUMCM writing quality: keywords could not be extracted for review")
    else:
        keywords = [item.strip() for item in re.split(r"[；;]", keyword_text) if item.strip()]
        if len(keywords) == 1 and re.search(r"[,，、]", keyword_text):
            warn("CUMCM writing quality: separate keywords with semicolons, not commas")
            keywords = [item.strip() for item in re.split(r"[,，、]", keyword_text) if item.strip()]
        if not 3 <= len(keywords) <= 5:
            warn(f"CUMCM writing quality: expected 3-5 keywords, found {len(keywords)}")
        software_re = re.compile(
            r"^(?:python|matlab|mathematica|excel|spss|stata|r语言|r language|"
            r"numpy|pandas|scipy|sklearn|scikit-learn|xgboost|lingo|gurobi|cplex|"
            r"typst|latex|wps|word)$",
            re.I,
        )
        software_hits = [item for item in keywords if software_re.fullmatch(item)]
        if software_hits:
            warn("CUMCM writing quality: software/tool names used as keywords: " + ", ".join(software_hits))

# Image reference check: Typst uses image("..."), LaTeX uses \includegraphics{...}
if is_typst:
    image_re = re.compile(r'image\(\s*"([^"]+)"')
else:
    image_re = re.compile(r'\\includegraphics\s*(?:\[[^\]]*\])?\s*\{([^}]+)\}')
for path, text in file_texts:
    for ref in image_re.findall(text):
        # Typst resolves relative images from the source file; LaTeX uses the
        # compilation directory, which this workflow fixes to main.parent.
        image_base = path.parent if is_typst else main.parent
        target = (image_base / ref).resolve()
        if not target.is_file():
            fail(f"referenced image does not exist from {rel(path)} "
                 f"(image base: {rel(image_base)}): {ref}")

if figures_dir and figures_dir.exists():
    for fig in sorted(figures_dir.glob("*.pdf")):
        if fig.name not in paper_text:
            warn(f"figure PDF not referenced in paper: {fig.name}")
else:
    info("figures dir not supplied/found; skip unused figure check")

# Figure/table caption, label and automatic-numbering checks
if is_typst:
    direct_typst_figures = []
    for path, text in file_texts:
        if path not in section_files:
            continue
        for start, end, body in extract_calls(text, "figure"):
            direct_typst_figures.append((path, text, start, end, body))
    for path, text, _, end, body in direct_typst_figures:
        if "caption:" not in body:
            fail("figure without caption")
            continue
        cap_match = re.search(r"caption:\s*\[(.*?)\]", body, re.S)
        if cap_match:
            cap = re.sub(r"\s+", " ", cap_match.group(1)).strip()
            if re.match(r"^(?:图|表|Figure|Table)\s*[0-9一二三四五六七八九十]+(?:[.．、:：-]|\s)", cap, re.I):
                fail(f"manual number prefix in Typst caption; use automatic numbering: {cap[:80]}")
            if len(cap) > 80:
                warn(f"long figure caption: {cap[:80]}...")
            if len(cap) < 4:
                warn("very short figure caption")
        if not re.match(r"\s*<[-\w:.]+>", text[end:end + 100]):
            warn(f"Typst figure/table has no adjacent label for cross-reference: {rel(path)}")
else:
    # LaTeX: figures and tables use captions plus labels; equations use labels.
    figure_blocks = re.findall(r"\\begin\{figure\*?\}.*?\\end\{figure\*?\}", paper_text, re.S)
    table_blocks = re.findall(r"\\begin\{table\*?\}.*?\\end\{table\*?\}", paper_text, re.S)
    for kind, block in [("figure", item) for item in figure_blocks] + [("table", item) for item in table_blocks]:
        cap_match = re.search(r"\\caption\{([^}]*)\}", block)
        if not cap_match:
            fail(f"LaTeX {kind} without \\caption{{}}")
            continue
        cap = re.sub(r"\s+", " ", cap_match.group(1)).strip()
        if re.match(r"^(?:图|表|Figure|Table)\s*[0-9一二三四五六七八九十]+(?:[.．、:：-]|\s)", cap, re.I):
            fail(f"manual number prefix in LaTeX caption; use automatic numbering: {cap[:80]}")
        if len(cap) > 80:
            warn(f"long figure caption: {cap[:80]}...")
        if len(cap) < 4:
            warn("very short figure caption")
        if not re.search(r"\\label\{[^}]+\}", block):
            warn(f"LaTeX {kind} has no \\label{{}} for cross-reference")

    equation_blocks = re.findall(
        r"\\begin\{(?:equation|align|gather|multline)\}(.*?)\\end\{(?:equation|align|gather|multline)\}",
        paper_text,
        re.S,
    )
    for block in equation_blocks:
        if "\\label{" not in block:
            warn("numbered LaTeX display equation has no \\label{} for cross-reference")
    if re.search(r"\\tag\s*\{\s*\d+[A-Za-z]?\s*\}", paper_text):
        fail("manual LaTeX equation tag detected; use automatic equation numbering")

# Literal source references drift after editing; source must use label/ref syntax.
hardcoded_ref_re = re.compile(
    r"(?:如|见|由|根据|in|see)?\s*(?:图|表|式|Figure|Table|Equation|Eq\.)\s*"
    r"(?:[（(]\s*)?[0-9]+(?:[.-][0-9]+)*(?:\s*[）)])?",
    re.I,
)
for path, text in file_texts:
    if path not in section_files or path.name.startswith("A_"):
        continue
    scrubbed = re.sub(r"\\(?:ref|eqref|autoref|cref)\{[^}]+\}", "", text)
    scrubbed = re.sub(r"@[-\w:.]+", "", scrubbed)
    scrubbed = re.sub(r"(?:caption:\s*\[[^\]]*\]|\\caption\{[^}]*\})", "", scrubbed, flags=re.S)
    match = hardcoded_ref_re.search(scrubbed)
    if match:
        fail(f"hard-coded figure/table/equation reference in {rel(path)}: {match.group(0).strip()}")

if refs and refs.exists():
    refs_text = read(refs)
    if len(refs_text.strip()) < 80:
        warn(f"{rel(refs)} looks very short")
    if is_typst:
        citation_re = r"@\w[\w:-]*|#cite\("
    else:
        citation_re = r"\\cite\w*\{[^}]+\}"
    if re.search(citation_re, paper_text):
        info("citation markers detected")
    else:
        warn(f"{rel(refs)} exists but no citation markers detected in paper")
else:
    warn("references file not supplied/found; skip reference completeness check")

if results_file and results_file.exists():
    results_text = read(results_file)
    metric_names = re.findall(
        r"(?i)\b(?:rmse|mae|mape|r2|score|objective|accuracy|precision|recall|f1|"
        r"权重|目标值|误差|得分)\b",
        results_text,
    )
    if metric_names and not any(name.lower() in paper_text.lower() for name in metric_names[:20]):
        warn("metrics appear in result file but are hard to find in paper text")
else:
    info("results file not supplied/found; skip metric consistency scan")

if all_results and all_results.exists():
    try:
        data = json.loads(read(all_results))
        nums = []

        def walk(value):
            if isinstance(value, dict):
                for item in value.values():
                    walk(item)
            elif isinstance(value, list):
                for item in value:
                    walk(item)
            elif isinstance(value, (int, float)):
                nums.append(value)

        walk(data)
        key_nums = []
        for num in nums[:100]:
            if abs(num) >= 1:
                key_nums.append(str(round(num, 4)).rstrip("0").rstrip("."))
        if key_nums and not any(num and num in paper_text for num in key_nums[:30]):
            warn("numeric values from all-results JSON are hard to find in paper")
    except Exception as exc:
        warn(f"cannot parse all-results JSON: {exc}")
else:
    info("all-results JSON not supplied/found; skip JSON numeric scan")

if exit_code == 0:
    print("PASS: writing text gate passed")
else:
    print("FAIL: writing text gate failed")

sys.exit(exit_code)
PY
