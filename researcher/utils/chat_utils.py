from langchain_core.messages import  AIMessage, HumanMessage, ToolMessage

def chat_interface(compiled_graph):
    """Enhanced terminal chat interface for the ReAct agent"""
    print("\n🤖AI Agent Chat Interface")
    print("Type 'quit' or 'exit' to end the conversation")
    # print("Type 'debug' to toggle detailed execution trace\n")
    
    conversation_state = {"messages": []}
    show_debug = False
    
    while True:
        # Get user input
        print("\n" + "="*50)
        user_input = input("You: ").strip()
        
        # Check for special commands
        if user_input.lower() in ['quit', 'exit', 'bye']:
            print("👋 Goodbye!")
            break
            
        if user_input.lower() == 'debug':
            show_debug = not show_debug
            print(f"🔧 Debug mode: {'ON' if show_debug else 'OFF'}")
            continue
            
        if not user_input:
            continue
            
        # Store the current message count to track new messages
        initial_msg_count = len(conversation_state["messages"])
        
        # Add user message to conversation
        conversation_state["messages"].append(HumanMessage(content=user_input))
        
        try:
            # Get response from agent
            print("\n🔄 Processing...")
            result = compiled_graph.invoke(conversation_state)
            
            # Update conversation state
            conversation_state = result
            
            # Display the conversation flow for new messages
            new_messages = result["messages"][initial_msg_count:]
            
            print("\n📋 Agent Response:")
            print("-" * 30)
            
            for i, msg in enumerate(new_messages):
                if isinstance(msg, HumanMessage):
                    if show_debug:
                        print(f"👤 Human: {msg.content}")
                
                elif isinstance(msg, AIMessage):
                    if msg.tool_calls:
                        print(f"🤖 Agent: I need to use tools to help with this.")
                        if show_debug:
                            print(f"   Content: {msg.content}")
                        
                        for tool_call in msg.tool_calls:
                            tool_name = tool_call.get('name', 'unknown')
                            tool_args = tool_call.get('args', {})
                            print(f"🔧 Calling tool: {tool_name}({', '.join(f'{k}={v}' for k, v in tool_args.items())})")
                    else:
                        print(f"🤖 Agent: {msg.content}")
                
                elif isinstance(msg, ToolMessage):
                    tool_name = getattr(msg, 'name', 'unknown')
                    print(f"⚙️  Tool '{tool_name}' result: {msg.content}")
            
            # Show final response if it's different from intermediate responses
            final_ai_message = None
            for msg in reversed(result["messages"]):
                if isinstance(msg, AIMessage) and not msg.tool_calls:
                    final_ai_message = msg
                    break
            
            if final_ai_message and len([m for m in new_messages if isinstance(m, AIMessage)]) > 1:
                print(f"\n✅ Final Answer: {final_ai_message.content}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            # Remove the last user message if there was an error
            if len(conversation_state["messages"]) > initial_msg_count:
                conversation_state["messages"] = conversation_state["messages"][:initial_msg_count]

def chat_interface_simple(compiled_graph):
    """Alternative simple interface that shows all message types"""
    print("\n🤖 Simple ReAct Agent Chat")
    print("Type 'quit' to exit\n")
    
    conversation_state = {"messages": []}
    
    while True:
        user_input = input("\nYou: ").strip()
        
        if user_input.lower() in ['quit', 'exit']:
            break
            
        if not user_input:
            continue
        
        # Track messages before processing
        msg_count_before = len(conversation_state["messages"])
        conversation_state["messages"].append(HumanMessage(content=user_input))
        
        try:
            result = compiled_graph.invoke(conversation_state)
            conversation_state = result
            
            # Show all new messages since user input
            new_messages = result["messages"][msg_count_before + 1:]  # +1 to skip the user message we just added
            
            for msg in new_messages:
                if isinstance(msg, AIMessage):
                    if msg.tool_calls:
                        print(f"\n🤖 Agent (with tools): {msg.content}")
                        for tool_call in msg.tool_calls:
                            args_str = ', '.join(f'{k}={v}' for k, v in tool_call.get('args', {}).items())
                            print(f"   🔧 Using: {tool_call.get('name')}({args_str})")
                    else:
                        print(f"\n🤖 Agent: {msg.content}")
                elif isinstance(msg, ToolMessage):
                    print(f"   ⚙️ Tool result: {msg.content}")
                    
        except Exception as e:
            print(f"❌ Error: {e}")
            conversation_state["messages"] = conversation_state["messages"][:-1]