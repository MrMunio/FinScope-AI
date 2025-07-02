from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage,HumanMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph,END
from langgraph.prebuilt import ToolNode

# import tools and models
from researcher.tools.web_tools.brave_search import batch_web_search # for Brave search
from researcher.tools.web_tools.google_pse_search import batch_pse_web_search # for switching to Google PSE search
from researcher.tools.web_tools.scrapper import scrape_urls 
from researcher.tools.scratch_pad import scratch_pad_1 as scratch_pad
from researcher.llm_services import google_model,openai_model

from datetime import datetime

def generate_web_researcher_prompt() -> str:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    prompt = f"""Current date & time (IST): {timestamp}

You are a professional company profile agent. When given a company name and research query, follow these instructions:

1. Analyze the user's request to determine all possible relevant questions or information needs (e.g., founders, revenue, leadership, etc.) and generate multiple queries accordingly. Use `batch_web_search` to process multiple search queries at once.
   
2. Review the *search snippets* returned by `batch_web_search`. Record any direct answers, useful data, or insights found in the snippets to the `scratch_pad` before initiating any scraping.

3. For missing or incomplete data:
   - Prioritize *official or high-authority URLs*.
   - Use `scrape_urls` to extract content from selected URLs.

4. Extract and compile the following (at minimum):
   - Year founded
   - Founders
   - Headquarters
   - Current leadership (CEO, Chairman, etc.)
   - Industry and offerings (products/services)
   - Number of employees and revenue (if available)
   - Any additional information relevant to the company—even if not explicitly requested.

5. Your goal is to gather *as much relevant company information as possible*. Go beyond the user query where appropriate—the more insights, the better.

6. Use `scratch_pad` for all intermediate analysis, observations, or planning.

7. Respond only when:
   - You have confidently extracted all available and relevant information.
   - No further search is expected to yield additional insights.

8. Your final output should be a *comprehensive, well-formatted, professional, and descriptive summary* of the company, followed by the list of source URLs used.

Tools available: `batch_web_search`, `scrape_urls`, `scratch_pad`
"""
    return prompt


tools=[batch_web_search,scrape_urls,scratch_pad]

llm = openai_model.bind_tools(tools)

class AgentState(TypedDict):
    messages:Annotated[Sequence[BaseMessage],add_messages]

# node 1
def llm_inference(state:AgentState)->AgentState:
    web_researcher_system_prompt=generate_web_researcher_prompt()
    system_prompt=SystemMessage(content=web_researcher_system_prompt)
    result = llm.invoke([system_prompt]+state["messages"])
    return {"messages":[result]}

# route conditional logic
def should_continue(state:AgentState)->str:
    last_message=state['messages'][-1]
    if not last_message.tool_calls:
        return "end"
    else:
        return "continue"
    
graph=StateGraph(AgentState)

graph.add_node("llm",llm_inference)
graph.add_node("tools",ToolNode(tools))

graph.set_entry_point("llm")
graph.add_conditional_edges(
    "llm",
    should_continue,
    {
        "end":END,
        "continue":"tools"
    }
)
graph.add_edge("tools","llm")

company_profiler_agent=graph.compile(name="company_profiler_agent")

# build `Agent as Tool` function for Master agent
from langchain_core.tools import tool
@tool
def company_profiler_agent_as_tool(query:str)-> str:
    """
A tool for interacting with the **Company Profiler Agent**, which specializes in gathering comprehensive non-financial information about a given company.

Args:
    query (str): A detailed query specifying the target company and the research topics to be explored. 
                 Note: This agent does *not* handle financial research.
"""
    state={"messages":[HumanMessage(content=query)]}
    response = company_profiler_agent.invoke(state)
    final_message = response["messages"][-1].content
    return final_message

