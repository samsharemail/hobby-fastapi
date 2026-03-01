# app/services/parser_service.py
import os
import re
from collections import Counter

IGNORE_FILE_PATTERNS = [
    r"\.g\.cs$", r"\.designer\.cs$", r"AssemblyInfo", r"Reference", r"Generated", r"Svcutil",
    r"Interop", r"\.svc$", r"\.designer", r"\.resources", r"obj\\", r"bin\\"
]

def is_noise_path(path):
    lower = path.lower()
    for pat in IGNORE_FILE_PATTERNS:
        if re.search(pat.lower(), lower):
            return True
    return False

def parse_dotnet_project(root_path):
    """
    Parse project collecting controllers/services/repos/dbcontexts and shallow relationships.
    Returns architecture dict and controllers sorted by relevance.
    """
    architecture = {
        "controllers": [],
        "services": [],
        "repositories": [],
        "dbcontexts": [],
        "minimal_apis": [],
        "relationships": []
    }

    # Walk files
    for root, _, files in os.walk(root_path):
        for file in files:
            if not file.endswith(".cs"):
                continue

            path = os.path.join(root, file)
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
            except:
                continue

            # skip noisy file paths early
            if is_noise_path(path):
                continue

            name = file.replace(".cs", "")

            # detect controllers: class inherits Controller or name endswith Controller or contains [ApiController]
            if re.search(r"\[ApiController\]", content) or re.search(r"class\s+\w+\s*:\s*Controller", content) or name.endswith("Controller"):
                architecture["controllers"].append(name)

            # detect services and repositories by name heuristics
            if re.search(r"\binterface\s+I\w+Service\b", content) or " Service" in name or name.endswith("Service") or "HostedService" in name:
                architecture["services"].append(name)

            if name.endswith("Repository") or "Repository" in content:
                architecture["repositories"].append(name)

            if "DbContext" in content or name.endswith("Context") or name.endswith("DbContext"):
                architecture["dbcontexts"].append(name)

            # minimal api detection
            if re.search(r"\bMapGet\(|\bMapPost\(|\bMapPut\(", content):
                architecture["minimal_apis"].append(name)

            # DI usage -> relationships (IService / IRepository)
            for match in re.findall(r"I([A-Z]\w+Service)\b", content):
                architecture["relationships"].append(f"{name} -> I{match}")

            for match in re.findall(r"I([A-Z]\w+Repository)\b", content):
                architecture["relationships"].append(f"{name} -> I{match}")

            # direct DbContext usage
            if "DbContext" in content:
                architecture["relationships"].append(f"{name} -> DbContext")

    # deduplicate
    for k in architecture:
        architecture[k] = list(dict.fromkeys(architecture[k]))

    # Score controllers by number of references in relationships and presence of "Controller" in name
    rel_counter = Counter()
    for rel in architecture["relationships"]:
        parts = rel.split(" -> ")
        if len(parts) == 2:
            rel_counter[parts[0]] += 1
            rel_counter[parts[1]] += 0  # ensure keys exist

    controllers = architecture["controllers"]
    controllers_scores = []
    for c in controllers:
        score = rel_counter.get(c, 0)
        # boost controllers (prefer explicit controllers)
        if c.endswith("Controller"):
            score += 2
        controllers_scores.append((c, score))

    # sort by score desc, then alphabetically
    controllers_sorted = [c for c, _ in sorted(controllers_scores, key=lambda x: (-x[1], x[0]))]

    return architecture, controllers_sorted