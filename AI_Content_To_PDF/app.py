import streamlit as st
from bs4 import BeautifulSoup
import html as html_module
import re
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_community.document_loaders import WebBaseLoader

from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from datetime import datetime
import os
from dotenv import load_dotenv

# testing-url ='https://www.realme.com/global/realme-gt-neo-3t/specs'

# Load API key
load_dotenv()

# LangChain looks for GOOGLE_API_KEY automatically
api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    raise ValueError(
        "API key not found! Please set GOOGLE_API_KEY in your .env file")


# # Initialize model
model = ChatGoogleGenerativeAI(model="gemini-1.5-flash", api_key=api_key)

template = '''You are expert in data extraction,data summarization and data validation checker from web_pages.
I give you {data} that I have extract from web-page  Summarize it and expand content with additional context.
Validate claims with reasoning (optional but recommended).

Rules:
- Summarize this {data} and add content with aditional context if you know about that otherwise just return dataAdditional context and background information that would be valuable
- Check the validation, claims with reasoning if you can do.
- Return data in such way that in future it will used to make PDF or Magzine.
- Avoid hallucination and research on it.Key takeaways and insights.
- No need of any graph, pictures and structure output(json,dict,etc..).
Format your response as a structured analysis that would be valuable for a PDF document.
 
'''

# Extract Data from WebPage
def extract_data(url):
    """Extract content from webpage"""
    loader = WebBaseLoader(url)
    data = loader.load()
    page_data = data[0].page_content
    return page_data

# Enhance extracted data from AI
def enhance_content(docs):
    """Sends content to Gemini / LLM."""
    prompt = PromptTemplate(template=template, input_variables=["docs"])
    final_prompt = prompt.format(data=docs) 
    response = model.invoke(final_prompt)
    return response
    # returns enhanced version  

def clean_html_to_text(html_or_text: str) -> str:
    """
    Convert HTML or messy text into clean plain text:
    - remove tags
    - convert <br> and <p> to line breaks
    - unescape HTML entities (&amp; -> &)
    - normalize whitespace while preserving paragraph breaks
    """
    if html_or_text is None:
        return ""
    text = str(html_or_text)

    # If it looks like HTML, use BeautifulSoup to extract text
    if "<" in text and ">" in text:
        soup = BeautifulSoup(text, "lxml")

        # convert <br> to newline
        for br in soup.find_all("br"):
            br.replace_with("\n")

        # mark paragraphs so we can preserve paragraph breaks
        for p in soup.find_all("p"):
            # insert paragraph marker before each <p> block
            p.insert_before("\n\n")
        # get text with spaces as separators for inline elements
        text = soup.get_text(separator=" ")

    # unescape HTML entities
    text = html_module.unescape(text)

    # Normalize whitespace BUT preserve paragraph markers:
    # 1) temporarily preserve double-newlines as a token
    text = re.sub(r'\n\s*\n', '[PARA_TOKEN]', text)
    # 2) collapse all other whitespace (newlines, tabs, multiple spaces) to single space
    text = re.sub(r'\s+', ' ', text)
    # 3) restore paragraph tokens as double newlines
    text = text.replace('[PARA_TOKEN]', '\n\n').strip()

    # Finally, ensure there's a space between letters/words if something got concatenated:
    text = re.sub(r'([a-zA-Z0-9])([<\[{(])', r'\1 \2', text)  
    return text

