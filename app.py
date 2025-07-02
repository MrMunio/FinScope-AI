from langgraph.checkpoint.memory import InMemorySaver
from researcher.agents.supervisor import corporate_researcher_v2
import chainlit as cl
from langchain_core.messages import HumanMessage
import re
from pathlib import Path

thread_counter = 1

@cl.on_chat_start
async def initialize_chat():
    global thread_counter
    corporate_researcher_v2.checkpointer = InMemorySaver()
    cl.user_session.set("thread_id", thread_counter)
    thread_counter += 1

@cl.on_message
async def on_message(msg: cl.Message):
    state_input = {"messages": [HumanMessage(content=msg.content)]}
    config = {"configurable": {"thread_id": cl.user_session.get("thread_id")}}
    response = await corporate_researcher_v2.ainvoke(state_input, config=config)
    last_msg = response["messages"][-1].content
    # Check for file path pattern
    match = re.search(r'\*\*(.*?)\.txt\*\*', last_msg)
    if match:
        file_path = match.group(1) + ".txt"
        file = Path(file_path)
        if file.exists():
            # Attach download link
            await cl.Message(content=last_msg).send()
            sent_msg = await cl.Message(content=f"📎 [Download]({file.name})").send()
            await cl.File(name=file.name, path=str(file)).send(for_id=sent_msg.id)
            return
    await cl.Message(content=last_msg).send()
