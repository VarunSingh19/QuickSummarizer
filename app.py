# import streamlit as st
# from phi.agent import Agent
# from phi.model.google import Gemini
# from phi.tools.duckduckgo import DuckDuckGo
# from google.generativeai import upload_file, get_file
# import google.generativeai as genai
# import time
# from pathlib import Path
# import tempfile
# from dotenv import load_dotenv
# import os
# import requests
# from bs4 import BeautifulSoup
# from pytube import YouTube
# import re
# from youtube_transcript_api import YouTubeTranscriptApi

# # --------------------------------------------------
# #                CHAPTER HANDLING
# # --------------------------------------------------

# def convert_timestamp_to_seconds(ts):
#     """
#     Converts a timestamp string (e.g., 0:00 or 0:00:00) into seconds.
#     Supports H:MM or H:MM:SS (with optional leading zeros).
#     """
#     parts = ts.split(':')
#     parts = [int(p) for p in parts]
#     if len(parts) == 2:
#         return parts[0] * 60 + parts[1]
#     elif len(parts) == 3:
#         return parts[0] * 3600 + parts[1] * 60 + parts[2]
#     return 0

# def get_youtube_chapters(url):
#     """
#     Extracts chapter markers from the YouTube video's description using a flexible regex.
#     Returns a sorted list of tuples: (start_time_in_seconds, chapter_title).
#     Only returns chapters if at least 2 are found.
#     """
#     try:
#         video = YouTube(url)
#         description = video.description
        
#         # Pattern explanation:
#         # 1) ^(\d{1,2}:\d{2}(?::\d{2})?)  -> Captures timestamps like 0:00, 00:02, 1:05:23, etc.
#         # 2) \s*[-–—>\s]*                -> Zero or more spaces, optional dash/em-dash/arrow/spaces
#         # 3) (.+)$                       -> Capture the rest of the line as the title
#         pattern = re.compile(r'^(\d{1,2}:\d{2}(?::\d{2})?)\s*[-–—>\s]*(.+)$')
        
#         chapters = []
#         for line in description.splitlines():
#             match = pattern.match(line.strip())
#             if match:
#                 timestamp_str = match.group(1)
#                 title = match.group(2).strip()
#                 seconds = convert_timestamp_to_seconds(timestamp_str)
#                 chapters.append((seconds, title))
        
#         chapters.sort(key=lambda x: x[0])
        
#         # Only return them if at least two are found
#         if len(chapters) < 2:
#             return []
#         return chapters
#     except Exception as e:
#         return []

# def get_youtube_transcript_list(url):
#     """
#     Returns the transcript list (each entry is a dict with keys: 'text', 'start', 'duration')
#     using youtube_transcript_api. Returns None if not available.
#     """
#     try:
#         video = YouTube(url)
#         video_id = video.video_id
#         transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
#         return transcript_list
#     except Exception:
#         return None

# def join_transcript_entries(entries):
#     """Joins a list of transcript entries into a single string."""
#     return " ".join([entry["text"] for entry in entries])

# # --------------------------------------------------
# #           WEB PAGE TEXT EXTRACTION
# # --------------------------------------------------

# def extract_text_from_url(url):
#     """
#     Fetches and returns the visible text from a web page at the given URL.
#     """
#     try:
#         response = requests.get(url)
#         if response.status_code != 200:
#             return f"Error: Received status code {response.status_code}"
#         soup = BeautifulSoup(response.content, 'html.parser')
#         # Remove script, style, and noscript elements
#         for element in soup(["script", "style", "noscript"]):
#             element.decompose()
#         text = soup.get_text(separator=" ", strip=True)
#         return text
#     except Exception as e:
#         return f"Error extracting text from URL: {str(e)}"

# # --------------------------------------------------
# #           STREAMLIT AND AGENT SETUP
# # --------------------------------------------------

# load_dotenv()
# API_KEY = os.getenv("GOOGLE_API_KEY")
# if API_KEY:
#     genai.configure(api_key=API_KEY)

