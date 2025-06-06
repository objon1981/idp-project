import os
import re
from collections import defaultdict

# List of your requirements.txt files (relative paths)
requirements_files = [
    './services/local-send/app/requirements.txt',
    './services/pake/server/requirements.txt',
    './services/json-crack/build/requirements.txt',
    './services/ocr-service/app/requirements.txt',
    './services/docetl/src/requirements.txt',
    './services/local_file_organizer/app/requirements.txt',
]

# Regex to parse lines like: package==1.2.3 or package>=1.0,<2.0 etc.
REQ_LINE_RE = re.compile(r'^\s*([a-zA-Z0-9_\-]+)([<>=!~]=?.*)?$')

def parse_requirement_line(line):
    line = line.strip()
    if not line or line.startswith('#'):
        return None, None
    match = REQ_LINE_RE.match(line)
    if not match:
        return None, None
    pkg = match.group(1).lower()
    ver = match.group(2) or ''
    return pkg, ver.strip()

def load_requirements(file_path):
    requirements = {}
    with open(file_path, 'r') as f:
        for line in f:
            pkg, ver = parse_requirement_line(line)
            if pkg:
                # If package repeats in same file, accumulate versions (rare but possible)
                if pkg in requirements:
                    # Concatenate versions for awareness
                    requirements[pkg] += f', {ver}' if ver else ''
                else:
                    requirements[pkg] = ver
    return requirements

def main():
    # Dict to hold package -> {file_path: version}
    pkg_map = defaultdict(dict)

    for req_file in requirements_files:
        if not os.path.exists(req_file):
            print(f"Warning: File not found: {req_file}")
            continue
        reqs = load_requirements(req_file)
        for pkg, ver in reqs.items():
            pkg_map[pkg][req_file] = ver

    print("\n=== Duplicate Packages Across Files ===")
    duplicates = {pkg: files for pkg, files in pkg_map.items() if len(files) > 1}
    if not duplicates:
        print("No duplicate packages found across requirements files.")
    else:
        for pkg, files in duplicates.items():
            print(f"\nPackage: {pkg}")
            for f, v in files.items():
                print(f"  {f}: {v}")

    print("\n=== Conflicting Versions ===")
    conflicts_found = False
    for pkg, files in duplicates.items():
        versions = set(v for v in files.values())
        if len(versions) > 1:
            conflicts_found = True
            print(f"\nPackage: {pkg}")
            for f, v in files.items():
                print(f"  {f}: {v}")
    if not conflicts_found:
        print("No version conflicts found among duplicated packages.")

    print("\n=== Unique Packages Per File ===")
    for req_file in requirements_files:
        if not os.path.exists(req_file):
            continue
        reqs = load_requirements(req_file)
        unique_pkgs = [pkg for pkg in reqs if len(pkg_map[pkg]) == 1]
        print(f"\nFile: {req_file}")
        if unique_pkgs:
            for pkg in unique_pkgs:
                print(f"  {pkg} {reqs[pkg]}")
        else:
            print("  No unique packages.")

if __name__ == "__main__":
    main()
