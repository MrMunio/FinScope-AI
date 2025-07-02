from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
import os

fast_model = "meta-llama/llama-4-maverick:free"
powerful_model = "deepseek/deepseek-chat-v3-0324:free"
open_router_model=ChatOpenAI(model=powerful_model,base_url="https://openrouter.ai/api/v1",api_key=os.getenv("OPEN_ROUTER_API_KEY"))
openai_model=ChatOpenAI(model="gpt-4o-mini",api_key=os.getenv("OPENAI_API_KEY"))
google_model=ChatGoogleGenerativeAI(model="gemini-2.0-flash-lite",api_key=os.getenv("GOOGLE_API_KEY"))

if __name__=="__main__":
    print(google_model.invoke("hi"))