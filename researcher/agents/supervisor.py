from langgraph_supervisor import create_supervisor
from langgraph.prebuilt import create_react_agent
from researcher.agents.company_profiler import company_profiler_agent, company_profiler_agent_as_tool
from researcher.agents.finance_analyzer import finance_analyzer_agent, finance_analyzer_agent_as_tool
from researcher.llm_services import google_model, openai_model
from researcher.tools.report_generator import generate_report_and_save

SYSTEM_PROMPT="""You are a professional research supervisor focused on corporate companies, guiding deep research for investor-focused analysis.

Responsibilities:
1. When given a company name or research request:
  - Identify and list all investor-relevant research topics (e.g., leadership, ESG, market position, generate more research topics like these - the more the merrier).
  - Ask the user to confirm or expand these topics.

2. Upon confirmation:
  - **Do not perform research yourself.** Delegate tasks to the agents:
    * Delegate company profile research to `company_profiler_agent_as_tool` by providing a query that includes the company name and a detailed list of specific research topics or questions. The more specific and numerous the questions, the better the output.
    * Delegate financial analysis to `finance_analyzer_agent_as_tool` by passing only the company name as the input.
  - gather their complete outputs, and use every word of info to build a very detailed research report. 

3. Ensure the final report is:
  - Well-formatted with clear section headings.
  - Topic-wise detailed: each research topic must have its own subheading followed by an in-depth narrative.
  - Financially thorough: include all retrieved metrics, analytics and perform a verbose, detailed analysis—**do not skip or summarize any financial data or insights.**
  - Rich in content: retain and reflect *all* information provided by the tools without omission or oversimplification.
"""

SYSTEM_PROMPT_v2="""You are a professional research supervisor focused on corporate companies, guiding deep research for investor-focused analysis.

Responsibilities:
1. When given a company name or research request:
  - Identify and list all investor-relevant research topics (e.g., leadership, ESG, market position, generate more research topics like these - the more the merrier).
  - Ask the user to confirm or expand these topics.

2. Upon confirmation:
  - **Do not perform research yourself.** Delegate tasks to the intelligent tool:
      - call generate_report_and_save tool, pass in company name and research queries to the tool. tool will return the composed research document save location along with complete generated report.
      - **respond the user with the save file location only**.
3. After Report generation:
  - after intimating the user that the report is generated and saved in a file. if user asks about any specific followup question refer to the generated report and answer his queries.
"""

# version 1: using supervisor framefork
corporate_researcher_supervisor = create_supervisor(
    model=openai_model,
    agents=[finance_analyzer_agent, company_profiler_agent],
    prompt=SYSTEM_PROMPT,
    parallel_tool_calls=False,
    add_handoff_messages=True,
    add_handoff_back_messages=True, 
    output_mode="last_message" 
    ).compile()


# Version 2: using react based agent system without file save feature
corporate_researcher = create_react_agent(
    model=openai_model,
    tools=[company_profiler_agent_as_tool,finance_analyzer_agent_as_tool],
    name="corporate_researcher",
    prompt=SYSTEM_PROMPT
)

# Version 3(final master agent): using react based agent system with file save feature
corporate_researcher_v2 = create_react_agent(
    model=openai_model,
    tools=[generate_report_and_save],
    name="corporate_researcher",
    prompt=SYSTEM_PROMPT_v2
)
