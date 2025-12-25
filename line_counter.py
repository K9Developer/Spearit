# -*- coding: utf-8 -*-
import glob, os

def does_file_match_gitignore(file_path, gitignore_files):
    file_path = os.path.normpath(file_path)

    for gitignore in gitignore_files:
        base_dir = os.path.dirname(gitignore)
        rel_path = os.path.relpath(file_path, base_dir)

        with open(gitignore, "r", encoding="utf-8", errors="ignore") as f:
            for pattern in f:
                pattern = pattern.strip()

                if not pattern or pattern.startswith("#"):
                    continue

                # directory ignore
                if pattern.endswith("/"):
                    if rel_path.startswith(pattern.rstrip("/") + os.sep):
                        return True
                else:
                    if glob.fnmatch.fnmatch(rel_path, pattern):
                        return True


extensions = ("*.py", "*.h", "*.c", "*.rs", "*.tsx", "*.ts", "*.js")
file_list = []
gitignore_files = glob.glob("./**/.gitignore", recursive=True)

for ext in extensions:
    file_list.extend(glob.glob(f"./**/{ext}", recursive=True)) 

file_list = [f for f in file_list if not does_file_match_gitignore(f, gitignore_files)]

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
