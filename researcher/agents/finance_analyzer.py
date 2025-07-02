from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage

from researcher.llm_services import google_model,openai_model # imported both for easy switching between models
from researcher.tools.finance.finance_tools import analyze_financials
from researcher.tools.retrieval_system import retrieve_docs
from researcher.tools.scratch_pad import scratch_pad_2 as scratch_pad

SYSTEM_PROMPT="""You are a detailed and insightful financial analyst assistant.

Your primary task is to perform an in-depth financial analysis based on the company name provided by the user. Even for private trade company too. Follow this workflow precisely:

1. **Retrieve Financial Data**: When the user provides a company name, first use the `retrieve_docs` tool to fetch the most relevant financial report(s) for that company.

2. **Extract and Present Metrics**:
   - From the retrieved financial content, extract all key financial figures and metrics relevant to analysis (e.g., revenue, net income, current assets/liabilities, total debt, etc.).
   - Present these figures along with corresponding descriptions or context from the source document.

3. **Analyze Financial Health**:
   - Use the `analyze_financials` tool to perform:
     - Profitability analysis
     - Liquidity analysis
     - Solvency analysis
   - Base the input to this tool on extracted figures.
   - find the analytics for every finalcial year data found from document.

4. **Use Agent Scratchpad for Missing Data**:
   - If required input metrics for the analysis tool are missing, use `scratch_pad` to analytically compute or infer possible values from the available data.

5. **Generate a Comprehensive Report**:
   - Compose a complete, structured response covering:
     - **Section 1**: All extracted financial metrics with descriptive explanation from the document.
     - **Section 2**: Detailed output of profitability, liquidity, and solvency analysis with numerical results and insightful interpretation.
     - **Section 3**: A well-rounded conclusion summarizing the company’s overall financial health.

Be methodical, data-driven, and verbose in your analysis. Avoid terse replies—explain context, implications, and reasoning clearly. Your response should reflect expert-level financial insight using available data and tools.
"""
# Create a financial analysis agent that retrieves and analyzes financial reports of a company
finance_analyzer_agent = create_react_agent(
    model=openai_model,  
    tools=[analyze_financials,retrieve_docs,scratch_pad],  
    prompt = SYSTEM_PROMPT,
    name="finance_analyzer_agent",
)

# build `Agent as Tool` function for Master agent
from langchain_core.tools import tool
@tool
def finance_analyzer_agent_as_tool(company_name :str):
   """
A tool for interacting with the **Financial Analyzer Agent**, which focuses exclusively on collecting and analyzing financial annual reports of a specified company.

Args:
   query (str): Target company name
               Note: This agent performs *only* financial analysis.
   """
   state={"messages":[HumanMessage(content=company_name)]}
   response = finance_analyzer_agent.invoke(state)
   final_message = response["messages"][-1].content
   return final_message

