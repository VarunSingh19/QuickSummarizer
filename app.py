import streamlit as st
import pymongo
import os
import bcrypt
import cloudinary
import cloudinary.uploader
import cloudinary.api
from dotenv import load_dotenv
from datetime import datetime
import tempfile
import time
import requests
import re
from bs4 import BeautifulSoup
from pytube import YouTube
from youtube_transcript_api import YouTubeTranscriptApi
from pathlib import Path
import PyPDF2
import io
from typing import Dict, List
import json

# Summarization agent libraries
from phi.agent import Agent
from phi.model.google import Gemini
from phi.tools.duckduckgo import DuckDuckGo
import google.generativeai as genai
from google.generativeai import upload_file, get_file

# PDF generation library
from fpdf import FPDF

# --------------------------
# Set Page Configuration
# --------------------------
st.set_page_config(
    page_title="QuickSummarizer",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --------------------------
# Load Environment Variables
# --------------------------
load_dotenv()

# --------------------------
# MongoDB Configuration
# --------------------------
MONGODB_URI = "mongodb+srv://nextcrudtodo:varunsingh21@cluster09.8ytep.mongodb.net/?retryWrites=true&w=majority&appName=Cluster09"
client = pymongo.MongoClient(MONGODB_URI, serverSelectionTimeoutMS=10000)
try:
    print(client.server_info())
    print("Connected successfully!")
    db = client["studentshowcase_db"]
except Exception as e:
    print("Unable to connect:", e)
    st.error("Database connection error.")
    st.stop()

# --------------------------
# Cloudinary Configuration
# --------------------------
CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
API_KEY_CLD = os.getenv("CLOUDINARY_API_KEY")
API_SECRET_CLD = os.getenv("CLOUDINARY_API_SECRET")

if not (CLOUD_NAME and API_KEY_CLD and API_SECRET_CLD):
    st.error("Cloudinary configuration variables are missing.")
    st.stop()

cloudinary.config(
    cloud_name=CLOUD_NAME,
    api_key=API_KEY_CLD,
    api_secret=API_SECRET_CLD,
)

# --------------------------
# Google Generative AI Configuration
# --------------------------
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)
else:
    st.warning("GOOGLE_API_KEY not provided. Google Generative AI functionalities may be disabled.")