# st.set_page_config(
#     page_title="StudentShowcase Content Summarizer",
#     page_icon="🎓",
#     layout="wide"
# )

# # Custom CSS
# st.markdown("""
#     <style>
#     .main { background-color: #f0f2f6; }
#     .stApp { max-width: 1200px; margin: 0 auto; }
#     .stTextArea textarea { height: 100px; }
#     .stButton>button {
#         background-color: #4CAF50; color: white; padding: 10px 20px;
#         font-size: 16px; border-radius: 5px; border: none; transition: all 0.3s ease;
#     }
#     .stButton>button:hover { background-color: #45a049; }
#     .css-1v0mbdj.etr89bj1 {
#         display: flex; justify-content: center; align-items: center;
#         border: 2px dashed #4CAF50; border-radius: 10px; padding: 20px;
#     }
#     .tab-content { padding: 20px; border: 1px solid #ddd; border-radius: 0 0 5px 5px; }
#     </style>
#     """, unsafe_allow_html=True)

# st.title("🎓 StudentShowcase Content Summarizer")
# st.markdown("""
#     Welcome to the StudentShowcase Content Summarizer! This tool helps students analyze and summarize various types of content:
#     - Project videos
#     - Web pages
#     - YouTube videos

#     Get valuable insights and improve your understanding of different content formats.
# """)

# @st.cache_resource
# def initialize_agent():
#     return Agent(
#         name="StudentShowcase Content Summarizer",
#         model=Gemini(id="gemini-2.0-flash-exp"),
#         tools=[DuckDuckGo()],
#         markdown=True,
#     )

# multimodal_Agent = initialize_agent()

# # --------------------------------------------------
# #            TABS: VIDEO, WEB, YOUTUBE
# # --------------------------------------------------

# tab1, tab2, tab3 = st.tabs(["📹 Video Upload", "🌐 Web Page", "🎥 YouTube Video"])

# # ------------------ Tab 1: Video Upload ------------------
# with tab1:
#     st.header("📤 Upload Your Project Video")
#     video_file = st.file_uploader(
#         "Choose a video file", 
#         type=['mp4', 'mov', 'avi'], 
#         help="Upload your project video for AI analysis (Max 200MB)"
#     )

#     if video_file:
#         st.video(video_file)
#         user_query = st.text_area(
#             "What would you like to know about your project video?",
#             placeholder="E.g., Summarize the main points, suggest improvements, analyze presentation style...",
#             help="Be specific to get the most useful insights for your project."
#         )
#         if st.button("🚀 Analyze Video", key="analyze_video_button"):
#             if not user_query:
#                 st.warning("⚠️ Please enter a question or request for analysis.")
#             else:
#                 try:
#                     with st.spinner("🔄 Processing your video and gathering insights..."):
#                         with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_video:
#                             temp_video.write(video_file.getbuffer())
#                             video_path = temp_video.name

#                         processed_video = upload_file(video_path)
#                         while processed_video.state.name == "PROCESSING":
#                             time.sleep(1)
#                             processed_video = get_file(processed_video.name)

#                         analysis_prompt = f"""
# Analyze the uploaded student project video for content and presentation in detail.
# Focus on the following aspects:
# 1. Main points and key ideas presented.
# 2. Clarity and effectiveness of communication.
# 3. Use and impact of visual aids.
# 4. Specific areas for improvement.
# 5. Overall impression and potential impact.

# Then, address the student's specific query:
# {user_query}

# Provide a detailed, constructive, and actionable response.
#                         """

#                         response = multimodal_Agent.run(analysis_prompt, videos=[processed_video])
                    
#                     st.header("🎉 Analysis Results")
#                     st.markdown(response.content)

#                     st.subheader("📌 Tips for Improvement")
#                     st.info("""
# - Review the analysis and focus on key areas for improvement.
# - Practice your presentation to enhance clarity and confidence.
# - Consider peer reviews to get different perspectives.
# - Don't hesitate to re-upload improved versions for further analysis!
#                     """)
#                 except Exception as error:
#                     st.error(f"😕 An error occurred during analysis: {error}")
#                 finally:
#                     Path(video_path).unlink(missing_ok=True)
#     else:
#         st.info("👆 Upload your project video to begin the analysis.")

