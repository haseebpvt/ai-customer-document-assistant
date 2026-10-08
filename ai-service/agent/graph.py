from langgraph.graph import END, START, StateGraph

from agent.state import State


def echo(state: State) -> dict:
    return {"message": state["message"]}


builder = StateGraph(State)
builder.add_node("echo", echo)
builder.add_edge(START, "echo")
builder.add_edge("echo", END)

graph = builder.compile()
