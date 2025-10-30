"""
LLM Handler - Integrate with Google Gemini API for answer generation
"""
import os
from dotenv import load_dotenv
import google.generativeai as genai


# Load environment variables
load_dotenv()

# Configure Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if GEMINI_API_KEY and GEMINI_API_KEY != "your_gemini_api_key_here":
    genai.configure(api_key=GEMINI_API_KEY)
    # FIXED: Use gemini-2.0-flash-exp (correct available model)
    model = genai.GenerativeModel('gemini-2.5-flash')
else:
    model = None
    print("⚠️  Gemini API key not configured. Using fallback mode.")

def create_legal_prompt(query, context):
    """
    Create a prompt for legal question answering

    Args:
        query: User's legal question
        context: Retrieved relevant legal text chunks

    Returns:
        Formatted prompt string
    """
    prompt = f"""You are a legal assistant specializing in Indian law (IPC, CrPC, and other statutes).

**IMPORTANT INSTRUCTIONS:**
1. Answer the user's question based PRIMARILY on the provided legal document excerpts
2. Cite specific sections, articles, or provisions when available
3. If the provided context doesn't contain enough information, you may supplement with your knowledge but CLEARLY indicate this
4. Be precise, accurate, and use legal terminology appropriately
5. Always include a disclaimer that this is for informational purposes only

**LEGAL DOCUMENT EXCERPTS:**
{context}

**USER QUESTION:**
{query}

**YOUR ANSWER:**
Please provide a comprehensive answer with:
1. Direct answer to the question
2. Relevant legal sections/provisions (with citations)
3. Brief explanation in simple language
4. Disclaimer about consulting a qualified lawyer

Answer:"""

    return prompt

def generate_answer(query, context, use_simple_fallback=False):
    """
    Generate answer using Gemini API or fallback method

    Args:
        query: User's legal question
        context: Retrieved context from PDFs
        use_simple_fallback: If True, use simple extraction instead of LLM

    Returns:
        Generated answer text
    """
    # If no context, return early
    if not context or len(context.strip()) < 50:
        return generate_fallback_answer(query, "No relevant information found in the legal documents.")

    # Try using Gemini API
    if model is not None and not use_simple_fallback:
        try:
            prompt = create_legal_prompt(query, context)
            response = model.generate_content(prompt)

            if response and response.text:
                return response.text
            else:
                print("⚠️  Empty response from Gemini, using fallback")
                return generate_fallback_answer(query, context)

        except Exception as e:
            print(f"⚠️  Error calling Gemini API: {e}")
            return generate_fallback_answer(query, context)

    # Fallback: Simple extraction-based answer
    return generate_fallback_answer(query, context)

def generate_fallback_answer(query, context):
    """
    Generate a simple answer without LLM (fallback mode)

    Args:
        query: User's question
        context: Retrieved context

    Returns:
        Formatted answer based on retrieved context
    """
    answer = f"""**Based on the available legal documents:**

{context}

---

**Regarding your question:** "{query}"

The above sections from the legal documents are relevant to your query. Please review the specific provisions and sections mentioned.

**⚠️ DISCLAIMER:** This information is for reference purposes only and does not constitute legal advice. Please consult a qualified lawyer for advice specific to your situation.

**Note:** This response is based on document retrieval. For a more comprehensive AI-generated answer, please configure the Gemini API key in your .env file.
"""

    return answer

def generate_quick_answer(query):
    """
    Generate a quick answer using only Gemini (no retrieval)
    Useful when no documents are indexed yet

    Args:
        query: User's legal question

    Returns:
        Answer text
    """
    if model is None:
        return """I apologize, but I need either:
1. Legal documents to be indexed (run the ingestion script), OR
2. Gemini API to be configured

Please set up the system first by:
- Adding PDF files to data/pdfs/ folder
- Running: python backend/ingestion.py
- Or configuring GEMINI_API_KEY in .env file

For now, I cannot answer your question accurately."""

    try:
        prompt = f"""You are a legal assistant specializing in Indian law.

Question: {query}

Provide a helpful answer about Indian legal provisions (IPC, CrPC, etc.) related to this question. 
Include relevant sections if you know them, and always end with a disclaimer about consulting a lawyer.

Keep your answer concise but informative."""

        response = model.generate_content(prompt)

        if response and response.text:
            return response.text + "\n\n**⚠️ DISCLAIMER:** This is for informational purposes only. Please consult a qualified lawyer for legal advice."
        else:
            return "Unable to generate answer. Please try again."

    except Exception as e:
        return f"Error generating answer: {str(e)}\n\nPlease check your API configuration."

def check_api_configured():
    """Check if Gemini API is properly configured"""
    return model is not None

def get_api_status():
    """Get status of API configuration"""
    if model is not None:
        return {"status": "configured", "model": "gemini-2.5-flash"}
    else:
        return {"status": "not_configured", "message": "Please set GEMINI_API_KEY in .env file"}
