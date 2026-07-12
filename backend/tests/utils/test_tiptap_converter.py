import pytest
from app.utils.tiptap_converter import (
    _extract_text_from_node,
    _extract_list_items,
    tiptap_doc_to_plain_text,
)


class TestExtractTextFromNode:
    def test_text_node(self):
        node = {"type": "text", "text": "Hello"}
        assert _extract_text_from_node(node) == "Hello"

    def test_text_node_missing_text_key(self):
        node = {"type": "text"}
        assert _extract_text_from_node(node) == ""

    def test_paragraph_node(self):
        node = {
            "type": "paragraph",
            "content": [{"type": "text", "text": "Hello"}],
        }
        assert _extract_text_from_node(node) == "Hello\n"

    def test_heading_node(self):
        node = {
            "type": "heading",
            "content": [{"type": "text", "text": "Title"}],
        }
        assert _extract_text_from_node(node) == "Title\n"

    def test_bullet_list_node(self):
        node = {
            "type": "bulletList",
            "content": [
                {
                    "type": "listItem",
                    "content": [{"type": "text", "text": "Item 1"}],
                },
                {
                    "type": "listItem",
                    "content": [{"type": "text", "text": "Item 2"}],
                },
            ],
        }
        result = _extract_text_from_node(node)
        assert "Item 1" in result
        assert "Item 2" in result

    def test_ordered_list_node(self):
        node = {
            "type": "orderedList",
            "content": [
                {
                    "type": "listItem",
                    "content": [{"type": "text", "text": "First"}],
                },
            ],
        }
        result = _extract_text_from_node(node)
        assert "1." in result
        assert "First" in result

    def test_hard_break_node(self):
        node = {"type": "hardBreak"}
        assert _extract_text_from_node(node) == "\n"

    def test_horizontal_rule_node(self):
        node = {"type": "horizontalRule"}
        assert _extract_text_from_node(node) == "---\n"

    def test_unknown_node_falls_back_to_content(self):
        node = {
            "type": "unknown",
            "content": [{"type": "text", "text": "Text"}],
        }
        assert _extract_text_from_node(node) == "Text"

    def test_empty_content(self):
        node = {"type": "paragraph", "content": []}
        assert _extract_text_from_node(node) == "\n"


class TestExtractListItems:
    def test_bullet_list_prefix(self):
        node = {
            "type": "bulletList",
            "content": [
                {
                    "type": "listItem",
                    "content": [{"type": "text", "text": "Item 1"}],
                },
            ],
        }
        result = _extract_list_items(node, prefix="- ", numbered=False)
        assert result.startswith("- ")

    def test_ordered_list_numbered(self):
        node = {
            "type": "orderedList",
            "content": [
                {
                    "type": "listItem",
                    "content": [{"type": "text", "text": "First"}],
                },
                {
                    "type": "listItem",
                    "content": [{"type": "text", "text": "Second"}],
                },
            ],
        }
        result = _extract_list_items(node, numbered=True)
        assert "1." in result
        assert "2." in result

    def test_empty_list(self):
        node = {"type": "bulletList", "content": []}
        result = _extract_list_items(node)
        assert result == "\n"

    def test_item_text_stripped(self):
        node = {
            "type": "bulletList",
            "content": [
                {
                    "type": "listItem",
                    "content": [{"type": "text", "text": "  Item  "}],
                },
            ],
        }
        result = _extract_list_items(node)
        assert "Item" in result
        assert "  " not in result


class TestTiptapDocToPlainText:
    def test_none_returns_empty(self):
        assert tiptap_doc_to_plain_text(None) == ""

    def test_string_returns_string(self):
        assert tiptap_doc_to_plain_text("plain text") == "plain text"

    def test_non_dict_returns_str(self):
        assert tiptap_doc_to_plain_text([1, 2, 3]) == "[1, 2, 3]"

    def test_non_doc_dict_returns_str(self):
        assert tiptap_doc_to_plain_text({"type": "image"}) == "{'type': 'image'}"

    def test_empty_doc_returns_empty(self):
        doc = {"type": "doc", "content": []}
        assert tiptap_doc_to_plain_text(doc) == ""

    def test_simple_paragraph(self):
        doc = {
            "type": "doc",
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": "Hello world"}],
                },
            ],
        }
        assert tiptap_doc_to_plain_text(doc) == "Hello world"

    def test_multiple_paragraphs(self):
        doc = {
            "type": "doc",
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": "First"}],
                },
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": "Second"}],
                },
            ],
        }
        assert tiptap_doc_to_plain_text(doc) == "First\nSecond"

    def test_truncation_with_max_length(self):
        long_text = "word " * 50
        doc = {
            "type": "doc",
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": long_text}],
                },
            ],
        }
        result = tiptap_doc_to_plain_text(doc, max_length=20)
        assert len(result) <= 23
        assert result.endswith("...")

    def test_no_truncation_when_under_max_length(self):
        doc = {
            "type": "doc",
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": "Short text"}],
                },
            ],
        }
        assert tiptap_doc_to_plain_text(doc, max_length=100) == "Short text"

    def test_truncation_gracefully_at_space(self):
        text = "word word word word"
        doc = {
            "type": "doc",
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": text}],
                },
            ],
        }
        result = tiptap_doc_to_plain_text(doc, max_length=10)
        assert " " in result or len(result) == 10
