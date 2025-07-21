from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

import re

# === Connect to LM Studio ===
llm = ChatOpenAI(
    openai_api_base="http://127.0.0.1:1234/v1",  # ✅ LM Studio API URL
    openai_api_key="lm-studio",                 # ✅ Dummy key for compatibility
    model="meta-llama-3-8b-instruct"            # ✅ Using available model
)

def extract_python_code(text):
    """Extract Python code from markdown or mixed text"""
    # Try to find code blocks first
    code_blocks = re.findall(r'```(?:python)?\n(.*?)\n```', text, re.DOTALL)
    if code_blocks:
        return '\n'.join(code_blocks)
    
    # If no code blocks, try to find lines that look like Python code
    lines = text.split('\n')
    code_lines = []
    for line in lines:
        # Skip explanatory text, keep code-like lines
        if (line.strip() and 
            not line.startswith('Here is') and 
            not line.startswith('When you') and 
            not line.startswith('The ') and 
            not line.startswith('In this') and
            not line.strip().startswith('[') and
            ('=' in line or 'def ' in line or 'print(' in line or 'return ' in line or line.strip().startswith('#'))):
            code_lines.append(line)
    
    return '\n'.join(code_lines) if code_lines else text

# === Agent 2: Coder ===
def agent2_coder(task_request):
    print("[Agent 2] Generating code for the task...")
    response = llm.invoke([
        HumanMessage(
            content=f"Write Python code that solves this task and shows the result. Only return executable Python code, no explanations or markdown:\n{task_request}"
        )
    ])
    return response.content

# === Agent 1: Messenger ===
def agent1_messenger(user_input):
    print("\n[Agent 1] Received user input.")
    coder_response = agent2_coder(user_input)
    print("[Agent 1] Sending code back to user.\n")
    return coder_response

# === Main loop ===
if __name__ == "__main__":
    print("Two-Agent Python Code Generator\n")
    while True:
        user_prompt = input("You: ")
        if user_prompt.lower() in ["exit", "quit"]:
            break
        final_output = agent1_messenger(user_prompt)
        print(f"\n💡 Code:\n{final_output}\n")
        
        # Optional: Execute the code if it's safe
        try:
            # Extract just the Python code
            clean_code = extract_python_code(final_output)
            if clean_code.strip():
                print("Result:")
                exec(clean_code)
                print()
            else:
                print("⚠️ No executable code found\n")
        except Exception as e:
            print(f"⚠️ Could not execute code: {e}\n")
