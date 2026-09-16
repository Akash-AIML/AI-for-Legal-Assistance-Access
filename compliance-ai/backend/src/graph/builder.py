"""LangGraph decision workflow builder.

Flow: understand -> retrieve -> assess -> decide
          -> ANSWER        -> generate
          -> CLARIFY       -> clarify
          -> ESCALATE      -> escalate
          -> RETRIEVE_MORE -> retrieve_more -> assess -> decide (bounded, 1 retry)
"""
from __future__ import annotations

from functools import lru_cache

from langgraph.graph import END, START, StateGraph

from graph import nodes
from graph.state import GraphState


def build_graph():
    g = StateGraph(GraphState)

    g.add_node("understand", nodes.node_understand)
    g.add_node("retrieve", nodes.node_retrieve)
    g.add_node("assess", nodes.node_assess)
    g.add_node("decide", nodes.node_decide)
    g.add_node("generate", nodes.node_generate)
    g.add_node("clarify", nodes.node_clarify)
    g.add_node("escalate", nodes.node_escalate)
    g.add_node("retrieve_more", nodes.node_retrieve_more)

    g.add_edge(START, "understand")
    g.add_edge("understand", "retrieve")
    g.add_edge("retrieve", "assess")
    g.add_edge("assess", "decide")

    g.add_conditional_edges(
        "decide",
        nodes.route_after_assess,
        {
            "generate": "generate",
            "clarify": "clarify",
            "escalate": "escalate",
            "retrieve_more": "retrieve_more",
        },
    )

    g.add_edge("retrieve_more", "assess")
    g.add_edge("generate", END)
    g.add_edge("clarify", END)
    g.add_edge("escalate", END)

    return g.compile()


@lru_cache(maxsize=1)
def get_graph():
    return build_graph()