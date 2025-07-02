from researcher.agents.company_profiler import company_profiler_agent_as_tool
from researcher.agents.finance_analyzer import finance_analyzer_agent_as_tool
from researcher.tools.report_generator import generate_report_and_save


# print(finance_analyzer_agent_as_tool.invoke({"company_name":"Deloitte"}))
# print(company_profiler_agent_as_tool.invoke({"query":"company Deloitte and research aboutall all possible  queries useful for any investor"}))
#
print(generate_report_and_save.invoke({"company_name":"deloitte","research_topics":"all kinds of topics"}))
