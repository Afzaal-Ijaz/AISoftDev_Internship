import streamlit as st
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
import os
import json
from dotenv import load_dotenv

# Load API key
load_dotenv()

# LangChain looks for GOOGLE_API_KEY automatically
api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    raise ValueError(
        "API key not found! Please set GOOGLE_API_KEY in your .env file")


# # Initialize model
model1 = ChatGoogleGenerativeAI(model="gemini-2.5-flash", api_key=api_key)

# Making template
template = """
You are a expert in Conversion of prompt to JSON format, Please extract the key point or tags from the {text} and return this prompt into a single Json format.For Example         
output ={{ 
            "original_prompt": text,
            "word_count": len(text.split()),
            "character_count": len(text),
            "intent": guess_intent(text),
            "user_goal": None,
            "role": extract_role(text),
            "constraints": extract_constraints(text),
            "examples": extract_examples(text),
            "clarifying_questions": [],
            "tags": [],
            "complexity": estimate_complexity(text)}}

Rules:
- If a field cannot be found,set its value to "Not Given"
- If in the prompt has missing some key/values of json so do not show empty array/list skip it.
- Return only valid JSON (no extra commentry).
- Keep tags as array, keep constraints as arrays and compplexity is must.

"""


#Main Func
def main():

    # Page configuration
    st.set_page_config(
        page_title="Prompt-to-JSON",
        page_icon="🔄",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Main title
    st.title("🔄 Prompt-to-JSON Enhancer")
    st.markdown("Convert your prompt into structured JSON format.")
    # st.info("Sending prompt to Gemini — check logs if something goes wrong.")

    user_text = st.text_area("Enter your prompt:", height=140, placeholder="Enter your prompt here...")
    prompt1 = PromptTemplate(template=template, input_variables=["user_text"])

    
    if st.button("Generate JSON"):
         # Call model
        # with st.spinner("Calling Gemini..."):
            if user_text.strip() == "":
                st.warning("⚠️ Please enter a prompt first.")
            else:
                final_prompt = prompt1.format(text=user_text) 
                response = model1.invoke(final_prompt)

                try:
                    json_output = json.loads(response.content)
                    st.json(json_output) 
                except:
                    st.subheader("JSON Output")
                    st.write(response.content)



# python main
if __name__ == "__main__":
    main()









