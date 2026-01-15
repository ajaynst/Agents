from typing import List, Any, Dict
from langchain_groq import ChatGroq
import os
from dotenv import load_dotenv

load_dotenv()
groq_api_key = os.environ.get("GROQ_API_KEY")
llm = ChatGroq(model="llama3-8b-8192", temperature=0, api_key=groq_api_key)

def format_output(question: str, result: List[Dict[str, Any]]) -> str:
    """
    Formats the SQL query result into a user-friendly format.

    Args:
        question: The user's original question.
        result: The result of the SQL query, as a list of dictionaries.

    Returns:
        A formatted string (either a sentence or a Markdown table).
    """
    if not result:
        return "I found no records matching your query."

    if len(result) == 1 and len(result[0]) == 1:
        # Single value result, generate a sentence
        value = list(result[0].values())[0]
        prompt = f"""
        The user asked: '{question}'
        The SQL query returned this value: {value}
        
        Please formulate a concise, natural language sentence that answers the user's question based on this value.
        If the value is a monetary amount, please format it as 'Rs. <amount>'.
        Example: If the user asked 'How many customers are there?' and the value is 100, you should return 'There are 100 customers.'
        """
        sentence_response = llm.invoke(prompt)
        return sentence_response.content
    else:
        # Table result
        headers = result[0].keys()
        header_line = "| " + " | ".join(headers) + " |"
        separator = "| " + " | ".join(["---"] * len(headers)) + " |"
        body_lines = [
            "| " + " | ".join(map(str, row.values())) + " |" for row in result
        ]
        return "\n".join([header_line, separator] + body_lines)