# # ------------------ Tab 2: Web Page Summarization ------------------
# with tab2:
#     st.header("🌐 Summarize Web Page")
#     web_url = st.text_input("Enter the URL of the web page you want to summarize:")
#     if st.button("🔍 Summarize Web Page", key="summarize_web_button"):
#         if not web_url:
#             st.warning("⚠️ Please enter a valid URL.")
#         else:
#             try:
#                 with st.spinner("🔄 Extracting content and summarizing..."):
#                     web_content = extract_text_from_url(web_url)
#                     if not web_content or web_content.startswith("Error"):
#                         st.error(f"😕 Unable to extract content from the URL. Details: {web_content}")
#                     else:
#                         summary_prompt = f"""
# Please generate a detailed and structured summary of the following web page content:
# {web_content[:5000]}

# Your summary should include:
# 1. The main topic or purpose of the page.
# 2. Detailed key points and arguments presented.
# 3. Any significant data, statistics, or examples mentioned.
# 4. A conclusion or call to action (if applicable).

# Provide the summary in a clear and comprehensive manner.
#                         """
#                         response = multimodal_Agent.run(summary_prompt)

#                         st.header("🎉 Web Page Summary")
#                         st.markdown(response.content)
#             except Exception as error:
#                 st.error(f"😕 An error occurred during web page summarization: {error}")

# # ------------------ Tab 3: YouTube Video Summarization ------------------
# with tab3:
#     st.header("🎥 Summarize YouTube Video")
#     youtube_url = st.text_input("Enter the URL of the YouTube video you want to summarize:")

#     if st.button("🔍 Summarize YouTube Video", key="summarize_youtube_button"):
#         if not youtube_url:
#             st.warning("⚠️ Please enter a valid YouTube URL.")
#         else:
#             try:
#                 with st.spinner("🔄 Extracting transcript and chapters..."):
#                     transcript_list = get_youtube_transcript_list(youtube_url)
#                     if not transcript_list:
#                         st.error("😕 Unable to extract transcript for the video.")
#                     else:
#                         chapters = get_youtube_chapters(youtube_url)

#                         # If chapters are detected, segment the transcript accordingly
#                         if chapters:
#                             chapter_summaries = []
#                             # The final end time is the last entry's start + duration
#                             end_time = transcript_list[-1]["start"] + transcript_list[-1]["duration"]

#                             # Build a list of (start, end, title) for each chapter
#                             chapters_with_end = []
#                             for idx, (start, title) in enumerate(chapters):
#                                 if idx + 1 < len(chapters):
#                                     next_start = chapters[idx+1][0]
#                                 else:
#                                     next_start = end_time
#                                 chapters_with_end.append((start, next_start, title))

#                             # Summarize each chapter separately
#                             for start, end, title in chapters_with_end:
#                                 # Get transcript lines that fall into this chapter's time range
#                                 chapter_entries = [entry for entry in transcript_list 
#                                                    if start <= entry["start"] < end]
#                                 if chapter_entries:
#                                     chapter_text = join_transcript_entries(chapter_entries)

#                                     chapter_prompt = f"""
# Please generate detailed, note-style study notes for the chapter titled "{title}".
# The notes should include:
# - Key concepts and topics covered in this chapter.
# - Main learning points and insights.
# - Detailed explanations and examples provided.
# - Any actionable lessons or conclusions.

# Here is the transcript excerpt for this chapter:
# {chapter_text[:5000]}

# Provide the notes in a clear, organized, and concise manner.
#                                     """
#                                     chapter_response = multimodal_Agent.run(chapter_prompt)
#                                     chapter_summaries.append((title, chapter_response.content))

#                             # Display the chapter summaries
#                             st.header("🎉 YouTube Video Chapter Summaries")
#                             for title, summary in chapter_summaries:
#                                 st.subheader(f"Chapter: {title}")
#                                 st.markdown(summary)

