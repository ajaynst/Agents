import gradio as gr
from agent_core import SQLAgent

# Initialize the agent
sql_agent = SQLAgent()

def chat_interface(message, history):
    history = history or []
    
    # Get the agent's response
    response = sql_agent.invoke(message)
    
    # Check for clarification requests
    if response.startswith("CLARIFICATION_NEEDED:"):
        # The agent needs more information
        # We will format this to be a question to the user
        clarification_question = response.replace("CLARIFICATION_NEEDED:", "").strip()
        history.append((message, clarification_question))
    else:
        # The agent has provided a direct answer
        history.append((message, response))
        
    # Gradio's ChatInterface expects the last message to be the user's input, 
    # and the returned string to be the bot's response.
    # By returning an empty string, we prevent duplicating the user's message.
    return "", history

# Create the Gradio interface
iface = gr.ChatInterface(
    fn=chat_interface,
    title="SQL RAG Agent",
    description="Ask questions about your database in natural language.",
    examples=[
        "How many customers are there?",
        "What is the total loan amount for each customer?",
        "Show me the loans disbursed in the last 3 months.",
        "what is the sum of all deposits in branch_1?",
        "show it to the user in a table format"
    ],
    chatbot=gr.Chatbot(height=500),
    textbox=gr.Textbox(placeholder="Ask your question here...", container=False, scale=7),
    clear_btn="Clear",
)

if __name__ == "__main__":
    iface.launch()
