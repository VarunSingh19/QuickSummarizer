
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
# Set page configuration
# --------------------------
st.set_page_config(
    page_title="QuickSummarizer",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --------------------------
# Load environment variables
# --------------------------
load_dotenv()

# --------------------------
# MongoDB Configuration (Remote Atlas)
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
# Google Generative AI API Key Configuration
# --------------------------
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)
else:
    st.warning("GOOGLE_API_KEY not provided. Google Generative AI functionalities may be disabled.")

# --------------------------
# Custom CSS Injection
# --------------------------
st.markdown(
    """
    <style>
    .main { background-color: #f0f2f6; }
    .stApp { max-width: 1200px; margin: 0 auto; }
    .stTextArea textarea { height: 100px; }
    .stButton>button {
        background-color: #4CAF50; color: white; padding: 10px 20px;
        font-size: 16px; border-radius: 5px; border: none; transition: all 0.3s ease;
    }
    .stButton>button:hover { background-color: #45a049; }
    .chat-message {
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        display: flex;
        flex-direction: column;
    }
    .user-message {
        background-color: #e3f2fd;
    }
    .assistant-message {
        background-color: #f5f5f5;
    }
    </style>
    """, unsafe_allow_html=True
)

# --------------------------
# Initialize Session State Keys
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
# Helper Functions for Authentication & Storage
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
# PDF Related Functions
# --------------------------
def save_pdf_to_db(user_id, pdf_name, pdf_content, pdf_text):
    """Save PDF and its extracted text to database"""
    doc = {
        "user_id": user_id,
        "pdf_name": pdf_name,
        "pdf_content": pdf_content,
        "pdf_text": pdf_text,
        "timestamp": datetime.utcnow()
    }
    return db.pdfs.insert_one(doc)

def get_user_pdfs(user_id):
    """Get all PDFs for a user"""
    return list(db.pdfs.find({"user_id": user_id}))

def save_pdf_chat(user_id, pdf_id, question, answer):
    """Save chat history to database"""
    doc = {
        "user_id": user_id,
        "pdf_id": pdf_id,
        "question": question,
        "answer": answer,
        "timestamp": datetime.utcnow()
    }
    return db.pdf_chats.insert_one(doc)

def get_pdf_chats(pdf_id):
    """Get chat history for a specific PDF"""
    return list(db.pdf_chats.find({"pdf_id": pdf_id}).sort("timestamp", 1))

def extract_text_from_pdf(pdf_file) -> str:
    """Extract text from uploaded PDF file"""
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        st.error(f"Error extracting text from PDF: {str(e)}")
        return ""

def process_pdf_for_chat(pdf_text: str, chunk_size: int = 1000) -> List[str]:
    """Split PDF text into chunks of approximately `chunk_size` words."""
    words = pdf_text.split()
    chunks = []
    for i in range(0, len(words), chunk_size):
        chunk = " ".join(words[i:i+chunk_size])
        chunks.append(chunk)
    return chunks




