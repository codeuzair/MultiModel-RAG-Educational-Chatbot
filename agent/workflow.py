# from langgraph.graph import StateGraph, START
# from langgraph.graph.message import add_messages
# from langgraph.prebuilt.tool_node import ToolNode, tools_condition
# from langchain_core.messages import AIMessage
# from typing_extensions import Annotated, TypedDict
# from utils.model_loaders import ModelLoader
# from toolkit.tools import (
#     answer_query_tool,
#     generate_important_questions_tool,
#     summarize_chapter_tool,
# )

# class State(TypedDict):
#     messages: Annotated[list, add_messages]

# class GraphBuilder:
#     def __init__(self):
#         self.model_loader = ModelLoader()
#         self.llm = self.model_loader.load_llm()

#         # Custom tools
#         self.tools = [
#             answer_query_tool,generate_important_questions_tool,summarize_chapter_tool
#             
#         ]

#         # Bind tools to LLM
#         self.llm_with_tools = self.llm.bind_tools(tools=self.tools)
#         self.graph = None

#     def _chatbot_node(self, state: State):
#         # Chatbot invokes LLM with tool routing
#         return {"messages": [self.llm_with_tools.invoke(state["messages"])]}

#     def _end_node(self, state: State):
#         # Default fallback response
#         return {"messages": [AIMessage(content="Sorry, I can’t assist with this.")]}

#     def build(self):
#         graph_builder = StateGraph(State)

#         # Add chatbot, tool, and fallback end nodes
#         graph_builder.add_node("chatbot", self._chatbot_node)
#         graph_builder.add_node("tools", ToolNode(tools=self.tools))
#         graph_builder.add_node("end", self._end_node)

#         # Tool decision based on LLM output, fallback to 'end' if no match
#         graph_builder.add_conditional_edges(
#             "chatbot",
#             tools_condition,
#             {
#                 "__default__": "end"
#             }
#         )

#         # If a tool is used, go back to chatbot
#         graph_builder.add_edge("tools", "chatbot")

#         # Start flow
#         graph_builder.add_edge(START, "chatbot")

#         # Set end node as final step
#         graph_builder.set_finish_point("end")

#         self.graph = graph_builder.compile()

#     def get_graph(self):
#         if self.graph is None:
#             raise ValueError("Graph not built. Call build() first.")
#         return self.graph


from langgraph.graph import StateGraph, START
from langgraph.graph.message import add_messages
from langgraph.prebuilt.tool_node import ToolNode, tools_condition
from langchain_core.messages import AIMessage, HumanMessage
from typing_extensions import Annotated, TypedDict
from utils.model_loaders import ModelLoader
from toolkit.tools import *

class State(TypedDict):
    messages: Annotated[list, add_messages]

class GraphBuilder:
    def __init__(self):
        self.model_loader=ModelLoader()
        self.llm = self.model_loader.load_llm()
        self.tools = [answer_query_tool,generate_important_questions_tool,summarize_chapter_tool]
        llm_with_tools = self.llm.bind_tools(tools=self.tools)
        self.llm_with_tools = llm_with_tools
        self.graph = None
    
    def _chatbot_node(self,state:State):
         return {"messages": [self.llm_with_tools.invoke(state["messages"])]}

    def build(self):
        graph_builder = StateGraph(State)
        
        graph_builder.add_node("chatbot", self._chatbot_node)
        
        tool_node=ToolNode(tools=self.tools)
        graph_builder.add_node("tools", tool_node)
        
        graph_builder.add_conditional_edges("chatbot", tools_condition)
        graph_builder.add_edge("tools", "chatbot")
        graph_builder.add_edge(START, "chatbot")
        
        self.graph = graph_builder.compile()
        
    def get_graph(self):
        if self.graph is None:
            raise ValueError("Graph not built. Call build() first.")
        return self.graph
