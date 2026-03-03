from copy import deepcopy


def openai_schema(schema: dict) -> dict:
    """
    Convert Pydantic schema into OpenAI strict-compatible schema:
    - Inline $ref references
    - Remove $defs
    - Enforce required = all properties
    - Enforce additionalProperties = False
    """

    schema = deepcopy(schema)
    defs = schema.pop("$defs", {})

    def resolve_refs(node: dict):
        if not isinstance(node, dict):
            return node

        # Replace $ref with actual definition
        if "$ref" in node:
            ref_path = node["$ref"]
            ref_name = ref_path.split("/")[-1]
            if ref_name in defs:
                return resolve_refs(deepcopy(defs[ref_name]))
            return node

        # Recurse into children
        for key, value in list(node.items()):
            if isinstance(value, dict):
                node[key] = resolve_refs(value)
            elif isinstance(value, list):
                node[key] = [
                    resolve_refs(item) if isinstance(item, dict) else item
                    for item in value
                ]

        return node

    schema = resolve_refs(schema)

    def enforce_strict(node: dict):
        if not isinstance(node, dict):
            return

        if node.get("type") == "object":
            properties = node.get("properties", {})

            node["required"] = list(properties.keys())
            node["additionalProperties"] = False

            for prop in properties.values():
                enforce_strict(prop)

        if node.get("type") == "array" and "items" in node:
            enforce_strict(node["items"])

    enforce_strict(schema)

    return schema
