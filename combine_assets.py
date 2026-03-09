#!/usr/bin/env python3
"""
combine_assets.py

Combines multiple OpenSpace .asset files that share the same GUI path
into a single consolidated .asset file.  Duplicate header declarations
are merged, all scene-graph nodes are included in order, and the
onInitialize / onDeinitialize / export blocks are unified.

Usage:
    python combine_assets.py --gui-path "/CVoL/Fish MDS relax 55" \
                             --output outfiles/CVoL/Actinopterygii_MDS_relax55.asset

    # Optionally specify the directory to search (default: directory of --output)
    python combine_assets.py --gui-path "/CVoL/Fish MDS relax 55" \
                             --output outfiles/CVoL/Actinopterygii_MDS_relax55.asset \
                             --search-dir outfiles/CVoL
"""

import argparse
import re
import sys
from pathlib import Path


# ── Header declarations recognised at the top of each file ──────────────────
# Output will always follow this canonical order.
_HEADER_SPECS = [
    ('colormaps',    re.compile(r'^local\s+colormaps\s*=')),
    ('transforms',   re.compile(r'^local\s+transforms\s*=')),
    ('meters_in_pc', re.compile(r'^local\s+meters_in_pc\s*=')),
    ('meters_in_Km', re.compile(r'^local\s+meters_in_Km\s*=')),
]

_NODE_DEF_RE  = re.compile(r'^local\s+(\w+)\s*=\s*\{')
_GUI_PATH_RE  = re.compile(r'Path\s*=\s*"([^"]+)"')
_ADD_RE       = re.compile(r'openspace\.addSceneGraphNode\((\w+)\)')
_REMOVE_RE    = re.compile(r'openspace\.removeSceneGraphNode\((\w+)\)')
_EXPORT_RE    = re.compile(r'asset\.export\((\w+)\)')


def _header_sort_key(line: str) -> int:
    stripped = line.strip()
    for i, (_, pattern) in enumerate(_HEADER_SPECS):
        if pattern.match(stripped):
            return i
    return len(_HEADER_SPECS)  # unknown headers sorted after known ones


def parse_asset_file(filepath: Path):
    """
    Parse a single .asset file.

    Returns
    -------
    header_lines : list[str]
        Top-level local declarations that precede any node definition.
    nodes : list[tuple[str, str, str | None]]
        Each entry is (identifier, full_lua_text, gui_path).
        gui_path is None if no Path field was found inside the node.
    add_calls, remove_calls, export_calls : list[str]
        Identifiers found in the respective call sites.
    """
    content = filepath.read_text(encoding='utf-8')
    lines = content.splitlines()

    # ── Phase 1: collect header lines (before the first node definition) ─────
    header_lines: list[str] = []
    i = 0
    while i < len(lines):
        stripped = lines[i].strip()
        if _NODE_DEF_RE.match(stripped):
            break
        if stripped and not stripped.startswith('--'):
            header_lines.append(lines[i])
        i += 1

    # ── Phase 2: parse node definitions via brace-depth tracking ─────────────
    nodes: list[tuple[str, str, str | None]] = []
    while i < len(lines):
        stripped = lines[i].strip()
        m = _NODE_DEF_RE.match(stripped)
        if m:
            identifier = m.group(1)
            node_lines = [lines[i]]
            depth = lines[i].count('{') - lines[i].count('}')
            i += 1
            while i < len(lines) and depth > 0:
                node_lines.append(lines[i])
                depth += lines[i].count('{') - lines[i].count('}')
                i += 1

            node_text = '\n'.join(node_lines)
            gm = _GUI_PATH_RE.search(node_text)
            nodes.append((identifier, node_text, gm.group(1) if gm else None))
        else:
            i += 1

    # ── Phase 3: extract call-site identifiers from the whole file ────────────
    add_calls    = _ADD_RE.findall(content)
    remove_calls = _REMOVE_RE.findall(content)
    export_calls = _EXPORT_RE.findall(content)

    return header_lines, nodes, add_calls, remove_calls, export_calls


