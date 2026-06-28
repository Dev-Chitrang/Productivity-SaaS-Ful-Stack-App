from typing import Any, Optional


def _extract_text_from_node(node: dict) -> str:
    node_type = node.get("type")

    if node_type == "text":
        return node.get("text", "")

    if node_type == "paragraph":
        content = node.get("content", [])
        text = "".join(_extract_text_from_node(child) for child in content)
        return text + "\n"

    if node_type == "heading":
        content = node.get("content", [])
        text = "".join(_extract_text_from_node(child) for child in content)
        return text + "\n"

    if node_type == "bulletList":
        return _extract_list_items(node, "- ")

    if node_type == "orderedList":
        return _extract_list_items(node, numbered=True)

    if node_type == "listItem":
        content = node.get("content", [])
        return "".join(_extract_text_from_node(child) for child in content)

    if node_type == "hardBreak":
        return "\n"

    if node_type == "horizontalRule":
        return "---\n"

    content = node.get("content", [])
    return "".join(_extract_text_from_node(child) for child in content)


def _extract_list_items(node: dict, prefix: str = "- ", numbered: bool = False) -> str:
    content = node.get("content", [])
    lines = []
    for i, item in enumerate(content):
        item_text = _extract_text_from_node(item).strip()
        p = f"{i + 1}. " if numbered else prefix
        lines.append(f"{p}{item_text}")
    return "\n".join(lines) + "\n"


def tiptap_doc_to_plain_text(data: Any, max_length: int = 200) -> str:
    if data is None:
        return ""
    if isinstance(data, str):
        return data
    if not isinstance(data, dict):
        return str(data)
    if data.get("type") != "doc":
        return str(data)

    content = data.get("content", [])
    text = "".join(_extract_text_from_node(child) for child in content)
    text = text.strip()

    if not text:
        return ""

    if max_length > 0 and len(text) > max_length:
        truncated = text[:max_length]
        last_space = truncated.rfind(" ")
        if last_space > max_length // 2:
            truncated = truncated[:last_space]
        return truncated + "..."

    return text
