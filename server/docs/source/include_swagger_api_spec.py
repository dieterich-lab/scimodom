import copy
from pathlib import Path
from typing import Any

import yaml

OPENAPI_DIR = Path(__file__).parent / "openapi"
COMMON_FILE = OPENAPI_DIR / "_common.yaml"
INCLUDE_DIR = OPENAPI_DIR / "_include"

_COMMON_REF_PREFIX = "_common.yaml#"


def _rewrite_common_refs(node: Any) -> Any:
    if isinstance(node, dict):
        ref = node.get("$ref")
        if isinstance(ref, str) and ref.startswith(_COMMON_REF_PREFIX):
            node = dict(node)
            node["$ref"] = ref.removeprefix("_common.yaml")
            return node
        return {key: _rewrite_common_refs(value) for key, value in node.items()}
    if isinstance(node, list):
        return [_rewrite_common_refs(value) for value in node]
    return node


def write() -> list[Path]:
    """Write complete Swagger API specs from fragments.

    This function merges shared version, info, servers, and components
    from _common.yaml into each fragment under docs/source/openapi, so
    those only need to be edited in one place. Each fragment only needs
    paths and endpoint-specific components. This keeps every generated
    file independent; no runtime cross-file resolution required from
    Swagger UI or openapi-spec-validator, no need to copy _common.yaml
    into the build's _static output.

    The .rst pages must point the swagger-plugin directive at the
    generated files, not the fragments.

    Run automatically as part of the Sphinx build (see conf.py), or
    as standalone e.g. for local linting:

        python docs/source/include_swagger_api_spec.py
        openapi-spec-validator docs/source/openapi/_include/*.yaml
    """
    common = yaml.safe_load(COMMON_FILE.read_text())
    common_info = common["info"]
    common_servers = copy.deepcopy(common["servers"])
    common_servers[0].setdefault("variables", {})["version"] = {
        "default": common_info["version"]
    }
    common_components = common.get("components", {})

    INCLUDE_DIR.mkdir(exist_ok=True)
    written = []
    for fragment_path in sorted(OPENAPI_DIR.glob("*.yaml")):
        if fragment_path.name == "_common.yaml":
            continue
        fragment = yaml.safe_load(fragment_path.read_text()) or {}

        merged: dict[str, Any] = {
            "openapi": common.get("openapi", "3.0.4"),
            # Fragment's info (e.g. 'title') is layered on top of the
            # shared version/license - fragment wins on key collision.
            "info": {**common_info, **fragment.get("info", {})},
            "servers": common_servers,
        }
        for key, value in fragment.items():
            if key not in ("components", "info"):
                merged[key] = value

        # Fragment-local components win over shared ones on name collision,
        # EXCEPT when the fragment's entry is just "$ref: _common.yaml#/
        # components/<section>/<name>" pointing at itself - that's a
        # readability aid meaning "this one comes from _common.yaml", not
        # a real override, and must not replace the already-inlined
        # common definition with a (now self-referential) ref.
        merged_components = copy.deepcopy(common_components)
        for section, entries in fragment.get("components", {}).items():
            dest = merged_components.setdefault(section, {})
            for name, value in entries.items():
                common_ref = f"_common.yaml#/components/{section}/{name}"
                if isinstance(value, dict) and value.get("$ref") == common_ref:
                    continue
                dest[name] = value
        if merged_components:
            merged["components"] = merged_components

        merged = _rewrite_common_refs(merged)

        out_path = INCLUDE_DIR / fragment_path.name
        out_path.write_text(yaml.safe_dump(merged, sort_keys=False))
        written.append(out_path)
    return written


if __name__ == "__main__":
    for path in write():
        print(f"Written {path}")
