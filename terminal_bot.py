from researcher.agents.supervisor import corporate_researcher_supervisor,corporate_researcher_v2 # Import the Compiled Master Agent Graph
from researcher.agents.company_profiler import company_profiler_agent
from researcher.agents.finance_analyzer import finance_analyzer_agent


if __name__=="__main__":
    # Run the compiled master agent graph as an interactive chatbot in terminal
    from researcher.utils.chat_utils import chat_interface
    chat_interface(corporate_researcher_v2)