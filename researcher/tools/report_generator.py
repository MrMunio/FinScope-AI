from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from researcher.agents.company_profiler import company_profiler_agent
from researcher.agents.finance_analyzer import finance_analyzer_agent
from datetime import datetime
import os

# A single tool for generating a comprehensive research report, utilizing two Sub Agents, on a given company. this will be used by Master Agent(final version).
@tool
def generate_report_and_save(company_name: str, research_topics: str):
    """
    Generates a comprehensive research report on a given company.

    This function uses AI agents to collect and analyze data related to:
    - The company's general profile based on provided research topics.
    - The company's latest financial metrics and analytics.

    Args:
        company_name (str): Name of the company to research.
        research_topics (str): Topics or questions for company profile research.

    Returns:
        str: Success message with the file path of the saved report along with entire report generated, or error message.
    """
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_dir = "extracts"
    # Create directory if it doesn't exist
    os.makedirs(file_dir, exist_ok=True)
    file_name = f"{company_name}_research_report_{timestamp}.txt"
    prompt_1= f"""Company Name: {company_name}
Research Topics:
{research_topics}"""
    prompt_2 = f"Company Name: {company_name}"
    response_1 = company_profiler_agent.invoke({"messages":[HumanMessage(content=prompt_1)]})
    response_2 = finance_analyzer_agent.invoke({"messages":[HumanMessage(content=prompt_2)]})

    profile_details = response_1["messages"][-1].content
    financial_details = response_2["messages"][-1].content

    # Check if both responses are too short
    profile_valid = len(profile_details) >= 500
    financial_valid = len(financial_details) >= 500
    
    if not profile_valid and not financial_valid:
        return "Failed to perform research due to some technical issues."
    
    # Build report with only valid sections
    report_sections = []
    
    if profile_valid:
        report_sections.append(profile_details)
    
    if financial_valid:
        report_sections.append(financial_details)
    
    report = "\n\n\n".join(report_sections)
    
    file_path = os.path.join(file_dir, file_name)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(report)
    
    return f"Report generated successfully and saved at location: {file_path}" + "\n\n" + f"Generated Report :{report}"
    
if __name__=="__main__":
    print(generate_report_and_save("deloitte","all kinds of topics"))