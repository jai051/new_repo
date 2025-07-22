from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from tavily import TavilyClient
import re

# === Connect to LM Studio (Deepseek or LLaMA etc.) ===
llm = ChatOpenAI(
    openai_api_base="http://127.0.0.1:1234/v1",
    openai_api_key="lm-studio",  # Dummy key
    model="meta-llama-3-8b-instruct"
)

# === Tavily Web Search Client (with your API key) ===
tavily = TavilyClient(api_key="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")

# === Extract Python Code from LLM Output ===
def extract_python_code(text):
    code_blocks = re.findall(r'```(?:python)?\n(.*?)\n```', text, re.DOTALL)
    if code_blocks:
        return '\n'.join(code_blocks)
    
    lines = text.split('\n')
    code_lines = []
    for line in lines:
        if (line.strip() and 
            not line.startswith('Here is') and 
            not line.startswith('When you') and 
            not line.startswith('The ') and 
            not line.startswith('In this') and
            not line.strip().startswith('[') and
            ('=' in line or 'def ' in line or 'print(' in line or 'return ' in line or line.strip().startswith('#'))):
            code_lines.append(line)
    
    return '\n'.join(code_lines) if code_lines else text

# === Agent 2: Code Generator ===
def agent2_coder(task_request):
    print("[Agent 2] Generating code for the task...")
    response = llm.invoke([
        HumanMessage(
            content=f"Write Python code that solves this task and shows the result. "
                    f"Only return executable Python code, no explanations or markdown:\n{task_request}"
        )
    ])
    return response.content

# === Agent 3: Web Search using Tavily ===
def agent3_websearch(query):
    print("[Agent 3] Doing a web search...")
    results = tavily.search(query=query, search_depth="basic", max_results=1)
    if results and "results" in results and results["results"]:
        return results["results"][0]["content"]
    return "No relevant web information found."

# === Agent 1: Decision Maker ===
def agent1_messenger(user_input):
    print("\n[Agent 1] Received user input.")
    
    # Simple heuristic: use keywords to determine if search is needed
    if any(keyword in user_input.lower() for keyword in ["who", "what", "when", "where", "why", "news", "latest", "explain", "summarize", "current"]):
        print("[Agent 1] Detected that web search might be helpful.")
        web_info = agent3_websearch(user_input)
        print("[Agent 1] Passing web info + prompt to coder.")
        combined_request = f"{user_input}\n\nUse this info if needed:\n{web_info}"
        coder_response = agent2_coder(combined_request)
    else:
        print("[Agent 1] Passing prompt directly to coder.")
        coder_response = agent2_coder(user_input)
    
    print("[Agent 1] Sending code back to user.\n")
    return coder_response

# === Main Interactive Loop ===
if __name__ == "__main__":
    print("🤖 Three-Agent Python Code Generator (LangChain + Tavily + LM Studio)\n")
    while True:
        user_prompt = input("You: ")
        if user_prompt.lower() in ["exit", "quit"]:
            break
        final_output = agent1_messenger(user_prompt)
        print(f"\n💡 Code:\n{final_output}\n")
        
        # Optional: Execute the code if it's safe
        try:
            clean_code = extract_python_code(final_output)
            if clean_code.strip():
                print("📊 Result:")
                exec(clean_code)
                print()
            else:
                print("⚠️ No executable code found\n")
        except Exception as e:
            print(f"⚠️ Could not execute code: {e}\n")
