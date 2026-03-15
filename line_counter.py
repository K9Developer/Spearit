# -*- coding: utf-8 -*-
import glob, os

import os
import fnmatch
import re
from pathlib import Path

def _to_posix(p: str) -> str:
    return p.replace(os.sep, "/").replace("\\", "/")


def _is_under(base_dir: str, path: str) -> bool:
    try:
        Path(path).resolve().relative_to(Path(base_dir).resolve())
        return True
    except Exception:
        return False


def _strip_gitignore_line(line: str) -> str:
    line = line.rstrip("\n\r")
    i = len(line)
    while i > 0 and line[i - 1] == " ":
        if i >= 2 and line[i - 2] == "\\":
            break
        i -= 1
    return line[:i]


def _unescape_leading(s: str) -> str:
    if s.startswith(r"\#"):
        return "#" + s[2:]
    if s.startswith(r"\!"):
        return "!" + s[2:]
    if s.startswith(r"\ "):
        return " " + s[2:]
    return s


def _git_glob_to_regex(pat: str) -> re.Pattern:
    i = 0
    out = ["^"]
    while i < len(pat):
        c = pat[i]
        if c == "*":
            if i + 1 < len(pat) and pat[i + 1] == "*":
                out.append(".*")
                i += 2
            else:
                out.append("[^/]*")
                i += 1
        elif c == "?":
            out.append("[^/]")
            i += 1
        else:
            out.append(re.escape(c))
            i += 1
    out.append("$")
    return re.compile("".join(out))


def _match_pattern(rel_posix: str, basename: str, pattern: str, is_dir: bool) -> bool:
    dir_only = pattern.endswith("/")
    if dir_only:
        pattern = pattern[:-1]

    anchored = pattern.startswith("/")
    if anchored:
        pattern = pattern[1:]

    pattern = _to_posix(pattern)

    # directory ignore: match dir name anywhere (or anchored), and everything under it
    if dir_only:
        if anchored:
            return rel_posix == pattern or rel_posix.startswith(pattern + "/")
        dir_re = re.compile(rf"(^|.*/){re.escape(pattern)}(/|$)")
        return bool(dir_re.search(rel_posix))

    # IMPORTANT FIX:
    # Patterns without '/' match a name at any depth (file OR directory).
    # Example: "node_modules" should ignore node_modules/**.
    if "/" not in pattern:
        if fnmatch.fnmatchcase(basename, pattern):
            return True
        # match any parent directory segment
        parent_parts = rel_posix.split("/")[:-1]
        return any(fnmatch.fnmatchcase(part, pattern) for part in parent_parts)

    # Patterns with '/' match path; if not anchored, allow any depth (**/pattern)
    if not anchored and not pattern.startswith("**/"):
        pattern = "**/" + pattern

    rx = _git_glob_to_regex(pattern)
    return bool(rx.match(rel_posix))


def does_file_match_gitignore(file_path: str, gitignore_files: list[str]) -> bool:
    file_path = str(Path(file_path).resolve())
    is_dir = Path(file_path).is_dir()

    gitignore_files = sorted(gitignore_files, key=lambda p: len(Path(p).resolve().parts))

    ignored = False
    for gi in gitignore_files:
        gi_path = Path(gi).resolve()
        base_dir = str(gi_path.parent)

        if not _is_under(base_dir, file_path):
            continue

        rel = _to_posix(os.path.relpath(file_path, base_dir))
        base = os.path.basename(rel)

        try:
            lines = gi_path.read_text(encoding="utf-8", errors="ignore").splitlines()
        except OSError:
            continue

        for raw in lines:
            line = _strip_gitignore_line(raw)
            if not line:
                continue

            line = _unescape_leading(line)
            if line.startswith("#"):
                continue

            neg = line.startswith("!")
            if neg:
                line = _unescape_leading(line[1:])

            if not line:
                continue

            if _match_pattern(rel, base, line, is_dir=is_dir):
                ignored = not neg

    return ignored


extensions = ("*.py", "*.h", "*.c", "*.rs", "*.tsx", "*.ts", "*.js")
file_list = []
gitignore_files = glob.glob("./**/.gitignore", recursive=True)

for ext in extensions:
    for file in glob.glob(f"./**/{ext}", recursive=True):
        if does_file_match_gitignore(file, gitignore_files):
            continue
        file_list.append(file)

print(f"Counting lines in {len(file_list)} files...")

extension_counts = {ext: 0 for ext in extensions}
extension_translate = {
    "py": "Python",
    "h": "C Header",
    "c": "C",
    "rs": "Rust"
}

for file_path in file_list:
    with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
        line_count = sum(1 for _ in file)
        ext = os.path.splitext(file_path)[1][1:]
        extension_counts[f"*.{ext}"] += line_count

total_lines = sum(extension_counts.values())
for ext, count in extension_counts.items():
    lang = extension_translate.get(ext[2:], ext)
    print(f"{lang}: {count} lines")
print(f"Total lines: {total_lines} lines")
