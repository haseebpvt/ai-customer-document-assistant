from langgraph.graph import END, START, StateGraph

from agent.nodes import document_processing, identify_file, image_processing
from agent.state import State


def route_by_file_format(state: State) -> str:
    if state["file_format"] == "image":
        return "image_processing"
    return "document_processing"


builder = StateGraph(State)
builder.add_node("identify_file", identify_file)
builder.add_node("image_processing", image_processing)
builder.add_node("document_processing", document_processing)
builder.add_edge(START, "identify_file")
builder.add_conditional_edges("identify_file", route_by_file_format)
builder.add_edge("image_processing", END)
builder.add_edge("document_processing", END)

graph = builder.compile()
