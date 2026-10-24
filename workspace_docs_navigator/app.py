"""Local Markdown workspace navigator.

Run from this folder with: python app.py
Then open http://127.0.0.1:8765

The server never sends workspace content anywhere. It serves only on loopback
and indexes Markdown files that live below the repository root.
"""

from __future__ import annotations

import html
import json
import posixpath
import re
import sys
import webbrowser
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import RLock
from urllib.parse import parse_qs, quote, urlparse


APP_DIR = Path(__file__).resolve().parent
WORKSPACE_ROOT = APP_DIR.parent.resolve()
HOST = "127.0.0.1"
PORT = 8767
NAVIGATOR_VERSION = "2026.10.13-map2"
MAX_DOCUMENT_BYTES = 2_000_000

SKIPPED_DIRECTORY_NAMES = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "dist",
    "build",
    ".vite",
    ".next",
    ".obsidian",
}

THEME_RULES = {
    "Architecture": ("architecture", "design", "system", "pipeline", "component", "diagram"),
    "Planning": ("prd", "plan", "roadmap", "task", "requirement", "scope", "brief"),
    "Research": ("research", "paper", "dataset", "evaluation", "literature", "study"),
    "Implementation": ("api", "backend", "frontend", "code", "setup", "build", "test", "deployment"),
    "Memory & handoff": ("memory", "handoff", "context", "session", "decision", "checkpoint"),
    "Product": ("product", "user", "feature", "experience", "privacy", "safety"),
}


