# SHRUVI – Personal AI Voice Assistant 🤖

**SHRUVI** is a personal AI voice assistant developed using Python. It can understand voice commands, answer questions, search the internet, provide weather updates, remember information, and perform useful tasks on your computer.

## ✨ Features

- 🎙️ **Voice Recognition:** Understands spoken commands using speech recognition.
- 🧠 **AI Conversations:** Uses Google Gemini for intelligent responses.
- 🔊 **Female Voice:** Uses Microsoft Edge Text-to-Speech.
- 🌐 **Internet Search:** Searches the web using Tavily.
- 🌦️ **Weather Updates:** Retrieves weather information using Open-Meteo.
- 🕒 **Date and Time:** Provides the current date and time.
- 💾 **Personal Memory:** Remembers and recalls user-defined facts.
- 💻 **Application Control:** Opens supported desktop applications.
- 🌍 **Website Access:** Opens websites such as Google, YouTube, Gmail, and others.

## 🛠️ Technologies Used

- Python
- Google Gemini API
- Tavily Search API
- Microsoft Edge TTS
- SpeechRecognition
- SoundDevice
- NumPy
- Open-Meteo API
- Requests

## 📁 Project Structure

```text
SHRUVI/
│
├── main.py
├── mic_test.py
├── .env
├── .gitignore
├── requirements.txt
├── README.md
└── .vscode/
```

**Note:** Private files such as `.env`, `memory.json`, and `.venv` are excluded from GitHub.

## ⚙️ Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/shivamRider-create/shurvi.git
```

### 2. Navigate to the project folder

```bash
cd shurvi
```

### 3. Create a virtual environment

```bash
python -m venv .venv
```

### 4. Activate the virtual environment

For Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

### 5. Install dependencies

```bash
pip install -r requirements.txt
```

### 6. Configure API keys

Create a `.env` file in the project folder:

```env
GEMINI_API_KEY=your_gemini_api_key
TAVILY_API_KEY=your_tavily_api_key
```

Replace the placeholders with your own API keys.

**Important:** Never upload your actual API keys to GitHub.

### 7. Run SHRUVI

```bash
python main.py
```

## 🔐 Security

- API keys are stored in a local `.env` file.
- `.gitignore` prevents private files from being uploaded.
- Never share API keys, passwords, or personal credentials.

## 🚀 Future Improvements

- Improved natural language understanding.
- More desktop automation features.
- Better conversation memory.
- Enhanced voice recognition.
- Additional AI-powered capabilities.

## 👨‍💻 Developer

**Shivam Vishwakarma**

GitHub: [shivamRider-create](https://github.com/shivamRider-create)

Project Repository: [SHRUVI](https://github.com/shivamRider-create/shurvi)

## 🎯 Project Goal

The goal of SHRUVI is to develop a personal AI-powered voice assistant that makes everyday computer interactions easier through voice commands and intelligent automation.

---

**SHRUVI – Your Personal AI Voice Assistant.** ❤️