#                         else:
#                             # No chapters found; summarize the entire transcript
#                             full_transcript = join_transcript_entries(transcript_list)
#                             summary_prompt = f"""
# Please generate detailed note-style study notes from the following YouTube video transcript.
# The notes should include:
# - Key concepts and topics covered in the video.
# - Main learning points and insights.
# - Detailed explanations, examples, and actionable lessons.
# - A summary of all topics discussed.

# Transcript (first 5000 characters):
# {full_transcript[:5000]}

# Provide the notes in a clear, organized, and concise manner.
#                             """
#                             response = multimodal_Agent.run(summary_prompt)
#                             st.header("🎉 YouTube Video Detailed Notes")
#                             st.markdown(response.content)

#                         # Embed the YouTube video
#                         video_id = YouTube(youtube_url).video_id
#                         st.video(f"https://www.youtube.com/watch?v={video_id}")
#             except Exception as error:
#                 st.error(f"😕 An error occurred during YouTube video summarization: {error}")

# # --------------------------------------------------
# #                       FOOTER
# # --------------------------------------------------
# st.markdown("---")
# st.markdown("""
# <div style="text-align: center; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; color: white;">
#     <h4>🎓 StudentShowcase Content Summarizer</h4>
#     <p>Powered by <strong>Gemini 2.0 Flash Exp</strong> | Developed for student success</p>
#     <p>
#         Made by 
#         <a href="https://github.com/VarunSingh19" target="_blank" style="color: white;">
#             <img src="https://img.icons8.com/ios-glyphs/30/ffffff/github.png" style="vertical-align: middle; margin-right: 8px;"/>
#             VarunSingh19
#         </a>
#     </p>
# </div>
# """, unsafe_allow_html=True)
import streamlit as st

# Set page configuration immediately after importing Streamlit.
st.set_page_config(
    page_title="StudentShowcase Content Summarizer",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

import pymongo
import os
import bcrypt
import cloudinary
import cloudinary.uploader
import cloudinary.api
from dotenv import load_dotenv  # using python-dotenv
from datetime import datetime
import tempfile
import time
import requests
import re
from bs4 import BeautifulSoup
from pytube import YouTube
from youtube_transcript_api import YouTubeTranscriptApi
from pathlib import Path

# Summarization agent libraries
from phi.agent import Agent
from phi.model.google import Gemini
from phi.tools.duckduckgo import DuckDuckGo
from google.generativeai import upload_file, get_file
import google.generativeai as genai

# --------------------------------------------------
# Load environment variables and configure APIs
# --------------------------------------------------
load_dotenv()

# MongoDB Configuration
MONGODB_URI = os.getenv("MONGODB_URI")
if not MONGODB_URI:
    st.error("MONGODB_URI not found in environment variables.")
    st.stop()

client = pymongo.MongoClient(MONGODB_URI)
db = client["studentshowcase_db"]

# Cloudinary Configuration
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

# Google Generative AI API Key Configuration
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)
else:
    st.warning("GOOGLE_API_KEY not provided. Google Generative AI functionalities may be disabled.")