def combine_assets(gui_path: str, output_file: str, search_dir: str) -> None:
    output_path = Path(output_file).resolve()
    search_path = Path(search_dir).resolve()

    if not search_path.is_dir():
        print(f"Error: search directory does not exist: {search_path}", file=sys.stderr)
        sys.exit(1)

    all_header_lines: list[str] = []
    combined_nodes:   list[tuple[str, str]] = []   # (identifier, text)
    combined_add:     list[str] = []
    combined_remove:  list[str] = []
    combined_export:  list[str] = []
    matched_files:    list[Path] = []

    for asset_file in sorted(search_path.glob('*.asset')):
        if asset_file.resolve() == output_path:
            continue  # never read the output file as input

        try:
            header_lines, nodes, add_calls, remove_calls, export_calls = \
                parse_asset_file(asset_file)
        except Exception as exc:
            print(f"Warning: skipping {asset_file.name}: {exc}", file=sys.stderr)
            continue

        # Keep only nodes whose GUI.Path matches the requested path
        matching_nodes = [
            (ident, text)
            for ident, text, gpath in nodes
            if gpath == gui_path
        ]
        if not matching_nodes:
            continue

        matched_files.append(asset_file)
        all_header_lines.extend(header_lines)

        matching_idents = {ident for ident, _ in matching_nodes}
        combined_nodes.extend(matching_nodes)
        combined_add.extend(c for c in add_calls    if c in matching_idents)
        combined_remove.extend(c for c in remove_calls if c in matching_idents)
        combined_export.extend(c for c in export_calls  if c in matching_idents)

    if not matched_files:
        print(f"No asset files found with GUI path: {gui_path!r}", file=sys.stderr)
        sys.exit(1)

    # ── Deduplicate and sort headers in canonical order ───────────────────────
    seen_headers: set[str] = set()
    unique_headers: list[str] = []
    for line in all_header_lines:
        key = line.strip()
        if key and key not in seen_headers:
            seen_headers.add(key)
            unique_headers.append(line)
    unique_headers.sort(key=_header_sort_key)

    # ── Write combined output ─────────────────────────────────────────────────
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open('w', encoding='utf-8', newline='\n') as fout:
        for line in unique_headers:
            fout.write(line + '\n')
        fout.write('\n')

        for _ident, text in combined_nodes:
            fout.write(text + '\n')
            fout.write('\n')

        fout.write('asset.onInitialize(function()\n')
        for ident in combined_add:
            fout.write(f'    openspace.addSceneGraphNode({ident});\n')
        fout.write('end)\n')
        fout.write('\n')

        fout.write('asset.onDeinitialize(function()\n')
        for ident in combined_remove:
            fout.write(f'    openspace.removeSceneGraphNode({ident});\n')
        fout.write('end)\n')
        fout.write('\n')

        for ident in combined_export:
            fout.write(f'asset.export({ident})\n')

    # ── Report ────────────────────────────────────────────────────────────────
    cwd = Path.cwd()
    try:
        display_out = output_path.relative_to(cwd)
    except ValueError:
        display_out = output_path

    print(f"Combined {len(matched_files)} file(s) → {display_out}")
    for f in matched_files:
        try:
            rel = f.relative_to(cwd)
        except ValueError:
            rel = f
        print(f"  + {rel}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            'Combine OpenSpace .asset files that share a GUI path '
            'into a single consolidated .asset file.'
        )
    )
    parser.add_argument(
        '--gui-path', required=True,
        help='GUI Path value to match, e.g. "/CVoL/Fish MDS relax 55"',
    )
    parser.add_argument(
        '--output', required=True,
        help='Path for the combined output .asset file',
    )
    parser.add_argument(
        '--search-dir',
        help=(
            'Directory to search for .asset files '
            '(default: directory containing --output)'
        ),
    )
    args = parser.parse_args()

    search_dir = args.search_dir
    if search_dir is None:
        candidate = Path(args.output).parent
        search_dir = str(candidate) if candidate.parts else '.'

    combine_assets(args.gui_path, args.output, search_dir)


if __name__ == '__main__':
    main()