def generate_pdf(enhanced_content, output_path="enhanced_content.pdf"):
    """
    Generate a PDF for the enhanced_content string.
    Returns absolute path to the file on success, else None.
    """
    try:
        enhanced_content = clean_html_to_text(enhanced_content)
        # Ensure content is string
        if enhanced_content is None:
            enhanced_content = ""
        if not isinstance(enhanced_content, str):
            try:
                enhanced_content = str(enhanced_content)
            except Exception:
                enhanced_content = ""

        # Truncate extremely long strings for paragraph chunking later if necessary
        # ReportLab can choke on very long single Paragraphs — so split into paragraphs.
        paragraphs = [p.strip() for p in enhanced_content.split("\n\n") if p.strip()]
        if not paragraphs:
            paragraphs = [enhanced_content]

        # Use absolute path so os.path.exists checks match
        abs_path = os.path.abspath(output_path)
        doc = SimpleDocTemplate(abs_path, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []

        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            alignment=TA_CENTER,
            textColor=colors.darkblue,
            spaceAfter=20,
        )
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.darkgreen,
            spaceAfter=12,
        )
        content_style = ParagraphStyle(
            'CustomContent',
            parent=styles['Normal'],
            fontSize=11,
            alignment=TA_JUSTIFY,
            leftIndent=12,
            rightIndent=12,
            spaceAfter=18,
        )

        # Title and metadata
        story.append(Paragraph("AI-Enhanced Content Report", title_style))
        story.append(Spacer(1, 8))
        story.append(Paragraph(f"<b>Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", content_style))
        story.append(Spacer(1, 12))

        # Add enhanced content paragraphs
        story.append(Paragraph("AI-Enhanced Content", subtitle_style))
        for para in paragraphs:
            # Replace single newlines with <br/> within a paragraph (safe)
            safe_para = para.replace("\n", "<br/>")
            story.append(Paragraph(safe_para, content_style))

        # Build PDF
        doc.build(story)

        # Confirm file exists
        if os.path.exists(abs_path):
            return abs_path
        else:
            print("generate_pdf: file not found after build:", abs_path)
            return None

    except Exception as e:
        # show error to console / Streamlit
        print("Error generating PDF:", e)
        return None

    
#Reset all program
def reset_app():
    """Completely restart the Streamlit app."""
    st.session_state.clear()  
    st.rerun()  

# main func
def main():
    
    # Page configuration
    st.set_page_config(
        page_title="URL-to-PDF",
        page_icon="🔍",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    
    # Main title
    st.title("🤖 AI Content-to-PDF")
    st.markdown("Convert your content into structured PDF format.")

    url = st.text_input('please enter url of a web-page:', placeholder="Enter your url here...")
        
    if st.button("Extract Data"):
            if url.strip() == "":
                st.warning("⚠️ Please enter a url first.")
            else:
                docs = extract_data(url)
                st.session_state["docs"] = docs  # save in session_state
                st.write(docs)
               
    
    # button 2: AI modified data
    if st.button("AI Modified Data"):
        if "docs" not in st.session_state:
           st.warning("⚠️ Please extract data first.")
        else:
          enhanced = enhance_content(st.session_state["docs"])
          st.session_state["enhanced"] = enhanced
          st.write("✨ AI Modified Data:")
          st.write(enhanced)   
          
    # ---- Generate PDF ----
    if st.button("📄 Generate PDF"):
       if "enhanced" not in st.session_state or not st.session_state["enhanced"]:
        st.warning("⚠️ Please modify data first.")
       else:
          # generate and get absolute path
            pdf_path = generate_pdf(st.session_state["enhanced"], "enhanced_content.pdf")
            if pdf_path and os.path.exists(pdf_path):
               st.success("📄 PDF generated successfully!")
               with open(pdf_path, "rb") as f:
                st.download_button(
                    "⬇️ Download PDF",
                    f,
                    file_name=os.path.basename(pdf_path),
                    mime="application/pdf",
                )
            else:
              st.error("❌ Failed to generate PDF. Check logs or console for details.")

            
    # Sidebar
    st.sidebar.title("📄 Instructions")
    st.sidebar.markdown('''Web content often lacks depth or accuracy. AI can enhance content by adding context, 
    validating facts, and producing higher-quality summaries
    ''')
    st.sidebar.markdown('''1- Enter URL of Webpage \n 2- CLick on the ('Extract Data') \n 3- Click on the ('AI Modified Data') \n 4- Click on the ('Generate PDF')  ''')
    
    
    
    # Reset button
    if st.button("🔁 Reset App"):
      reset_app()
      
      
      # Inject CSS
    st.markdown(
    """
    <style>
        /* Optional: change sidebar color */
        section[data-testid="stSidebar"] {
            background-color: #e6f0ff;  /* light blue */
        }
        
    </style>
    """,
    unsafe_allow_html=True
    )  
                   

# python main
if __name__ == "__main__":
    main()           
    
