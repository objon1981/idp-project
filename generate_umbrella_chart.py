import os
import re
from packaging.version import parse as parse_version

# Paths
SERVICES_DIR = "./services"
UMBRELLA_CHART_DIR = "./umbrella-chart"
FILES_DIR = os.path.join(UMBRELLA_CHART_DIR, "files")
TEMPLATES_DIR = os.path.join(UMBRELLA_CHART_DIR, "templates")

# Regex to parse requirements lines like:
# package==version or package>=version or just package
REQ_LINE_RE = re.compile(r"^\s*([a-zA-Z0-9_\-]+)([=<>!~]+([\w\.\*]+))?\s*(#.*)?$")

def find_requirements_files():
    req_files = []
    for root, _, files in os.walk(SERVICES_DIR):
        for f in files:
            if f == "requirements.txt":
                req_files.append(os.path.join(root, f))
    return req_files

def parse_requirements(file_path):
    reqs = {}
    with open(file_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            m = REQ_LINE_RE.match(line)
            if m:
                pkg = m.group(1).lower()
                version_spec = m.group(2) or ""
                reqs[pkg] = version_spec
    return reqs

def merge_requirements(req_files):
    merged = {}
    for f in req_files:
        reqs = parse_requirements(f)
        for pkg, ver in reqs.items():
            # If no version yet, or this version is "higher", update it
            if pkg not in merged or is_version_higher(ver, merged[pkg]):
                merged[pkg] = ver
    return merged

def is_version_higher(ver1, ver2):
    # If one has no version spec, treat the other as higher
    if not ver1:
        return False
    if not ver2:
        return True
    # Compare versions if '==' or '>='
    # Only handle == and >= for simplicity
    op_ver1 = parse_op_version(ver1)
    op_ver2 = parse_op_version(ver2)
    if not op_ver1 or not op_ver2:
        # Can't compare, just keep existing
        return False
    op1, v1 = op_ver1
    op2, v2 = op_ver2
    try:
        v1_parsed = parse_version(v1)
        v2_parsed = parse_version(v2)
    except:
        return False

    if op1 == "==" and op2 == "==":
        # Keep the higher version
        return v1_parsed > v2_parsed
    if op1 == ">=" and op2 == ">=":
        return v1_parsed > v2_parsed
    if op1 == "==" and op2 == ">=":
        # == version is more strict, treat == as higher if equal or greater
        return v1_parsed >= v2_parsed
    if op1 == ">=" and op2 == "==":
        # >= is less strict, only higher if greater
        return v1_parsed > v2_parsed
    # fallback
    return False

def parse_op_version(ver_str):
    # Parse something like '==1.0.0' or '>=0.1.2' into (op, version)
    m = re.match(r"([=<>!~]+)([\w\.\*]+)", ver_str)
    if m:
        return m.group(1), m.group(2)
    return None

def write_base_requirements(merged_reqs):
    os.makedirs(FILES_DIR, exist_ok=True)
    path = os.path.join(FILES_DIR, "base-requirements.txt")
    with open(path, "w") as f:
        for pkg, ver in sorted(merged_reqs.items()):
            f.write(f"{pkg}{ver}\n")
    print(f"Wrote consolidated requirements to {path}")

def write_configmap_template():
    os.makedirs(TEMPLATES_DIR, exist_ok=True)
    path = os.path.join(TEMPLATES_DIR, "configmap-base-requirements.yaml")
    content = """
apiVersion: v1
kind: ConfigMap
metadata:
  name: base-requirements
data:
  base-requirements.txt: |-
{{- with .Files.Get "files/base-requirements.txt" | indent 4 }}
{{ . | indent 4 }}
{{- end }}
"""
    with open(path, "w") as f:
        f.write(content.strip() + "\n")
    print(f"Wrote Helm ConfigMap template to {path}")

def print_instructions():
    print("""
==================== Instructions ====================

1. To install dependencies in your service Dockerfiles, mount the ConfigMap as a file and install like this:

    COPY your_service_code /app/
    # Mount ConfigMap as /app/base-requirements.txt in your pod via Helm deployment volume and volumeMount
    
    RUN pip install -r /app/base-requirements.txt

2. Update your Helm deployment manifests to add:

    volumes:
      - name: base-requirements-volume
        configMap:
          name: base-requirements
          items:
            - key: base-requirements.txt
              path: base-requirements.txt

    volumeMounts:
      - name: base-requirements-volume
        mountPath: /app/base-requirements.txt
        subPath: base-requirements.txt

3. Now all your services share the same consolidated dependencies base.

======================================================
""")

def main():
    req_files = find_requirements_files()
    if not req_files:
        print("No requirements.txt files found under ./services")
        return
    merged = merge_requirements(req_files)
    write_base_requirements(merged)
    write_configmap_template()
    print_instructions()

if __name__ == "__main__":
    main()