def safe_read(path: Path) -> str:
    """Read common UTF encodings without failing the whole index on one file."""
    raw = path.read_bytes()
    if len(raw) > MAX_DOCUMENT_BYTES:
        return ""
    for encoding in ("utf-8-sig", "utf-8", "utf-16"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def first_heading(content: str) -> str:
    for line in content.splitlines():
        match = re.match(r"^#\s+(.+?)\s*$", line)
        if match:
            return match.group(1).strip()
    return ""


def headings(content: str, limit: int = 40) -> list[dict[str, object]]:
    found: list[dict[str, object]] = []
    for line_number, line in enumerate(content.splitlines(), start=1):
        match = re.match(r"^(#{1,6})\s+(.+?)\s*#*\s*$", line)
        if match:
            found.append({"text": match.group(2).strip(), "level": len(match.group(1)), "line": line_number})
        if len(found) >= limit:
            break
    return found


def clean_preview(content: str, limit: int = 300) -> str:
    text = re.sub(r"```.*?```", " ", content, flags=re.DOTALL)
    text = re.sub(r"!?(?:\[[^\]]*\]\([^)]*\))", " ", text)
    text = re.sub(r"[#>*_`|]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit] + ("…" if len(text) > limit else "")


def classify(relative_path: str, content: str, doc_headings: list[dict[str, object]]) -> list[str]:
    haystack = f"{relative_path} {' '.join(str(item['text']) for item in doc_headings)} {content[:4000]}".lower()
    labels = [label for label, needles in THEME_RULES.items() if any(needle in haystack for needle in needles)]
    return labels or ["General"]


class MarkdownIndex:
    def __init__(self, root: Path) -> None:
        self.root = root
        self._documents: list[dict[str, object]] = []
        self._contents: dict[str, str] = {}
        self._edges: list[dict[str, str]] = []
        self._lock = RLock()
        self.reindex()

    def reindex(self) -> int:
        documents: list[dict[str, object]] = []
        contents: dict[str, str] = {}
        for path in self.root.rglob("*.md"):
            try:
                relative = path.relative_to(self.root)
                if any(part.lower() in SKIPPED_DIRECTORY_NAMES for part in relative.parts):
                    continue
                stat = path.stat()
                if stat.st_size > MAX_DOCUMENT_BYTES:
                    continue
                content = safe_read(path)
            except (OSError, ValueError):
                continue

            relative_text = relative.as_posix()
            doc_headings = headings(content)
            title = first_heading(content) or path.stem.replace("_", " ").replace("-", " ")
            collection = relative.parts[0] if len(relative.parts) > 1 else "Repository root"
            modified = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).astimezone()
            documents.append(
                {
                    "path": relative_text,
                    "title": title,
                    "collection": collection,
                    "categories": classify(relative_text, content, doc_headings),
                    "headings": doc_headings,
                    "preview": clean_preview(content),
                    "updated": modified.isoformat(timespec="seconds"),
                    "updated_timestamp": stat.st_mtime,
                    "size": stat.st_size,
                    "word_count": len(re.findall(r"\b\w+\b", content)),
                }
            )
            contents[relative_text] = content

        path_set = {str(document["path"]) for document in documents}
        title_lookup: dict[str, list[str]] = {}
        for document in documents:
            title_lookup.setdefault(str(document["title"]).lower(), []).append(str(document["path"]))
            title_lookup.setdefault(Path(str(document["path"])).stem.lower(), []).append(str(document["path"]))

        edges: list[dict[str, str]] = []
        seen_edges: set[tuple[str, str]] = set()
        for source_path, content in contents.items():
            for raw_target, relation in self._references(content):
                target_path = self._resolve_reference(source_path, raw_target, path_set, title_lookup)
                if target_path is None or target_path == source_path:
                    continue
                key = (source_path, target_path)
                if key not in seen_edges:
                    seen_edges.add(key)
                    edges.append({"source": source_path, "target": target_path, "relation": relation})

        outgoing: dict[str, list[str]] = {path: [] for path in path_set}
        incoming: dict[str, list[str]] = {path: [] for path in path_set}
        for edge in edges:
            outgoing[edge["source"]].append(edge["target"])
            incoming[edge["target"]].append(edge["source"])
        for document in documents:
            path = str(document["path"])
            document["outgoing_links"] = sorted(outgoing[path])
            document["incoming_links"] = sorted(incoming[path])

        documents.sort(key=lambda item: str(item["title"]).lower())
        with self._lock:
            self._documents = documents
            self._contents = contents
            self._edges = edges
        return len(documents)

    @staticmethod
    def _references(content: str) -> list[tuple[str, str]]:
        references: list[tuple[str, str]] = []
        for target in re.findall(r"(?<!!)\[[^\]]*\]\(([^)]+)\)", content):
            references.append((target.strip().split(" ", 1)[0], "markdown"))
        for target in re.findall(r"\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]", content):
            references.append((target.strip(), "wikilink"))
        return references

    @staticmethod
    def _resolve_reference(
        source_path: str,
        raw_target: str,
        path_set: set[str],
        title_lookup: dict[str, list[str]],
    ) -> str | None:
        target = raw_target.split("#", 1)[0].strip().replace("\\", "/")
        if not target or re.match(r"(?:https?://|mailto:|tel:)", target, flags=re.IGNORECASE):
            return None
        candidates = [target.lstrip("/")]
        candidates.append(posixpath.normpath(posixpath.join(posixpath.dirname(source_path), target)))
        expanded: list[str] = []
        for candidate in candidates:
            expanded.append(candidate)
            if not candidate.lower().endswith(".md"):
                expanded.append(f"{candidate}.md")
        for candidate in expanded:
            if candidate in path_set:
                return candidate
        named = title_lookup.get(Path(target).stem.lower(), [])
        return named[0] if len(named) == 1 else None

    def documents(self, query: str = "", category: str = "", collection: str = "", sort: str = "title") -> list[dict[str, object]]:
        tokens = [token.lower() for token in re.findall(r"[\w'-]+", query) if len(token) > 1]
        with self._lock:
            result: list[dict[str, object]] = []
            for document in self._documents:
                if category and category not in document["categories"]:
                    continue
                if collection and collection != document["collection"]:
                    continue
                body = self._contents.get(str(document["path"]), "")
                searchable = f"{document['title']} {document['path']} {' '.join(str(h['text']) for h in document['headings'])} {body}".lower()
                if tokens and not all(token in searchable for token in tokens):
                    continue
                copy = dict(document)
                copy["score"] = sum(searchable.count(token) for token in tokens)
                result.append(copy)

        if sort == "updated":
            result.sort(key=lambda item: float(item["updated_timestamp"]), reverse=True)
        elif sort == "path":
            result.sort(key=lambda item: str(item["path"]).lower())
        elif query:
            result.sort(key=lambda item: (int(item["score"]), str(item["title"]).lower()), reverse=True)
        else:
            result.sort(key=lambda item: str(item["title"]).lower())
        return result

    def document(self, relative_path: str) -> tuple[dict[str, object], str] | None:
        with self._lock:
            content = self._contents.get(relative_path)
            metadata = next((item for item in self._documents if item["path"] == relative_path), None)
            return (dict(metadata), content) if metadata is not None and content is not None else None

    def facets(self) -> dict[str, object]:
        with self._lock:
            categories: dict[str, int] = {}
            collections: dict[str, int] = {}
            for document in self._documents:
                collections[str(document["collection"])] = collections.get(str(document["collection"]), 0) + 1
                for category in document["categories"]:
                    categories[str(category)] = categories.get(str(category), 0) + 1
            return {"total": len(self._documents), "categories": categories, "collections": collections}

    def graph(self) -> dict[str, object]:
        with self._lock:
            return {
                "nodes": [
                    {
                        "id": str(document["path"]),
                        "title": str(document["title"]),
                        "collection": str(document["collection"]),
                        "categories": list(document["categories"]),
                        "outgoing": len(document["outgoing_links"]),
                        "incoming": len(document["incoming_links"]),
                    }
                    for document in self._documents
                ],
                "edges": list(self._edges),
            }


INDEX = MarkdownIndex(WORKSPACE_ROOT)


class NavigatorHandler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:  # Keep terminal output focused.
        return

    def send_json(self, payload: object, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def send_html(self, source: str, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = source.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def send_file(self, path: Path, content_type: str) -> None:
        body = path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:  # noqa: N802
        if urlparse(self.path).path == "/api/reindex":
            self.send_json({"total": INDEX.reindex()})
            return
        self.send_json({"error": "Not found"}, HTTPStatus.NOT_FOUND)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)
        if parsed.path == "/map":
            self.send_html(self._map_page())
            return
        if parsed.path == "/":
            self.send_file(APP_DIR / "index.html", "text/html; charset=utf-8")
            return
        if parsed.path == "/app.js":
            self.send_file(APP_DIR / "app.js", "application/javascript; charset=utf-8")
            return
        if parsed.path == "/styles.css":
            self.send_file(APP_DIR / "styles.css", "text/css; charset=utf-8")
            return
        if parsed.path == "/api/facets":
            self.send_json(INDEX.facets())
            return
        if parsed.path == "/api/meta":
            self.send_json({"version": NAVIGATOR_VERSION, "port": PORT})
            return
        if parsed.path == "/api/graph":
            self.send_json(INDEX.graph())
            return
        if parsed.path == "/api/documents":
            self.send_json(
                {
                    "documents": INDEX.documents(
                        query=query.get("q", [""])[0],
                        category=query.get("category", [""])[0],
                        collection=query.get("collection", [""])[0],
                        sort=query.get("sort", ["title"])[0],
                    )
                }
            )
            return
        if parsed.path == "/api/document":
            relative_path = query.get("path", [""])[0]
            record = INDEX.document(relative_path)
            if record is None:
                self.send_json({"error": "Markdown document not found"}, HTTPStatus.NOT_FOUND)
                return
            metadata, content = record
            self.send_json({"document": metadata, "content": content})
            return
        self.send_json({"error": "Not found"}, HTTPStatus.NOT_FOUND)

    def _map_page(self) -> str:
        graph = INDEX.graph()
        nodes = graph["nodes"]
        edges = graph["edges"]
        groups: dict[str, list[dict[str, object]]] = {}
        for node in nodes:
            groups.setdefault(str(node["collection"]), []).append(node)
        ordered_groups = sorted(groups.items())

        positions: dict[str, tuple[float, float]] = {}
        for group_index, (_, members) in enumerate(ordered_groups):
            cluster_x = 140 + (group_index % 4) * 235
            cluster_y = 125 + (group_index // 4) * 235
            for member_index, node in enumerate(sorted(members, key=lambda item: str(item["title"]))):
                positions[str(node["id"])] = (
                    cluster_x + (member_index % 5) * 38,
                    cluster_y + (member_index // 5) * 38,
                )

        edge_svg = "".join(
            f'<line x1="{positions[edge["source"]][0]}" y1="{positions[edge["source"]][1]}" '
            f'x2="{positions[edge["target"]][0]}" y2="{positions[edge["target"]][1]}" />'
            for edge in edges
            if edge["source"] in positions and edge["target"] in positions
        )
        node_svg = "".join(
            f'<a href="/?open={quote(str(node["id"]))}"><circle cx="{positions[str(node["id"])][0]}" '
            f'cy="{positions[str(node["id"])][1]}" r="7"><title>{html.escape(str(node["title"]))}: '
            f'{html.escape(str(node["id"]))}</title></circle></a>'
            for node in nodes
        )

        def tree(branch: dict[str, object]) -> str:
            output: list[str] = ["<ul>"]
            for name, value in sorted(branch.items()):
                if isinstance(value, dict) and "__node__" in value:
                    node = value["__node__"]
                    output.append(f'<li class="file"><a href="/?open={quote(str(node["id"]))}">{html.escape(str(node["title"]))}</a><small>{html.escape(str(node["id"]))}</small></li>')
                else:
                    output.append(f"<li><details open><summary>{html.escape(name)}</summary>{tree(value)}</details></li>")
            output.append("</ul>")
            return "".join(output)

        root: dict[str, object] = {}
        for node in nodes:
            cursor = root
            parts = str(node["id"]).split("/")
            for index, part in enumerate(parts):
                if index == len(parts) - 1:
                    cursor[part] = {"__node__": node}
                else:
                    cursor = cursor.setdefault(part, {})  # type: ignore[assignment]

        legend = " ".join(f"<span>{html.escape(name)} ({len(members)})</span>" for name, members in ordered_groups)
        return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Sanctuary Docs Connections</title><style>
body{{margin:0;background:#f5f1e7;color:#17221d;font-family:Georgia,serif}}header{{padding:24px 34px;border-bottom:1px solid #d9d2c4;background:#fffdf7;display:flex;justify-content:space-between;align-items:center}}h1{{margin:0;font-size:30px}}p,small{{color:#66706a}}a{{color:#8e371b}}.back{{border:1px solid #17221d;padding:9px 12px;text-decoration:none;color:#17221d;font-family:Arial,sans-serif;font-size:13px}}main{{padding:25px 34px;max-width:1500px;margin:auto}}.stats,.legend{{font-family:Arial,sans-serif;font-size:13px;color:#59645e}}.legend span{{display:inline-block;margin:4px 8px 4px 0;padding:5px 8px;background:#dfe7dc}}svg{{width:100%;height:600px;background:#fffdf7;border:1px solid #d9d2c4;margin:14px 0}}line{{stroke:#aaa391;stroke-width:1.1;opacity:.75}}circle{{fill:#a24120;stroke:#fffdf7;stroke-width:2;cursor:pointer}}circle:hover{{fill:#17221d;r:10}}.tree{{background:#fffdf7;border:1px solid #d9d2c4;padding:16px;font-family:Arial,sans-serif}}ul{{list-style:none;margin:4px 0;padding-left:20px}}summary{{cursor:pointer;color:#405249;padding:4px}}.file{{padding:4px 0}}.file small{{display:block;font-size:10px;padding-top:2px;overflow-wrap:anywhere}}</style></head><body><header><div><p style="margin:0 0 7px;font:700 10px Arial;letter-spacing:1.5px;color:#a24120">SERVER-RENDERED DOCUMENT MAP</p><h1>Workspace Connections</h1></div><a class="back" href="/">Back to documents</a></header><main><p class="stats">{len(nodes)} Markdown files · {len(edges)} resolved Markdown or Obsidian wikilinks. Lines show explicit document links; isolated dots are still shown.</p><div class="legend">{legend}</div><svg viewBox="0 0 980 620" role="img" aria-label="Document connection graph">{edge_svg}{node_svg}</svg><h2>Folder tree</h2><section class="tree">{tree(root)}</section></main></body></html>'''


def main() -> None:
    print(f"Indexing Markdown below: {WORKSPACE_ROOT}")
    print(f"Workspace Docs Navigator {NAVIGATOR_VERSION}: http://{HOST}:{PORT}")
    print("Press Ctrl+C to stop. Use Refresh index after adding or editing documentation.")
    try:
        with ThreadingHTTPServer((HOST, PORT), NavigatorHandler) as server:
            webbrowser.open(f"http://{HOST}:{PORT}", new=2)
            server.serve_forever()
    except OSError as error:
        print(f"Could not start at http://{HOST}:{PORT}: {error}", file=sys.stderr)
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
