````markdown
# QuickSummarizer

**QuickSummarizer** is an interactive Streamlit web application designed to help students and educators analyze and summarize various types of content—including project videos, web pages, and YouTube videos—using advanced AI-powered summarization techniques. The app features user authentication, profile management, and data storage via MongoDB, and leverages external APIs (such as Cloudinary and Google Generative AI) for enhanced functionality.

---

## Table of Contents

- [Features](#features)
- [Demo](#demo)
- [Architecture](#architecture)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [File Structure](#file-structure)
- [Dependencies](#dependencies)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)

---

## Features

- **User Authentication:**

  - Secure login and sign-up (with password hashing using bcrypt).
  - Profile management with optional profile picture uploads via Cloudinary.

- **Content Summarization:**

  - **Project Video Analysis:** Upload a project video, then request detailed feedback including main points, presentation style, and improvement suggestions.
  - **Web Page Summarization:** Enter a URL to extract and summarize key content from a web page.
  - **YouTube Video Summarization:** Generate detailed chapter-wise study notes or full video summaries by extracting transcripts and chapter information from YouTube videos.

- **AI-Powered Summarization:**

  - Utilizes a Gemini AI model (`gemini-2.0-flash-exp`) along with custom prompts to generate structured, actionable summaries.
  - Supports integration with Google Generative AI services (if an API key is provided).

- **Data Storage:**

  - MongoDB (Atlas) is used for storing user details and summary history.
  - Summaries can be viewed, deleted, and downloaded as PDFs generated with the FPDF library.

- **User Interface:**
  - Responsive design with custom CSS styling.
  - Sidebar navigation for easy access to summarization, profile management, and logout functionalities.

---

## Demo

![Screenshot of App](https://via.placeholder.com/800x400)

> **Note:** This demo screenshot is a placeholder. Replace it with actual screenshots from your deployed app.

---

## Architecture

The application is built using the following core components:

- **Frontend:**

  - Built with [Streamlit](https://streamlit.io/) for rapid web app development.
  - Custom CSS is injected for styling.

- **Backend & APIs:**

  - **MongoDB Atlas:** For data persistence (user data and summarization records).
  - **Cloudinary:** For hosting and managing user-uploaded profile pictures.
  - **Google Generative AI & Gemini Model:** For performing advanced content summarization tasks.
  - **External Libraries:**
    - `pytube` and `youtube_transcript_api` for YouTube integration.
    - `BeautifulSoup` and `requests` for web content extraction.
    - `FPDF` for PDF generation.

- **Session Management:**
  - Uses Streamlit’s session state to manage user sessions and navigation.

---

## Installation

### Prerequisites

- Python 3.8+
- [MongoDB Atlas](https://www.mongodb.com/cloud/atlas) account (or a local MongoDB instance)
- [Cloudinary](https://cloudinary.com/) account
- Google Generative AI API key (optional)

### Clone the Repository

```bash
git https://github.com/VarunSingh19/QuickSummarizer
cd QuickSummarizer
```
````

### Create and Activate a Virtual Environment

```bash
python -m venv venv
source venv/bin/activate   # On Windows use: venv\Scripts\activate
```

### Install Required Packages

```bash
pip install -r requirements.txt
```

_If you don’t have a `requirements.txt` yet, you can create one by listing these packages:_

- streamlit
- pymongo
- bcrypt
- python-dotenv
- cloudinary
- requests
- beautifulsoup4
- pytube
- youtube_transcript_api
- fpdf
- phi-agent
- google-generativeai

---

## Configuration

1. **Environment Variables:**  
   Create a `.env` file in the project root and add the following variables:

   ```ini
   # MongoDB Configuration
   MONGODB_URI="your_mongodb_connection_string"

   # Cloudinary Configuration
   CLOUDINARY_CLOUD_NAME="your_cloudinary_cloud_name"
   CLOUDINARY_API_KEY="your_cloudinary_api_key"
   CLOUDINARY_API_SECRET="your_cloudinary_api_secret"

   # Google API Configuration (Optional)
   GOOGLE_API_KEY="your_google_api_key"
   ```

2. **MongoDB:**  
   Update the `MONGODB_URI` in your `.env` with your MongoDB connection string. If using MongoDB Atlas, ensure your IP address is whitelisted.

3. **Cloudinary:**  
   Set up your Cloudinary account and update the credentials in the `.env` file.

4. **Google Generative AI:**  
   If you wish to enable Google Generative AI functionalities, add your API key. Otherwise, the app will run with limited AI functionality.

---

## Usage

1. **Start the Application:**

   ```bash
   streamlit run app.py
   ```

2. **Authentication:**

   - **Sign Up:** Create a new account by providing a username, email, and password. Optionally, upload a profile picture.
   - **Login:** Access the app by logging in with your email and password.

3. **Content Summarization:**

   - **Project Videos:** Upload a video file and provide a custom query to receive a detailed analysis.
   - **Web Pages:** Enter a valid URL to extract and summarize the content.
   - **YouTube Videos:** Enter a YouTube video URL to generate chapter-wise study notes or a complete transcript summary.

4. **Profile & History:**
   - View and update your profile, including uploading a new profile picture.
   - Review your past summarizations, download them as PDFs, or delete them from the history.

---

## File Structure

```plaintext
├── app.py                  # Main Streamlit application file
├── README.md               # This file
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables (not committed)
└── assets/                 # (Optional) Directory for additional assets like images or CSS
```

---

## Dependencies

- [Streamlit](https://streamlit.io/)
- [PyMongo](https://pymongo.readthedocs.io/)
- [bcrypt](https://pypi.org/project/bcrypt/)
- [Cloudinary](https://cloudinary.com/documentation/python_integration)
- [python-dotenv](https://pypi.org/project/python-dotenv/)
- [Requests](https://pypi.org/project/requests/)
- [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/)
- [Pytube](https://pytube.io/)
- [youtube_transcript_api](https://pypi.org/project/youtube-transcript-api/)
- [FPDF](https://pypi.org/project/fpdf/)
- [phi-agent](https://github.com/yourusername/phi-agent) (or the appropriate source)
- [google-generativeai](https://pypi.org/project/google-generativeai/)

---

## Contributing

Contributions are welcome! If you have suggestions, bug fixes, or enhancements, please follow these steps:

1. Fork the repository.
2. Create a new branch: `git checkout -b feature/YourFeature`
3. Commit your changes: `git commit -m 'Add some feature'`
4. Push to the branch: `git push origin feature/YourFeature`
5. Open a pull request.

Please ensure your code adheres to the existing style and includes appropriate tests or documentation where applicable.

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## Contact

Developed by **VarunSingh19**

- GitHub: [VarunSingh19](https://github.com/VarunSingh19)
- Email: [your-email@example.com](mailto:varunsinghh2409@gmail.com)

For any questions or suggestions, feel free to open an issue or contact me directly.

---

> _Empowering students with AI-driven insights to enhance their academic projects and presentations._
