from typing import Annotated, TypedDict

from langchain_core.messages import HumanMessage
from langchain_ollama import ChatOllama
from langgraph.graph import START, END, StateGraph
from langgraph.graph.message import add_messages


class State(TypedDict):
    messages: Annotated[list, add_messages]


llm = ChatOllama(model="qwen2.5:7b", temperature=0.7)


def chat_node(state: State):
    return {"messages": [llm.invoke(state["messages"])]}


builder = StateGraph(State)
builder.add_node("chat", chat_node)
builder.add_edge(START, "chat")
builder.add_edge("chat", END)
graph = builder.compile()


if __name__ == "__main__":
    result = graph.invoke(
        {"messages": [HumanMessage(content="你好，用一句话介绍你自己")]}
    )
    print(result["messages"][-1].content)
