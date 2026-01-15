try:
    from langchain.agents import AgentExecutor
    print(f"AgentExecutor found in: {AgentExecutor.__module__}")
except ImportError:
    print("AgentExecutor not in langchain.agents")

try:
    from langchain_community.agent_toolkits import AgentExecutor
    print(f"AgentExecutor found in: {AgentExecutor.__module__}")
except ImportError:
    print("AgentExecutor not in langchain_community.agent_toolkits")

try:
    from langchain.chains.agent import AgentExecutor
    print(f"AgentExecutor found in: {AgentExecutor.__module__}")
except ImportError:
    print("AgentExecutor not in langchain.chains.agent")

try:
    from langchain.agents import create_react_agent
    print(f"create_react_agent found in: {create_react_agent.__module__}")
except ImportError:
    print("create_react_agent not in langchain.agents")

try:
    from langchain_community.agents import create_react_agent
    print(f"create_react_agent found in: {create_react_agent.__module__}")
except ImportError:
    print("create_react_agent not in langchain_community.agents")

