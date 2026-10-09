import agent.nodes as nodes
from agent.bedrock.converse import json_object
from agent.bedrock.fields import ClaimForm
from agent.graph import route_by_content, route_by_file_format


def test_images_go_to_the_vision_node():
    assert route_by_file_format({"file_format": "image"}) == "image_processing_node"


def test_pdf_and_docx_go_to_text_extraction():
    assert route_by_file_format({"file_format": "pdf"}) == "document_processing_node"
    assert route_by_file_format({"file_format": "docx"}) == "document_processing_node"


def test_unsupported_files_skip_to_finalize():
    assert route_by_file_format({"status": "unsupported"}) == "finalize_node"


def test_empty_content_skips_classification():
    assert route_by_content({"content": "  "}) == "finalize_node"
    assert route_by_content({"content": "CLAIM FORM"}) == "identify_document_node"


def test_missing_fields_lists_null_and_blank_values(monkeypatch):
    monkeypatch.setattr(nodes, "update_document", lambda *args, **kwargs: None)
    state = {
        "document_id": "d1",
        "document_type": "Claim Form",
        "fields": {"customer_name": "Asha Menon", "claim_reference": " ", "date": None},
    }
    assert nodes.missing_fields_node(state) == {
        "missing_fields": ["claim_reference", "date", "amount"]
    }


def test_json_object_strips_a_markdown_fence():
    assert json_object('```json\n{"a": 1}\n```') == '{"a": 1}'


def test_numbers_become_strings():
    assert ClaimForm.model_validate_json('{"amount": 1250.5}').amount == "1250.5"