# --------------------------
# Summarization Helper Functions
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
# The create_pdf function remains the same
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
            # Replace problematic characters with their closest ASCII equivalents
            replacements = {
                ''': "'",
                ''': "'",
                '"': '"',
                '"': '"',
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
            # Remove any remaining non-Latin1 characters
            return ''.join(char for char in text if ord(char) < 256)

        def chapter_body(self, content):
            self.set_font("Arial", size=12)
            # Split content into paragraphs and process each
            paragraphs = content.split('\n')
            for paragraph in paragraphs:
                if paragraph.strip():  # Skip empty paragraphs
                    sanitized_para = self.sanitize_text(paragraph)
                    self.multi_cell(0, 10, sanitized_para)
                    self.ln()

    try:
        # Create PDF instance
        pdf = PDF()
        pdf.add_page()
        pdf.chapter_body(content)
        
        # Get the PDF as bytes
        pdf_output = pdf.output(dest='S')
        
        # Convert to bytes if necessary
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
    # Remove characters that are not alphanumeric, spaces, hyphens, or underscores
    name = re.sub(r'[^\w\s-]', '', name)
    name = name.strip().replace(' ', '_')
    return name



# --------------------------
# Delete Summary 
# --------------------------
def delete_summary(summary_id):
    """Delete a specific summary from the database"""
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

# [Previous helper functions remain the same...]

# --------------------------
# PDF Chat Tab Function
# --------------------------
def show_pdf_chat_tab():
    st.header("📚 Chat with PDF")
    
    # Create columns for upload and PDF selection
    col1, col2 = st.columns([1, 1])
    
    with col1:
        pdf_file = st.file_uploader(
            "Upload a new PDF file", 
            type=['pdf'],
            help="Upload a PDF document to chat with"
        )
    
    with col2:
        # Show existing PDFs
        user_pdfs = get_user_pdfs(st.session_state.user["_id"])
        if user_pdfs:
            pdf_names = ["Select a PDF..."] + [pdf["pdf_name"] for pdf in user_pdfs]
            selected_pdf = st.selectbox("Or select an existing PDF", pdf_names)
            if selected_pdf != "Select a PDF...":
                selected_pdf_doc = next((pdf for pdf in user_pdfs if pdf["pdf_name"] == selected_pdf), None)
                if selected_pdf_doc:
                    st.session_state.current_pdf_id = selected_pdf_doc["_id"]
    
    # Process new PDF upload
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
                st.rerun()  # Refresh to show the new PDF in the selection
    
    # Chat interface
    if st.session_state.current_pdf_id:
        st.subheader("Chat with your PDF")
        
        # Create a chat message container
        chat_container = st.container()
        
        # Display chat history
        with chat_container:
            chat_history = get_pdf_chats(st.session_state.current_pdf_id)
            for chat in chat_history:
                with st.container():
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
        
        # Chat input area
        st.markdown("---")
        user_question = st.text_area(
            "Ask a question about your PDF:",
            height=100,
            key="pdf_chat_input"
        )
        
        if st.button("Send", key="send_pdf_question"):
            if user_question:
                with st.spinner("Generating response..."):
                    # Get the PDF text from database
                    pdf_doc = db.pdfs.find_one({"_id": st.session_state.current_pdf_id})
                    pdf_text = pdf_doc["pdf_text"]
                    
                    # Create the prompt for the AI
                    chat_prompt = f"""
Based on the following PDF content, please answer this question:
{user_question}

Relevant PDF content:
{pdf_text[:5000]}

Please provide a detailed and accurate response based solely on the information contained in the PDF.
                    """
                    
                    # Get response from AI
                    response = multimodal_Agent.run(chat_prompt)
                    
                    # Save the chat to database
                    save_pdf_chat(
                        st.session_state.user["_id"],
                        st.session_state.current_pdf_id,
                        user_question,
                        response.content
                    )
                    
                    # Refresh the page to show new message
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
            """
        )
        
        # Create tabs including the new PDF chat tab
        tab1, tab2, tab3, tab4 = st.tabs([
            "📹 Video Upload",
            "🌐 Web Page",
            "🎥 YouTube Video",
            "📚 Chat with PDF"
        ])
        
         # --- Tab 1: Video Upload ---
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
                    placeholder="E.g., Summarize the main points, suggest improvements, analyze presentation style..."
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

Provide a detailed, constructive, and actionable response.
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

        # --- Tab 2: Web Page Summarization ---
        with tab2:
            st.header("🌐 Summarize Web Page")
            web_url = st.text_input("Enter the URL of the web page you want to summarize:")
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

Provide the summary in a clear and comprehensive manner.
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

        # --- Tab 3: YouTube Video Summarization ---
        with tab3:
            st.header("🎥 Summarize YouTube Video")
            youtube_url = st.text_input("Enter the URL of the YouTube video you want to summarize:")
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

Here is the transcript excerpt for this chapter:
{chapter_text[:5000]}

Provide the notes in a clear, organized, and concise manner.
                                            """
                                            chapter_response = multimodal_Agent.run(chapter_prompt)
                                            chapter_summaries.append((title, chapter_response.content))
                                    st.header("🎉 YouTube Video Chapter Summaries")
                                    summary_combined = ""
                                    for title, summary in chapter_summaries:
                                        st.subheader(f"Chapter: {title}")
                                        st.markdown(summary)
                                        summary_combined += f"Chapter: {title}\n{summary}\n\n"
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

Transcript (first 5000 characters):
{full_transcript[:5000]}

Provide the notes in a clear, organized, and concise manner.
                                    """
                                    response = multimodal_Agent.run(summary_prompt)
                                    st.header("🎉 YouTube Video Detailed Notes")
                                    st.markdown(response.content)
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
    
    elif nav == "Profile":
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
        st.subheader("Your Past Summarizations")
        summaries = list(db.summaries.find({"user_id": user["_id"]}).sort("timestamp", -1))
        if summaries:
            for idx, summ in enumerate(summaries):
                # Create a unique key for this summary's container
                summary_key = f"summary_{idx}_{summ['_id']}"
                
                # Create two columns for the summary header: one for info, one for buttons
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"**Type:** {summ['type'].capitalize()} | **On:** {summ['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
                    st.markdown(f"**Input:** {summ['input']}")
                
                with col2:
                    # Create a container for buttons to keep them aligned
                    button_container = st.container()
                    with button_container:
                        # Delete button with confirmation
                        if st.button("🗑️ Delete", key=f"delete_btn_{summary_key}"):
                            st.warning("Are you sure you want to delete this summary?")
                            col3, col4 = st.columns(2)
                            with col3:
                                if st.button("✔️ Yes", key=f"confirm_delete_{summary_key}"):
                                    if delete_summary(summ['_id']):
                                        st.success("Summary deleted successfully!")
                                        st.rerun()  # Refresh the page to show updated list
                                    else:
                                        st.error("Failed to delete summary. Please try again.")
                            with col4:
                                if st.button("❌ No", key=f"cancel_delete_{summary_key}"):
                                    st.rerun()  # Refresh the page to remove confirmation dialog

                # Show the summary content in an expander
                with st.expander("View Summary"):
                    st.markdown(summ['result'])
                
                # Create a PDF download button for the summary with unique key
                title = summ['input']
                pdf_bytes = create_pdf(title, summ['result'])
                if pdf_bytes is not None:  # Only create download button if PDF generation was successful
                    try:
                        filename = f"{sanitize_filename(title)}.pdf"
                        st.download_button(
                            "📥 Download PDF",
                            data=pdf_bytes,
                            file_name=filename,
                            mime="application/pdf",
                            key=f"download_btn_{summary_key}"
                        )
                    except Exception as e:
                        st.error(f"Error creating download button: {str(e)}")


# --------------------------
# Authentication Forms
# --------------------------
def show_auth():
    st.title("🔥 QuickSummarizer")
    st.subheader("Login or Sign Up to Continue")
    tabs = st.tabs(["Login", "Sign Up"])

    with tabs[0]:
        st.subheader("Login")
        login_email = st.text_input("Email", key="login_email")
        login_password = st.text_input("Password", type="password", key="login_password")
        if st.button("Login"):
            user = get_user_by_email(login_email)
            if user and bcrypt.checkpw(login_password.encode(), user["password"].encode()):
                st.session_state.logged_in = True
                st.session_state.user = user
                st.success("Logged in successfully!")
                # (The next run will show the main app)
            else:
                st.error("Invalid credentials. Please try again.")

    with tabs[1]:
        st.subheader("Sign Up")
        signup_username = st.text_input("Username", key="signup_username")
        signup_email = st.text_input("Email", key="signup_email")
        signup_password = st.text_input("Password", type="password", key="signup_password")
        signup_confirm_password = st.text_input("Confirm Password", type="password", key="signup_confirm_password")
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
                    # (The next run will show the main app)

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
    <div style="text-align: center; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; color: white;">
        <h4>QuickSummarizer</h4>
        <p>Powered by <strong>Gemini 2.0 Flash Exp</strong> | Developed for students</p>
        <p>
            Made by 
            <a href="https://github.com/VarunSingh19" target="_blank" style="color: white;">
                <img src="https://img.icons8.com/ios-glyphs/30/ffffff/github.png" style="vertical-align: middle; margin-right: 8px;"/>
                VarunSingh19
            </a>
        </p>
    </div>
    """, unsafe_allow_html=True
)