# --------------------------------------------------
# Inject Custom CSS
# --------------------------------------------------
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
    .css-1v0mbdj.etr89bj1 {
        display: flex; justify-content: center; align-items: center;
        border: 2px dashed #4CAF50; border-radius: 10px; padding: 20px;
    }
    .tab-content { padding: 20px; border: 1px solid #ddd; border-radius: 0 0 5px 5px; }
    </style>
    """, unsafe_allow_html=True
)

# --------------------------------------------------
# Session State for Authentication
# --------------------------------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user" not in st.session_state:
    st.session_state.user = {}

# --------------------------------------------------
# Helper Functions for Authentication & Storage
# --------------------------------------------------
def get_user_by_email(email):
    """Fetch a user document by email."""
    return db.users.find_one({"email": email})

def create_user(username, email, password, profile_pic_url=None):
    """Create a new user; returns the user document and an error message if any."""
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
    """Update a user's profile picture."""
    db.users.update_one({"_id": user_id}, {"$set": {"profile_pic_url": profile_pic_url}})

def save_summary(user_id, summary_type, input_data, result_text):
    """Store a summarization result in MongoDB."""
    doc = {
        "user_id": user_id,
        "type": summary_type,  # "video", "web", or "youtube"
        "input": input_data,
        "result": result_text,
        "timestamp": datetime.utcnow()
    }
    db.summaries.insert_one(doc)

# --------------------------------------------------
# Summarization Helper Functions
# --------------------------------------------------
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
    except Exception as e:
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

# --------------------------------------------------
# Summarization Agent Initialization
# --------------------------------------------------
@st.cache_resource
def initialize_agent():
    return Agent(
        name="StudentShowcase Content Summarizer",
        model=Gemini(id="gemini-2.0-flash-exp"),
        tools=[DuckDuckGo()],
        markdown=True,
    )

multimodal_Agent = initialize_agent()

# --------------------------------------------------
# Authentication Forms (Login / Sign Up)
# --------------------------------------------------
def show_auth():
    st.title("🎓 StudentShowcase Content Summarizer")
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
                st.experimental_rerun()
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
                    st.experimental_rerun()

# --------------------------------------------------
# Main App Navigation (only for logged in users)
# --------------------------------------------------
if not st.session_state.logged_in:
    show_auth()
else:
    # Sidebar navigation
    nav = st.sidebar.radio("Navigation", ["Summarize", "Profile", "Logout"])
    if nav == "Logout":
        st.session_state.logged_in = False
        st.session_state.user = {}
        st.experimental_rerun()
    elif nav == "Summarize":
        st.title("🎓 StudentShowcase Content Summarizer")
        st.markdown(
            """
            Welcome to the StudentShowcase Content Summarizer! Choose one of the options below to analyze your content:
            - Project Videos
            - Web Pages
            - YouTube Videos
            """
        )

        # --------------------------------------------------
        # Tab Layout for Summarization Options
        # --------------------------------------------------
        tab1, tab2, tab3 = st.tabs(["📹 Video Upload", "🌐 Web Page", "🎥 YouTube Video"])

        # ------------------ Tab 1: Video Upload ------------------
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
                    placeholder="E.g., Summarize the main points, suggest improvements, analyze presentation style...",
                    help="Be specific to get the most useful insights for your project."
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
                            # Save the summary result to MongoDB
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

        # ------------------ Tab 2: Web Page Summarization ------------------
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
                                # Save the summary to MongoDB
                                save_summary(
                                    st.session_state.user["_id"],
                                    "web",
                                    web_url,
                                    response.content
                                )
                    except Exception as error:
                        st.error(f"😕 An error occurred during web page summarization: {error}")

        # ------------------ Tab 3: YouTube Video Summarization ------------------
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
                                        if idx + 1 < len(chapters):
                                            next_start = chapters[idx+1][0]
                                        else:
                                            next_start = end_time
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
                                    # Save the combined YouTube summary to MongoDB
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

    elif nav == "Profile":
        st.title("👤 Your Profile")
        user = st.session_state.user

        # Display profile picture (or a default image)
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
                    st.experimental_rerun()
                except Exception as e:
                    st.error(f"Failed to update profile picture: {e}")
            else:
                st.error("Please select a picture to upload.")

        st.markdown("---")
        st.subheader("Your Past Summarizations")
        summaries = list(db.summaries.find({"user_id": user["_id"]}).sort("timestamp", -1))
        if summaries:
            for summ in summaries:
                st.markdown(f"**Type:** {summ['type'].capitalize()} | **On:** {summ['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
                st.markdown(f"**Input:** {summ['input']}")
                with st.expander("View Summary"):
                    st.markdown(summ['result'])
                st.markdown("---")
        else:
            st.info("You haven't generated any summaries yet.")

# --------------------------------------------------
# Footer
# --------------------------------------------------
st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; color: white;">
        <h4>🎓 StudentShowcase Content Summarizer</h4>
        <p>Powered by <strong>Gemini 2.0 Flash Exp</strong> | Developed for student success</p>
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
