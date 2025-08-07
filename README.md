# AI Study Planner

An intelligent study planning application that helps you organize your study schedule and sync it with Google Calendar. This project uses AI to help you create and manage your study plans effectively.

## 🚀 Features

- **AI-Powered Planning**: Get personalized study plans based on your subjects and available time
- **Google Calendar Integration**: Automatically sync your study schedule with Google Calendar
- **Interactive Interface**: Chat-based interface for easy interaction with the planning system
- **Flexible Scheduling**: Supports custom time zones and study preferences
- **Export/Import**: Save and load study plans as JSON files

## 📋 Prerequisites

Before you begin, ensure you have the following installed:

- Python 3.8 or higher
- pip (Python package manager)
- Google Cloud Platform account with Calendar API enabled
- API key for the AI model (Gemini)

## 🛠 Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/BuiHenry1404/ai-agent-project.git
   cd ai-study-planner-openrouter
   ```

2. **Create and activate a virtual environment** (recommended)
   ```bash
   # Windows
   python -m venv venv
   .\venv\Scripts\activate
   
   # macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   Create a `.env` file in the project root and add your API keys:
   ```
   GEMINI_API_KEY=your_gemini_api_key_here
   GOOGLE_CREDENTIALS=path/to/your/credentials.json
   ```

## 🔑 Google Calendar API Setup

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google Calendar API
4. Create OAuth 2.0 credentials (OAuth client ID)
5. Download the credentials JSON file and save it as `credentials.json` in the project root
6. On first run, the application will open a browser window for authentication

## 🚦 Usage

1. **Run the application**
   ```bash
   python main.py
   ```

2. **Interact with the AI planner**
   - Follow the on-screen instructions to create your study plan
   - The AI will help you schedule your study sessions
   - Your schedule will be automatically synced with Google Calendar

3. **Save/Load plans**
   - Study plans can be saved as JSON files
   - Load previous plans to modify or review them

## 📂 Project Structure

- `main.py`: Main application entry point
- `google_calendar.py`: Handles Google Calendar integration
- `file_stream_console.py`: Console interface utilities
- `requirements.txt`: Project dependencies
- `.env`: Environment variables (not committed to version control)

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [AutoGen](https://github.com/microsoft/autogen)
- Uses Google Calendar API for scheduling
- Powered by Gemini AI