# --------------------------
# Custom CSS for Modern Design
# --------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500&display=swap');

    body {
        font-family: 'Roboto', sans-serif;
    }

    .main {
        background-color: #f5f5f5;
    }

    .stApp {
        max-width: 1200px;
        margin: 0 auto;
    }

    .stTextArea textarea {
        height: 100px;
        border-radius: 5px;
        border: 1px solid #ccc;
    }

    .stButton>button {
        background-color: #4CAF50;
        color: white;
        padding: 10px 20px;
        font-size: 16px;
        border-radius: 5px;
        border: none;
        transition: all 0.3s ease;
    }

    .stButton>button:hover {
        background-color: #45a049;
    }

    .chat-container {
        display: flex;
        flex-direction: column;
        gap: 10px;
    }

    .chat-message {
        padding: 15px;
        border-radius: 10px;
        max-width: 70%;
    }

    .user-message {
        background-color: #DCF8C6;
        align-self: flex-end;
    }

    .assistant-message {
        background-color: #FFFFFF;
        border: 1px solid #ccc;
        align-self: flex-start;
    }

    .summary-card {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
    
    /* Additional CSS for Food Analysis Feature */
    .food-card {
        background-color: white;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        padding: 20px;
        margin-bottom: 20px;
        transition: transform 0.3s ease;
    }
    
    .food-card:hover {
        transform: translateY(-5px);
    }
    
    .nutrition-stats {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        margin: 15px 0;
    }
    
    .nutrition-stat {
        background-color: #f8f9fa;
        border-radius: 20px;
        padding: 8px 15px;
        font-weight: 500;
    }
    
    .protein { color: #2E7D32; border-left: 4px solid #2E7D32; }
    .carbs { color: #1565C0; border-left: 4px solid #1565C0; }
    .fat { color: #FF8F00; border-left: 4px solid #FF8F00; }
    .calories { color: #C62828; border-left: 4px solid #C62828; }
    
    .health-score {
        display: inline-block;
        padding: 5px 10px;
        border-radius: 15px;
        font-weight: bold;
        margin: 10px 0;
    }
    
    .score-high { background-color: #C8E6C9; color: #2E7D32; }
    .score-medium { background-color: #FFF9C4; color: #F57F17; }
    .score-low { background-color: #FFCDD2; color: #C62828; }
    
    /* Enhance the upload area */
    .uploadArea {
        border: 2px dashed #4CAF50;
        border-radius: 10px;
        padding: 25px;
        text-align: center;
        margin: 20px 0;
        background-color: rgba(76, 175, 80, 0.05);
        transition: all 0.3s ease;
    }
    
    .uploadArea:hover {
        background-color: rgba(76, 175, 80, 0.1);
        border-color: #388E3C;
    }
    
    /* Custom badge styling */
    .badge {
        display: inline-block;
        padding: 3px 10px;
        font-size: 0.8em;
        font-weight: bold;
        border-radius: 12px;
        margin-right: 5px;
    }
    
    .badge-food { background-color: #E3F2FD; color: #1565C0; }
    .badge-video { background-color: #F3E5F5; color: #6A1B9A; }
    .badge-web { background-color: #E8F5E9; color: #2E7D32; }
    .badge-youtube { background-color: #FFEBEE; color: #C62828; }
    .badge-pdf { background-color: #FFF3E0; color: #E65100; }
    </style>
    """, unsafe_allow_html=True
)

# --------------------------
# Initialize Session State
# --------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user" not in st.session_state:
    st.session_state.user = {}
if "current_pdf_id" not in st.session_state:
    st.session_state.current_pdf_id = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# --------------------------
# Authentication & Storage Helpers
# --------------------------
def get_user_by_email(email):
    return db.users.find_one({"email": email})

def create_user(username, email, password, profile_pic_url=None):
    if get_user_by_email(email):
        return None, "A user with that email already exists."
    hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    user = {
        "username": username,
        "email": email,
        "password": hashed_pw,
        "profile_pic_url": profile_pic_url if profile_pic_url else "",
        "created_at": datetime.utcnow()
    }
    result = db.users.insert_one(user)
    user["_id"] = result.inserted_id
    return user, None

def update_profile_pic(user_id, profile_pic_url):
    db.users.update_one({"_id": user_id}, {"$set": {"profile_pic_url": profile_pic_url}})

def save_summary(user_id, summary_type, input_data, result_text):
    doc = {
        "user_id": user_id,
        "type": summary_type,
        "input": input_data,
        "result": result_text,
        "timestamp": datetime.utcnow()
    }
    db.summaries.insert_one(doc)

# --------------------------
# PDF-Related Functions
# --------------------------
def save_pdf_to_db(user_id, pdf_name, pdf_content, pdf_text):
    doc = {
        "user_id": user_id,
        "pdf_name": pdf_name,
        "pdf_content": pdf_content,
        "pdf_text": pdf_text,
        "timestamp": datetime.utcnow()
    }
    return db.pdfs.insert_one(doc)

def get_user_pdfs(user_id):
    return list(db.pdfs.find({"user_id": user_id}))

def save_pdf_chat(user_id, pdf_id, question, answer):
    doc = {
        "user_id": user_id,
        "pdf_id": pdf_id,
        "question": question,
        "answer": answer,
        "timestamp": datetime.utcnow()
    }
    return db.pdf_chats.insert_one(doc)

def get_pdf_chats(pdf_id):
    return list(db.pdf_chats.find({"pdf_id": pdf_id}).sort("timestamp", 1))

def extract_text_from_pdf(pdf_file) -> str:
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        st.error(f"Error extracting text from PDF: {str(e)}")
        return ""

# --------------------------
# Summarization Helpers
# --------------------------
def convert_timestamp_to_seconds(ts):
    parts = ts.split(':')
    parts = [int(p) for p in parts]
    if len(parts) == 2:
        return parts[0] * 60 + parts[1]
    elif len(parts) == 3:
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    return 0

def get_youtube_chapters(url):
    try:
        video = YouTube(url)
        description = video.description
        pattern = re.compile(r'^(\d{1,2}:\d{2}(?::\d{2})?)\s*[-–—>\s]*(.+)$')
        chapters = []
        for line in description.splitlines():
            match = pattern.match(line.strip())
            if match:
                timestamp_str = match.group(1)
                title = match.group(2).strip()
                seconds = convert_timestamp_to_seconds(timestamp_str)
                chapters.append((seconds, title))
        chapters.sort(key=lambda x: x[0])
        if len(chapters) < 2:
            return []
        return chapters
    except Exception:
        return []

def get_youtube_transcript_list(url):
    try:
        video = YouTube(url)
        video_id = video.video_id
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        return transcript_list
    except Exception:
        return None

def join_transcript_entries(entries):
    return " ".join([entry["text"] for entry in entries])

def extract_text_from_url(url):
    try:
        response = requests.get(url)
        if response.status_code != 200:
            return f"Error: Received status code {response.status_code}"
        soup = BeautifulSoup(response.content, 'html.parser')
        for element in soup(["script", "style", "noscript"]):
            element.decompose()
        text = soup.get_text(separator=" ", strip=True)
        return text
    except Exception as e:
        return f"Error extracting text from URL: {str(e)}"

# --------------------------
# PDF Helper Functions
# --------------------------
def create_pdf(title, content):
    class PDF(FPDF):
        def header(self):
            self.set_font("Arial", 'B', 16)
            self.cell(0, 10, self.sanitize_text(title), ln=True, align='C')
            self.ln(10)

        def footer(self):
            self.set_y(-15)
            self.set_font('Arial', 'I', 8)
            self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

        def sanitize_text(self, text):
            replacements = {
                '’': "'",
                '‘': "'",
                '“': '"',
                '”': '"',
                '—': '-',
                '–': '-',
                '…': '...',
                '\u0101': 'a',  # ā
                '\u0113': 'e',  # ē
                '\u012B': 'i',  # ī
                '\u014D': 'o',  # ō
                '\u016B': 'u',  # ū
            }
            for old, new in replacements.items():
                text = text.replace(old, new)
            return ''.join(char for char in text if ord(char) < 256)

        def chapter_body(self, content):
            self.set_font("Arial", size=12)
            paragraphs = content.split('\n')
            for paragraph in paragraphs:
                if paragraph.strip():
                    sanitized_para = self.sanitize_text(paragraph)
                    self.multi_cell(0, 10, sanitized_para)
                    self.ln()

    try:
        pdf = PDF()
        pdf.add_page()
        pdf.chapter_body(content)
        pdf_output = pdf.output(dest='S')
        if isinstance(pdf_output, str):
            pdf_bytes = pdf_output.encode('latin-1')
        elif isinstance(pdf_output, bytearray):
            pdf_bytes = bytes(pdf_output)
        else:
            pdf_bytes = pdf_output
        return pdf_bytes
    except Exception as e:
        st.error(f"Error creating PDF: {str(e)}")
        return None

def sanitize_filename(name):
    name = re.sub(r'[^\w\s-]', '', name)
    name = name.strip().replace(' ', '_')
    return name

# --------------------------
# Delete Summary
# --------------------------
def delete_summary(summary_id):
    try:
        result = db.summaries.delete_one({"_id": summary_id})
        return result.deleted_count > 0
    except Exception as e:
        print(f"Error deleting summary: {e}")
        return False

# --------------------------
# Summarization Agent Initialization
# --------------------------
@st.cache_resource
def initialize_agent():
    return Agent(
        name="QuickSummarizer",
        model=Gemini(id="gemini-2.0-flash-exp"),
        tools=[DuckDuckGo()],
        markdown=True,
    )

multimodal_Agent = initialize_agent()


# --------------------------
# Food Calorie Analysis Tab Function
# --------------------------
def show_food_analysis_tab():
    st.header("🍽️ Food Calorie Analyzer")
    
    st.markdown("""
    Upload a photo of your meal, and our AI will analyze it to:
    - Identify the food items
    - Estimate calories and nutritional content
    - Provide suggestions for healthier alternatives
    - Create a detailed nutritional report
    """)
    
    food_image = st.file_uploader(
        "Upload a food image", 
        type=['jpg', 'jpeg', 'png'],
        help="Upload a clear photo of your meal for the most accurate analysis"
    )
    
    if food_image:
        col1, col2 = st.columns(2)
        
        with col1:
            st.image(food_image, caption="Your food image", use_column_width=True)
        
        with col2:
            st.markdown("### Analysis Options")
            diet_preference = st.selectbox(
                "Your dietary preference",
                ["No specific preference", "Vegetarian", "Vegan", "Keto", "Low-carb", "Mediterranean", "High-protein"]
            )
            
            health_goals = st.multiselect(
                "Your health goals",
                ["Weight loss", "Muscle gain", "Balanced nutrition", "Heart health", "Diabetic-friendly", "Energy boost"]
            )
            
            st.markdown("### Analyze")
            analyze_button = st.button("🔍 Analyze Food Image", key="analyze_food_button")
        
        if analyze_button:
            with st.spinner("🔄 Analyzing your food image..."):
                try:
                    # Process and upload the food image
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_image:
                        temp_image.write(food_image.getbuffer())
                        image_path = temp_image.name
                    
                    # Upload to Cloudinary for a permanent URL (we'll use this URL to save in our DB)
                    upload_result = cloudinary.uploader.upload(image_path)
                    food_image_url = upload_result.get("secure_url", "")
                    
                    # Process with Google Generative AI multimodal model
                    processed_image = upload_file(image_path)
                    while processed_image.state.name == "PROCESSING":
                        time.sleep(1)
                        processed_image = get_file(processed_image.name)
                    
                    # Create prompt based on user preferences
                    health_goals_text = ", ".join(health_goals) if health_goals else "general health"
                    
                    analysis_prompt = f"""
You are a professional nutritionist and food analysis expert. You're examining a photograph of food.

Provide a detailed nutritional analysis of the food in this image, focusing on:

1. Detailed Identification: List all identifiable food items in the image, being as specific as possible.

2. Caloric Analysis:
   - Estimate total calories (provide a range if uncertain)
   - Break down calories by food item if multiple items are present
   - Estimate portion sizes when possible

3. Nutritional Breakdown:
   - Macronutrients (proteins, carbs, fats) - amounts and percentages
   - Estimated fiber content
   - Estimated sugar content
   - Key vitamins and minerals likely present

4. Health Evaluation:
   - Rate this meal's overall nutritional quality on a scale of 1-10
   - Identify positive nutritional aspects
   - Identify nutritional concerns or imbalances
   - Evaluate how well this meal aligns with a {diet_preference} diet
   - Assess how this meal supports these health goals: {health_goals_text}

5. Improvement Recommendations:
   - 3-5 specific, actionable suggestions to improve the nutritional profile
   - Recommended portion adjustments if applicable
   - Healthier alternative ingredients or preparation methods
   - Complementary foods that could balance this meal

6. Summary:
   - Provide a concise 2-3 sentence overall assessment

Format this as a professional nutritional report with clear sections and bullet points where appropriate.
                    """
                    
                    # Run the analysis
                    response = multimodal_Agent.run(analysis_prompt, images=[processed_image])
                    
                    # Clean up the temporary file
                    Path(image_path).unlink(missing_ok=True)
                    
                    # Display the results
                    st.header("🎉 Food Analysis Results")
                    st.markdown(response.content)
                    
                    # Create a PDF report
                    report_title = f"Food Analysis Report - {datetime.now().strftime('%Y-%m-%d')}"
                    pdf_content = f"# {report_title}\n\n{response.content}"
                    pdf_bytes = create_pdf(report_title, response.content)
                    
                    if pdf_bytes:
                        col1, col2 = st.columns(2)
                        with col1:
                            st.download_button(
                                "📥 Download Report as PDF",
                                data=pdf_bytes,
                                file_name="food_analysis_report.pdf",
                                mime="application/pdf"
                            )
                    
                    # Save the summary to the database
                    save_summary(
                        st.session_state.user["_id"],
                        "food_analysis",
                        food_image_url,  # Store the Cloudinary URL instead of the raw file
                        response.content
                    )
                    
                    # Show a tracking suggestion
                    st.info("""
                    💡 **Tip:** This report has been saved to your profile. You can access it anytime to track your eating habits and nutritional progress!
                    """)
                    
                except Exception as error:
                    st.error(f"😕 An error occurred during food analysis: {error}")
            
    else:
        # Show sample analysis with example image if no image is uploaded
        st.info("👆 Upload a food image to begin analysis, or see a sample report below.")
        
        with st.expander("See a sample food analysis report"):
            st.image("assets\sample_food\meal.jpg", caption="Sample food image")
            st.markdown("""
            ## Sample Food Analysis Report
            
            ### 🍽️ Food Identification
            - Hard-boiled eggs (3, cut in half)
            - Whole wheat toast (2 slices)
            - Sliced banana (on toast)
            - Sliced kiwi (2 slices)

            
            ### 📊 Caloric Analysis
            - **Total calories**: 400-550 kcal
              - Eggs: 210 kcal (3 eggs x 70 kcal/egg)
              - Toast: 140 kcal (2 slices x 70 kcal/slice)
              - Banana: 105 kcal (1 medium banana)
              - Kiwi: 90 kcal (2 medium kiwi)
            - Portion Sizes: Assumed based on common sizes. Adjustments may be needed.
            
            ### 🔍 Nutritional Breakdown
            - **Macronutrients**:
              - Protein: 23g (27%)
              - Carbohydrates: 54g (52%)
              - Fat: 25g (21%)
              - Fiber: Estimated 12-15g
              - Sugar: Estimated 24g (mostly from banana and kiwi)
            
            *This is just a sample report. Upload your own food image for a personalized analysis.*
            """)
            
            

# --------------------------
# PDF Chat Tab Function
# --------------------------
def show_pdf_chat_tab():
    st.header("📚 Chat with PDF")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        pdf_file = st.file_uploader(
            "Upload a new PDF file", 
            type=['pdf'],
            help="Upload a PDF document to chat with"
        )
    
    with col2:
        user_pdfs = get_user_pdfs(st.session_state.user["_id"])
        if user_pdfs:
            pdf_names = ["Select a PDF..."] + [pdf["pdf_name"] for pdf in user_pdfs]
            selected_pdf = st.selectbox("Or select an existing PDF", pdf_names)
            if selected_pdf != "Select a PDF...":
                selected_pdf_doc = next((pdf for pdf in user_pdfs if pdf["pdf_name"] == selected_pdf), None)
                if selected_pdf_doc:
                    st.session_state.current_pdf_id = selected_pdf_doc["_id"]
    
    if pdf_file:
        with st.spinner("Processing new PDF..."):
            pdf_text = extract_text_from_pdf(pdf_file)
            if pdf_text:
                pdf_content = pdf_file.getvalue()
                db_result = save_pdf_to_db(
                    st.session_state.user["_id"],
                    pdf_file.name,
                    pdf_content,
                    pdf_text
                )
                st.session_state.current_pdf_id = db_result.inserted_id
                st.success("PDF processed successfully!")
                st.rerun()
    
    if st.session_state.current_pdf_id:
        st.subheader("Chat with your PDF")
        
        chat_container = st.container()
        
        with chat_container:
            chat_history = get_pdf_chats(st.session_state.current_pdf_id)
            for chat in chat_history:
                st.markdown(
                    f"""<div class="chat-message user-message">
                        <strong>You:</strong><br>{chat['question']}
                    </div>""",
                    unsafe_allow_html=True
                )
                st.markdown(
                    f"""<div class="chat-message assistant-message">
                        <strong>Assistant:</strong><br>{chat['answer']}
                    </div>""",
                    unsafe_allow_html=True
                )
        
        st.markdown("---")
        user_question = st.text_area(
            "Ask a question about your PDF:",
            placeholder="E.g., 'What is the main topic?', 'Summarize section 2', 'Explain the concept on page 5'",
            height=100,
            key="pdf_chat_input"
        )
        
        if st.button("Send", key="send_pdf_question"):
            if user_question:
                with st.spinner("Generating response..."):
                    pdf_doc = db.pdfs.find_one({"_id": st.session_state.current_pdf_id})
                    pdf_text = pdf_doc["pdf_text"]
                    
                    chat_prompt = f"""
Based on the following PDF content, please answer this question:
{user_question}

Relevant PDF content:
{pdf_text[:5000]}

Please provide a detailed and accurate response based solely on the information contained in the PDF. If applicable, reference specific sections or pages from the PDF in your response.
                    """
                    
                    response = multimodal_Agent.run(chat_prompt)
                    
                    save_pdf_chat(
                        st.session_state.user["_id"],
                        st.session_state.current_pdf_id,
                        user_question,
                        response.content
                    )
                    
                    st.rerun()
    
    else:
        st.info("👆 Upload a new PDF or select an existing one to start chatting!")

# --------------------------
# Main App
# --------------------------
def main_app():
    nav = st.sidebar.radio("Navigation", ["Summarize", "Profile", "Logout"])
    
    if nav == "Logout":
        st.session_state.logged_in = False
        st.session_state.user = {}
        st.success("You have been logged out.")
        st.rerun()
    
    elif nav == "Summarize":
        st.title("🔥 QuickSummarizer")
        st.markdown(
            """
            Welcome to the QuickSummarizer! Choose one of the options below to analyze your content:
            - Project Videos
            - Web Pages
            - YouTube Videos
            - PDF Documents
            - Food Calorie Analysis
            """
        )
        
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📹 Video Upload",
            "🌐 Web Page",
            "🎥 YouTube Video",
            "📚 Chat with PDF",
            "🍽️ Food Analysis"
        ])
        
        
        with tab1:
            st.header("📤 Upload Your Project Video")
            video_file = st.file_uploader(
                "Choose a video file", 
                type=['mp4', 'mov', 'avi'], 
                help="Upload your project video for AI analysis (Max 200MB)"
            )
            if video_file:
                st.video(video_file)
                user_query = st.text_area(
                    "What would you like to know about your project video?",
                    placeholder="E.g., 'Summarize the main points of my presentation', 'How can I improve my delivery?', 'What are the strengths and weaknesses of my project?'"
                )
                if st.button("🚀 Analyze Video", key="analyze_video_button"):
                    if not user_query:
                        st.warning("⚠️ Please enter a question or request for analysis.")
                    else:
                        try:
                            with st.spinner("🔄 Processing your video and gathering insights..."):
                                with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_video:
                                    temp_video.write(video_file.getbuffer())
                                    video_path = temp_video.name

                                processed_video = upload_file(video_path)
                                while processed_video.state.name == "PROCESSING":
                                    time.sleep(1)
                                    processed_video = get_file(processed_video.name)

                                analysis_prompt = f"""
Analyze the uploaded student project video for content and presentation in detail.
Focus on the following aspects:
1. Main points and key ideas presented.
2. Clarity and effectiveness of communication.
3. Use and impact of visual aids.
4. Specific areas for improvement.
5. Overall impression and potential impact.

Then, address the student's specific query:
{user_query}

Provide a detailed, constructive, and actionable response that is encouraging and highlights both strengths and areas for improvement.
                                """
                                response = multimodal_Agent.run(analysis_prompt, videos=[processed_video])
                            
                            st.header("🎉 Analysis Results")
                            st.markdown(response.content)
                            st.subheader("📌 Tips for Improvement")
                            st.info(
                                """
- Review the analysis and focus on key areas for improvement.
- Practice your presentation to enhance clarity and confidence.
- Consider peer reviews to get different perspectives.
- Don't hesitate to re-upload improved versions for further analysis!
                                """
                            )
                            save_summary(
                                st.session_state.user["_id"],
                                "video",
                                "Uploaded video",
                                response.content
                            )
                        except Exception as error:
                            st.error(f"😕 An error occurred during analysis: {error}")
                        finally:
                            Path(video_path).unlink(missing_ok=True)
            else:
                st.info("👆 Upload your project video to begin the analysis.")

        with tab2:
            st.header("🌐 Summarize Web Page")
            st.markdown("Enter the URL of a web page to get a comprehensive summary, including the main topic, key points, significant data, and conclusions.")
            web_url = st.text_input("Web Page URL:")
            if st.button("🔍 Summarize Web Page", key="summarize_web_button"):
                if not web_url:
                    st.warning("⚠️ Please enter a valid URL.")
                else:
                    try:
                        with st.spinner("🔄 Extracting content and summarizing..."):
                            web_content = extract_text_from_url(web_url)
                            if not web_content or web_content.startswith("Error"):
                                st.error(f"😕 Unable to extract content from the URL. Details: {web_content}")
                            else:
                                summary_prompt = f"""
Please generate a detailed and structured summary of the following web page content:
{web_content[:5000]}

Your summary should include:
1. The main topic or purpose of the page.
2. Detailed key points and arguments presented.
3. Any significant data, statistics, or examples mentioned.
4. A conclusion or call to action (if applicable).

Provide the summary in a clear and comprehensive manner, aiming for conciseness while capturing the essence of the page.
                                """
                                response = multimodal_Agent.run(summary_prompt)
                                st.header("🎉 Web Page Summary")
                                st.markdown(response.content)
                                save_summary(
                                    st.session_state.user["_id"],
                                    "web",
                                    web_url,
                                    response.content
                                )
                    except Exception as error:
                        st.error(f"😕 An error occurred during web page summarization: {error}")

        with tab3:
            st.header("🎥 Summarize YouTube Video")
            st.markdown("Enter a YouTube video URL to generate detailed study notes. If the video has chapters, you'll receive notes for each chapter; otherwise, you'll get comprehensive notes for the entire video.")
            youtube_url = st.text_input("YouTube Video URL:")
            if st.button("🔍 Summarize YouTube Video", key="summarize_youtube_button"):
                if not youtube_url:
                    st.warning("⚠️ Please enter a valid YouTube URL.")
                else:
                    try:
                        with st.spinner("🔄 Extracting transcript and chapters..."):
                            transcript_list = get_youtube_transcript_list(youtube_url)
                            if not transcript_list:
                                st.error("😕 Unable to extract transcript for the video.")
                            else:
                                chapters = get_youtube_chapters(youtube_url)
                                if chapters:
                                    chapter_summaries = []
                                    end_time = transcript_list[-1]["start"] + transcript_list[-1]["duration"]
                                    chapters_with_end = []
                                    for idx, (start, title) in enumerate(chapters):
                                        next_start = chapters[idx+1][0] if idx+1 < len(chapters) else end_time
                                        chapters_with_end.append((start, next_start, title))
                                    for start, end, title in chapters_with_end:
                                        chapter_entries = [entry for entry in transcript_list if start <= entry["start"] < end]
                                        if chapter_entries:
                                            chapter_text = join_transcript_entries(chapter_entries)
                                            chapter_prompt = f"""
Please generate detailed, note-style study notes for the chapter titled "{title}".
The notes should include:
- Key concepts and topics covered in this chapter.
- Main learning points and insights.
- Detailed explanations and examples provided.
- Any actionable lessons or conclusions.

Structure the notes with bullet points or numbered lists where appropriate for easy studying.

Here is the transcript excerpt for this chapter:
{chapter_text[:5000]}
                                            """
                                            chapter_response = multimodal_Agent.run(chapter_prompt)
                                            chapter_summaries.append((title, chapter_response.content))
                                    st.header("🎉 YouTube Video Chapter Summaries")
                                    summary_combined = ""
                                    for title, summary in chapter_summaries:
                                        st.subheader(f"Chapter: {title}")
                                        st.markdown(summary)
                                        summary_combined += f"Chapter: {title}\n{summary}\n\n"
                                    pdf_bytes = create_pdf("YouTube Video Summary", summary_combined)
                                    if pdf_bytes:
                                        st.download_button(
                                            "📥 Download Notes as PDF",
                                            data=pdf_bytes,
                                            file_name="youtube_notes.pdf",
                                            mime="application/pdf"
                                        )
                                    save_summary(
                                        st.session_state.user["_id"],
                                        "youtube",
                                        youtube_url,
                                        summary_combined
                                    )
                                else:
                                    full_transcript = join_transcript_entries(transcript_list)
                                    summary_prompt = f"""
Please generate detailed note-style study notes from the following YouTube video transcript.
The notes should include:
- Key concepts and topics covered in the video.
- Main learning points and insights.
- Detailed explanations, examples, and actionable lessons.
- A summary of all topics discussed.

Structure the notes with bullet points or numbered lists where appropriate for easy studying.

Transcript (first 5000 characters):
{full_transcript[:5000]}
                                    """
                                    response = multimodal_Agent.run(summary_prompt)
                                    st.header("🎉 YouTube Video Detailed Notes")
                                    st.markdown(response.content)
                                    pdf_bytes = create_pdf("YouTube Video Summary", response.content)
                                    if pdf_bytes:
                                        st.download_button(
                                            "📥 Download Notes as PDF",
                                            data=pdf_bytes,
                                            file_name="youtube_notes.pdf",
                                            mime="application/pdf"
                                        )
                                    save_summary(
                                        st.session_state.user["_id"],
                                        "youtube",
                                        youtube_url,
                                        response.content
                                    )
                            video_id = YouTube(youtube_url).video_id
                            st.video(f"https://www.youtube.com/watch?v={video_id}")
                    except Exception as error:
                        st.error(f"😕 An error occurred during YouTube video summarization: {error}")

        with tab4:
            show_pdf_chat_tab()
        with tab5:
            # New Food Analysis Tab
            show_food_analysis_tab()
    
    elif nav == "Profile":
        # Enhanced Profile Page with Food Analysis Reports
        st.title("👤 Your Profile")
        user = st.session_state.user

        if user.get("profile_pic_url"):
            st.image(user["profile_pic_url"], width=150)
        else:
            st.image("https://via.placeholder.com/150", width=150)
        st.write(f"**Username:** {user.get('username','')}")
        st.write(f"**Email:** {user.get('email','')}")

        st.markdown("---")
        st.subheader("Update Profile Picture")
        new_profile_pic = st.file_uploader("Upload a new profile picture", type=["png", "jpg", "jpeg"], key="update_profile_pic")
        if st.button("Update Picture"):
            if new_profile_pic:
                try:
                    upload_result = cloudinary.uploader.upload(new_profile_pic)
                    new_pic_url = upload_result.get("secure_url", "")
                    update_profile_pic(user["_id"], new_pic_url)
                    st.session_state.user["profile_pic_url"] = new_pic_url
                    st.success("Profile picture updated!")
                except Exception as e:
                    st.error(f"Failed to update profile picture: {e}")
            else:
                st.error("Please select a picture to upload.")

        st.markdown("---")
        st.subheader("Your Past Summarizations & Analysis Reports")
        
        # Add filters for the summaries
        filter_options = ["All", "Video", "Web", "YouTube", "PDF Chat", "Food Analysis"]
        selected_filter = st.selectbox("Filter by type:", filter_options)
        
        # Query based on filter
        if selected_filter == "All":
            summaries = list(db.summaries.find({"user_id": user["_id"]}).sort("timestamp", -1))
        else:
            filter_value = selected_filter.lower().replace(" ", "_")
            summaries = list(db.summaries.find({"user_id": user["_id"], "type": filter_value}).sort("timestamp", -1))
        
        if summaries:
            for idx, summ in enumerate(summaries):
                summary_key = f"summary_{idx}_{summ['_id']}"
                with st.container():
                    st.markdown(f'<div class="summary-card">', unsafe_allow_html=True)
                    
                    # Add a special display for food analysis reports
                    if summ['type'] == 'food_analysis':
                        col1, col2, col3 = st.columns([2, 3, 1])
                        with col1:
                            # Display the food image from cloudinary URL
                            st.image(summ['input'], width=200)
                        with col2:
                            st.markdown(f"**Type:** Food Analysis | **Date:** {summ['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
                            # Extract and display calorie information if present
                            calorie_match = re.search(r'Total calories:\s*(\d+[-~]\d+)', summ['result'])
                            if calorie_match:
                                st.markdown(f"**Calories:** {calorie_match.group(1)}")
                            else:
                                st.markdown("**Food Analysis Report**")
                        with col3:
                            if st.button("🗑️ Delete", key=f"delete_btn_{summary_key}"):
                                st.warning("Are you sure you want to delete this summary?")
                                delete_col1, delete_col2 = st.columns(2)
                                with delete_col1:
                                    if st.button("✔️ Yes", key=f"confirm_delete_{summary_key}"):
                                        if delete_summary(summ['_id']):
                                            st.success("Summary deleted successfully!")
                                            st.rerun()
                                        else:
                                            st.error("Failed to delete summary. Please try again.")
                                with delete_col2:
                                    if st.button("❌ No", key=f"cancel_delete_{summary_key}"):
                                        st.rerun()
                    else:
                        # Regular display for other types of summaries
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.markdown(f"**Type:** {summ['type'].capitalize().replace('_', ' ')} | **On:** {summ['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
                            st.markdown(f"**Input:** {summ['input'] if not summ['input'].startswith('http') else f'[Link]({summ['input']})'}")
                        with col2:
                            if st.button("🗑️ Delete", key=f"delete_btn_{summary_key}"):
                                st.warning("Are you sure you want to delete this summary?")
                                delete_col1, delete_col2 = st.columns(2)
                                with delete_col1:
                                    if st.button("✔️ Yes", key=f"confirm_delete_{summary_key}"):
                                        if delete_summary(summ['_id']):
                                            st.success("Summary deleted successfully!")
                                            st.rerun()
                                        else:
                                            st.error("Failed to delete summary. Please try again.")
                                with delete_col2:
                                    if st.button("❌ No", key=f"cancel_delete_{summary_key}"):
                                        st.rerun()
                    
                    with st.expander("View Full Report"):
                        st.markdown(summ['result'])
                    
                    pdf_bytes = create_pdf(
                        f"{summ['type'].capitalize().replace('_', ' ')} Report",
                        summ['result']
                    )
                    if pdf_bytes:
                        filename = f"{sanitize_filename(summ['type'])}_{summ['timestamp'].strftime('%Y%m%d')}.pdf"
                        st.download_button(
                            "📥 Download PDF Report",
                            data=pdf_bytes,
                            file_name=filename,
                            mime="application/pdf",
                            key=f"download_btn_{summary_key}"
                        )
                    st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("No reports found with the selected filter.")
            
       

# --------------------------
# Authentication Forms
# --------------------------
def show_auth():
    st.title("🔥 QuickSummarizer")
    st.subheader("Login or Sign Up to Continue")
    tabs = st.tabs(["Login", "Sign Up"])

    with tabs[0]:
        st.subheader("Login")
        login_email = st.text_input("Email", key="login_email", placeholder="Enter your email")
        login_password = st.text_input("Password", type="password", key="login_password", placeholder="Enter your password")
        if st.button("Login"):
            user = get_user_by_email(login_email)
            if user and bcrypt.checkpw(login_password.encode(), user["password"].encode()):
                st.session_state.logged_in = True
                st.session_state.user = user
                st.success("Logged in successfully!")
            else:
                st.error("Invalid credentials. Please try again.")

    with tabs[1]:
        st.subheader("Sign Up")
        signup_username = st.text_input("Username", key="signup_username", placeholder="Choose a username")
        signup_email = st.text_input("Email", key="signup_email", placeholder="Enter your email")
        signup_password = st.text_input("Password", type="password", key="signup_password", placeholder="Choose a password")
        signup_confirm_password = st.text_input("Confirm Password", type="password", key="signup_confirm_password", placeholder="Confirm your password")
        profile_pic = st.file_uploader("Upload Profile Picture (optional)", type=["png", "jpg", "jpeg"], key="signup_profile_pic")
        if st.button("Sign Up"):
            if signup_password != signup_confirm_password:
                st.error("Passwords do not match.")
            else:
                profile_pic_url = ""
                if profile_pic:
                    try:
                        upload_result = cloudinary.uploader.upload(profile_pic)
                        profile_pic_url = upload_result.get("secure_url", "")
                    except Exception as e:
                        st.error(f"Profile picture upload failed: {e}")
                user, error = create_user(signup_username, signup_email, signup_password, profile_pic_url)
                if error:
                    st.error(error)
                else:
                    st.session_state.logged_in = True
                    st.session_state.user = user
                    st.success("Signed up successfully!")

# --------------------------
# Main Entry Point
# --------------------------
if st.session_state.logged_in:
    main_app()
else:
    show_auth()

# --------------------------
# Footer
# --------------------------
st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; font-family: 'Roboto', sans-serif; color: #333;">
        <h4>QuickSummarizer</h4>
        <p>Powered by <strong>Gemini 2.0 Flash Exp</strong> | Developed for students</p>
        <p>
            Made by 
            <a href="https://github.com/VarunSingh19" target="_blank" style="color: #4CAF50;">
                <img src="https://img.icons8.com/ios-glyphs/30/4CAF50/github.png" style="vertical-align: middle; margin-right: 8px;"/>
                VarunSingh19
            </a>
        </p>
    </div>
    """, unsafe_allow_html=True
)
