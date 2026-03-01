# app/services/mermaid_builder.py

def _sanitize_name(name):
    # Mermaid participant names must avoid spaces and special characters - make safe label
    return name.replace(" ", "_").replace(".", "_").replace("-", "_").replace("/", "_")

def build_mermaid(architecture, selected_controller: str = None, max_participants: int = 12):
    """
    Build a safe Mermaid sequence diagram.
    If selected_controller is provided, build diagram focused on that controller.
    Otherwise produce a compact overview (limited controllers).
    """

    diagram = []
    diagram.append("sequenceDiagram")
    diagram.append("    actor User")

    controllers = architecture.get("controllers", []) or []
    services = architecture.get("services", []) or []
    repos = architecture.get("repositories", []) or []
    relationships = architecture.get("relationships", []) or []
    minimal_apis = architecture.get("minimal_apis", []) or []

    # filter relationships noise (case-insensitive)
    IGNORE_KEYWORDS = ["interop", "assemblyinfo", "generated", "svcutil", "reference", "generatedclient", "assemblyinfo", "globalusings"]

    def is_noise(s):
        low = s.lower()
        return any(k in low for k in IGNORE_KEYWORDS)

    filtered_rels = [r for r in relationships if not is_noise(r)]

    # if selected_controller, ensure it's valid
    if selected_controller and selected_controller not in controllers:
        selected_controller = None

    participants = set()

    if selected_controller:
        # focus on selected controller: collect direct targets and one deeper level
        participants.add(selected_controller)
        # collect relationships starting from selected controller
        direct = []
        for rel in filtered_rels:
            parts = rel.split(" -> ")
            if len(parts) != 2:
                continue
            a, b = parts[0], parts[1]
            if a == selected_controller:
                if not is_noise(b):
                    direct.append((a, b))
                    participants.add(b)

        # collect one deeper level from those targets
        deeper = []
        for a, b in direct:
            for rel in filtered_rels:
                parts = rel.split(" -> ")
                if len(parts) != 2:
                    continue
                if parts[0] == b and not is_noise(parts[1]):
                    deeper.append((b, parts[1]))
                    participants.add(parts[1])

        # cap participants
        participants = list(participants)[:max_participants]

        # declare participants
        for p in participants:
            diagram.append(f"    participant {_sanitize_name(p)} as {p}")

        diagram.append("")

        # user -> controller -> targets -> deeper
        diagram.append(f"    User->>{_sanitize_name(selected_controller)}: HTTP Request")

        for a, b in direct:
            if b in participants:
                diagram.append(f"    {_sanitize_name(a)}->>{_sanitize_name(b)}: Call")

        for a, b in deeper:
            if a in participants and b in participants:
                diagram.append(f"    {_sanitize_name(a)}->>{_sanitize_name(b)}: Call")

        diagram.append(f"    {_sanitize_name(selected_controller)}-->>User: Response")
        return "\n".join(diagram)

    # No selected controller: build compact overview

    # choose up to 3 controllers (highest importance)
    overview_controllers = controllers[:3]

    # pick a handful of services/repos referenced in filtered_rels
    referenced = []
    for rel in filtered_rels:
        parts = rel.split(" -> ")
        if len(parts) != 2:
            continue
        a, b = parts[0], parts[1]
        if a in overview_controllers or b in overview_controllers:
            referenced.append(a); referenced.append(b)

    # merge with top services and repos
    participants.update(overview_controllers)
    # append first few services/repos
    for s in (services + repos):
        if len(participants) >= max_participants:
            break
        if s not in participants and not is_noise(s):
            participants.add(s)

    # also add referenced items up to cap
    for item in referenced:
        if len(participants) >= max_participants:
            break
        if item not in participants and not is_noise(item):
            participants.add(item)

    participants = list(participants)[:max_participants]

    for p in participants:
        diagram.append(f"    participant {_sanitize_name(p)} as {p}")

    diagram.append("")

    # Build flows for overview controllers (1 or 2)
    for controller in overview_controllers[:2]:
        diagram.append(f"    User->>{_sanitize_name(controller)}: HTTP Request")
        for rel in filtered_rels:
            parts = rel.split(" -> ")
            if len(parts) != 2:
                continue
            a, b = parts[0], parts[1]
            if a == controller and b in participants:
                diagram.append(f"    {_sanitize_name(a)}->>{_sanitize_name(b)}: Call")
        diagram.append(f"    {_sanitize_name(controller)}-->>User: Response")
        diagram.append("")

    # fallback if nothing produced
    if len(participants) == 0:
        diagram.append("    participant Application")
        diagram.append("")
        diagram.append("    User->>Application: Request")
        diagram.append("    Application-->>User: Response")

    return "\n".join(diagram)