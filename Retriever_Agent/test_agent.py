import asyncio
from agent_core import SQLAgent

async def main():
    # Initialize the agent
    sql_agent = SQLAgent()

    # Test cases
    test_questions = [
        "How many customers are there?",
        "What is the total loan amount for each customer? Show me the top 5.",
        "Show me the loans disbursed in the last 3 months.",
        "what is the sum of all deposits in branch_1?",
        "Show me all the loans for the customer with id '3024a891-5f3b-45a1-9c1e-e978aeb31601'",
        "Who has the highest balance?",
        "What is the average loan amount?",
        "List all branches and their locations."
    ]

    for question in test_questions:
        print(f"\n--- Testing question: {question} ---")
        
        # Get the agent's response
        response = sql_agent.invoke(question)
        
        print(f"Agent response:\n{response}")

if __name__ == "__main__":
    asyncio.run(main())
