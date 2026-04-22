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
#     return f"Report generated successfully and saved at location: extracts\AstraZeneca_research_report_20260119_083949.txt" + "\n\n" + f"""Generated Report :  ### AstraZeneca Company Profile

# **Overview:**
# AstraZeneca is a British-Swedish multinational biopharmaceutical company that was formed in 1999 through the merger of Astra AB and Zeneca Group PLC. It is headquartered in Cambridge, UK, and is involved in the discovery, development, manufacturing, and marketing of prescription medicines, focusing on areas such as oncology, cardiovascular diseases, renal, metabolism, and respiratory diseases.

# ---

# **Key Information:**
# - **Year Founded:** 1999
# - **Founders:** Merged from Astra AB and Zeneca Group PLC.
# - **Headquarters:** Cambridge, UK.
# - **Current Leadership:** 
#   - **CEO:** Pascal Soriot
#   - Leadership team includes various executives responsible for different therapeutic areas.

# ---

# #### Financial Performance & Key Metrics:
# - **2023 R&D Expenditure:** Approximately €13.6 billion, reflecting AstraZeneca’s commitment to research, as it allocates over 20% of its revenue towards R&D.
# - **Q1 2025 Financial Results:**
#   - **Total Revenue:** $13.6 billion, a 10% increase year-over-year.
#   - **Core EPS:** Increased by 21% to $2.49.
#   - **Gross Margin:** 84%.
# - **Future Projections:** AstraZeneca targets $80 billion in total revenue by 2030 with continued growth expected across major geographic regions.

# ---

# #### Pipeline and R&D Focus:
# AstraZeneca maintains one of the largest R&D pipelines globally, with a significant focus on oncology drugs such as:
# - **Enhertu** and **Imfinzi**, with several ongoing Phase III clinical trials.
# - Five positive Phase III study readouts were announced recently, indicating a promising pipeline for drug developments.

# ---

# #### Market Position and Competitive Advantage:
# AstraZeneca is recognized for its robust position in the pharmaceutical industry, particularly in oncology, where it competes with major players like Pfizer and Merck. Its strategies for innovation, including partnerships and collaborations, bolster its competitive edge.

# ---

# #### Recent Acquisitions and Partnerships:
# - **EsoBiotec Acquisition:** Acquiring in vivo cell therapy technology for up to $1 billion.
# - **Modella AI:** Focus on enhancing oncology drug research through AI-driven methodologies.
# - Various strategic collaborations to strengthen its capabilities in drug development and manufacturing across different therapeutic areas.

# ---

# #### ESG (Environmental, Social, and Governance) Practices:
# - AstraZeneca is committed to achieving net-zero emissions by 2050 and emphasizes reducing environmental impact. 
# - It invests in health equity initiatives globally, striving to improve access to its medicines.
# - Recent reports indicate challenges related to drug pricing in emerging markets, which may impact its ESG ratings.

# ---

# #### Regulatory Approvals and Clinical Trial Results:
# Recent approvals for oncology drugs demonstrate AstraZeneca’s capacity to launch successfully in major markets. The company rolls out frequent updates regarding its clinical trial results and continues to engage in new regulatory submissions across different regions.

# ---

# #### Stakeholder Engagement and Corporate Governance:
# AstraZeneca emphasizes transparency with stakeholders, particularly regarding its ESG initiatives and corporate governance practices. Annual sustainability engagement events with shareholders reveal the company's commitment to stakeholder communication and responsibility.

# ---

# #### Additional Insights:
# - AstraZeneca reflects a shift towards a diverse portfolio and focuses on leveraging advancements in technology and AI to promote more effective healthcare solutions.
# - The company maintains a wide-ranging global market presence with operations in over 100 countries, ensuring extensive access to healthcare professionals and patients.

# ---

# ### Sources:
# 1. [Business Wire](https://www.businesswire.com/news/home/20250428918895/en/AstraZenecas-Q1-2025-Financial-Results)
# 2. [Statista](https://www.statista.com/topics/7584/astrazeneca/)
# 3. [KnowESG](https://www.knowesg.com/esg-ratings/astrazeneca-plc)
# 4. [Bloomberg](https://www.bloomberg.com/quote/AZN:LN)
# 5. [Reuters](https://www.reuters.com/legal/litigation/astrazeneca-acquire-modella-ai-speed-oncology-drug-research-2026-01-13)
  
# This summary encapsulates key aspects of AstraZeneca's operations, leadership, financial data, and strategic focus areas while highlighting its commitment to innovation, sustainability, and stakeholder engagement."""

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