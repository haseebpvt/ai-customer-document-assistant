from langgraph.graph import END, START, StateGraph

from agent.nodes import (
    document_processing_node,
    extract_fields_node,
    identify_document_node,
    identify_file_node,
    image_processing_node,
)
from agent.state import State


def route_by_file_format(state: State) -> str:
    if state["file_format"] == "image":
        return "image_processing_node"
    return "document_processing_node"


def route_by_content(state: State) -> str:
    if not state.get("content", "").strip():
        return END
    return "identify_document_node"


builder = StateGraph(State)
builder.add_node("identify_file_node", identify_file_node)
builder.add_node("image_processing_node", image_processing_node)
builder.add_node("document_processing_node", document_processing_node)
builder.add_node("identify_document_node", identify_document_node)
builder.add_node("extract_fields_node", extract_fields_node)

builder.add_edge(START, "identify_file_node")
builder.add_conditional_edges("identify_file_node", route_by_file_format)
builder.add_conditional_edges("image_processing_node", route_by_content)
builder.add_conditional_edges("document_processing_node", route_by_content)
builder.add_edge("identify_document_node", "extract_fields_node")
builder.add_edge("extract_fields_node", END)

graph = builder.compile()
