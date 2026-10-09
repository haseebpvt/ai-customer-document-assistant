from botocore.exceptions import BotoCoreError, ClientError
from langgraph.graph import END, START, StateGraph
from langgraph.types import RetryPolicy
from pydantic import ValidationError

from agent.nodes import (
    document_processing_node,
    extract_fields_node,
    finalize_node,
    identify_document_node,
    identify_file_node,
    image_processing_node,
    missing_fields_node,
    summary_node,
)
from agent.state import State

# Bedrock can throttle, and a model can return JSON that fails the schema. Both may pass on a second try.
BEDROCK_RETRY = RetryPolicy(
    max_attempts=3,
    retry_on=(ValidationError, ClientError, BotoCoreError),
)


def route_by_file_format(state: State) -> str:
    if state["file_format"] == "image":
        return "image_processing_node"
    return "document_processing_node"


def route_by_content(state: State) -> str:
    # No text, so skip classification. Finalize still completes the row.
    if not state.get("content", "").strip():
        return "finalize_node"
    return "identify_document_node"


builder = StateGraph(State)
builder.add_node("identify_file_node", identify_file_node)
builder.add_node("image_processing_node", image_processing_node, retry_policy=BEDROCK_RETRY)
builder.add_node("document_processing_node", document_processing_node)
builder.add_node("identify_document_node", identify_document_node, retry_policy=BEDROCK_RETRY)
builder.add_node("extract_fields_node", extract_fields_node, retry_policy=BEDROCK_RETRY)
builder.add_node("missing_fields_node", missing_fields_node)
builder.add_node("summary_node", summary_node, retry_policy=BEDROCK_RETRY)
builder.add_node("finalize_node", finalize_node)

builder.add_edge(START, "identify_file_node")
builder.add_conditional_edges("identify_file_node", route_by_file_format)
builder.add_conditional_edges("image_processing_node", route_by_content)
builder.add_conditional_edges("document_processing_node", route_by_content)
builder.add_edge("identify_document_node", "extract_fields_node")
builder.add_edge("extract_fields_node", "missing_fields_node")
builder.add_edge("missing_fields_node", "summary_node")
builder.add_edge("summary_node", "finalize_node")
builder.add_edge("finalize_node", END)

graph = builder.compile()
