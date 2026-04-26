# 📄 Resume Analyzer AI

**AI-Powered Resume Screening and Optimization System**

[![Live Demo](https://img.shields.io/badge/Live-Demo-brightgreen.svg)](https://resumeanalyzer-ai-jlhy.onrender.com/)
[![GitHub stars](https://img.shields.io/github/stars/latamishra5/resumeanalyzer_ai.svg?style=social&label=Star)](https://github.com/latamishra5/resumeanalyzer_ai)
[![GitHub forks](https://img.shields.io/github/forks/latamishra5/resumeanalyzer_ai.svg?style=social&label=Fork)](https://github.com/latamishra5/resumeanalyzer_ai)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

---

## 🎯 Overview

Resume Analyzer AI is an intelligent web application that leverages cutting-edge AI and Natural Language Processing to help job seekers optimize their resumes for better job opportunities. Built with Streamlit and powered by Google Gemini AI, this tool provides comprehensive resume analysis, ATS scoring, and personalized recommendations.

### ✨ Key Features

- 🤖 **AI-Powered Analysis** - Advanced resume evaluation using Google Gemini AI
- 📊 **ATS Scoring** - Real-time Applicant Tracking System compatibility score
- 📝 **Resume Builder** - Professional templates with customizable sections
- 🎯 **Job Matching** - Intelligent job-resume compatibility analysis
- 📈 **Analytics Dashboard** - Track your resume improvement over time
- 🔍 **Keyword Optimization** - Identify missing keywords for better ATS performance
- 💡 **Personalized Feedback** - Actionable recommendations for resume enhancement
- 📱 **Responsive Design** - Works seamlessly on desktop and mobile devices

---

## 🚀 Live Demo

**🔗 [Try Resume Analyzer AI Now](https://resumeanalyzer-ai-jlhy.onrender.com/)**

✅ **Status**: Live and Working on Render Cloud

---

## 📸 Screenshots

<div align="center">

| Resume Upload | AI Analysis | Resume Builder |
|---------------|-------------|----------------|
| ![Resume Upload](https://raw.githubusercontent.com/latamishra5/resumeanalyzer_ai/main/screenshots/resume_upload.jpg) | ![AI Analysis](https://raw.githubusercontent.com/latamishra5/resumeanalyzer_ai/main/screenshots/resume_scoring.png) | ![Resume Builder](https://raw.githubusercontent.com/latamishra5/resumeanalyzer_ai/main/screenshots/resume_builder.png) |

| Dashboard | Job Matching | About |
|-----------|-------------|-------|
| ![Dashboard](https://raw.githubusercontent.com/latamishra5/resumeanalyzer_ai/main/screenshots/dashboard.png) | ![Job Matching](https://raw.githubusercontent.com/latamishra5/resumeanalyzer_ai/main/screenshots/ranking_maching.png) | ![About](https://raw.githubusercontent.com/latamishra5/resumeanalyzer_ai/main/screenshots/about.png) |

</div>

---

## 🛠️ Technology Stack

| Component | Technology | Description |
|-----------|-------------|-------------|
| **Frontend** | ![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=flat&logo=streamlit) | Web application framework |
| **Backend** | ![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python) | Core application logic |
| **AI/ML** | ![Google Gemini](https://img.shields.io/badge/Gemini%20AI-4285F4?style=flat&logo=google) | Resume analysis engine |
| **NLP** | ![NLTK](https://img.shields.io/badge/NLTK-0096D6?style=flat) | Natural language processing |
| **Database** | ![SQLite](https://img.shields.io/badge/SQLite-003B57?style=flat&logo=sqlite) | Data storage |
| **Parsing** | ![Pyresparser](https://img.shields.io/badge/Pyresparser-FF6B6B?style=flat) | Resume parsing |

---

## 📋 Prerequisites

- **Python 3.8+** - Latest Python version recommended
- **Git** - For cloning the repository
- **Google Gemini API Key** - For AI analysis features
- **Basic understanding of Python** - For customization

---

## 🚀 Quick Start

### Method 1: Clone and Run Locally

```bash
# 1. Clone the repository
git clone https://github.com/latamishra5/resumeanalyzer_ai.git
cd resumeanalyzer_ai

# 2. Create and activate virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
cp .env.example .env
# Edit .env file with your API keys

# 5. Run the application
streamlit run app.py
```

### Method 2: One-Click Deployment

[![Deploy on Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io/deploy?repository=latamishra5/resumeanalyzer_ai)

---

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the root directory:

```env
# Google Gemini AI API Key (Required)
GOOGLE_API_KEY=your_google_gemini_api_key_here

# OpenRouter API Key (Optional - for alternative AI models)
OPENROUTER_API_KEY=your_openrouter_api_key_here

# Database Configuration
DATABASE_URL=sqlite:///resume_data.db

# Application Settings
DEBUG=False
LOG_LEVEL=INFO
```

### Getting API Keys

#### Google Gemini AI
1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the key and add it to your `.env` file

#### OpenRouter (Optional)
1. Sign up at [OpenRouter](https://openrouter.ai/)
2. Navigate to API Keys section
3. Generate a new API key
4. Add it to your `.env` file

---

## 🌐 Deployment Guide

### ✅ Render Cloud Deployment (Working)

**Current Live URL**: https://resumeanalyzer-ai-jlhy.onrender.com/

#### Deployment Configuration:
- **Platform**: Render Cloud
- **Runtime**: Python 3.14.3
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `streamlit run app.py --server.port=$PORT --server.address=0.0.0.0`
- **Status**: ✅ Successfully Deployed

### Streamlit Cloud Deployment (Alternative)

#### Step 1: Prepare Your Repository
1. Ensure all files are committed to GitHub
2. Verify `requirements.txt` is complete
3. Add `.env.example` file (don't commit actual `.env`)
4. Make sure `app.py` is the main application file

#### Step 2: Deploy to Streamlit Cloud
1. Go to [share.streamlit.io](https://share.streamlit.io/)
2. Connect your GitHub account
3. Select the `resumeanalyzer_ai` repository
4. Configure deployment settings:
   - **Main file path**: `app.py`
   - **Python version**: `3.9` or higher
   - **Requirements file**: `requirements.txt`

#### Step 3: Set Environment Variables
In Streamlit Cloud dashboard:
1. Go to your app settings
2. Add secrets:
   ```toml
   GOOGLE_API_KEY = "your_actual_api_key_here"
   OPENROUTER_API_KEY = "your_actual_api_key_here"
   ```

#### Step 4: Deploy
Click "Deploy" and wait for the build to complete.

#### Step 5: Test Your App
1. Visit your Streamlit Cloud URL
2. Test all features
3. Check if API keys are working properly

### Alternative Deployment Options

You can also deploy to other platforms like:
- **Heroku**: Use Heroku CLI with Python buildpack
- **DigitalOcean**: Use App Platform
- **AWS**: Use Elastic Beanstalk
- **Google Cloud**: Use Cloud Run

---

## 🤔 Troubleshooting

### Common Issues

#### 1. API Key Errors
```
Error: Google API key is not configured
```
**Solution**: Ensure your `GOOGLE_API_KEY` is properly set in environment variables.

#### 2. Module Import Errors
```
ModuleNotFoundError: No module named 'xxx'
```
**Solution**: Run `pip install -r requirements.txt` to install all dependencies.

#### 3. Streamlit Cloud Deployment Issues
- **Build fails**: Check `requirements.txt` for correct package names and versions
- **App crashes**: Verify environment variables are set in Streamlit Cloud secrets
- **Slow loading**: Optimize image sizes and reduce API calls
- **Import errors**: Ensure all imports use absolute paths
- **API key errors**: Check secrets are properly configured in Streamlit Cloud

#### 4. Database Issues
```
sqlite3.OperationalError: no such table
```
**Solution**: The app will auto-create tables on first run. If issues persist, delete `resume_data.db` and restart.

### Performance Optimization

1. **Reduce API calls**: Cache results when possible
2. **Optimize images**: Use compressed images for better loading
3. **Lazy loading**: Load components only when needed
4. **Error handling**: Implement proper try-catch blocks

---

## 📁 Project Structure

```
resumeanalyzer_ai/
├── 📄 app.py                 # Main application file
├── 📄 requirements.txt      # Python dependencies
├── 📄 .env.example         # Environment variables template
├── 📄 README.md            # Project documentation
├── 📄 run_app.py           # Application launcher
├── 📄 setup_chromedriver.py # ChromeDriver setup
├── 📄 create_admin.py      # Admin account creator
├── 📄 reset_admin_password.py # Admin password reset
├── 📁 config/              # Configuration modules
│   ├── 📄 database.py      # Database operations
│   ├── 📄 courses.py       # Course recommendations
│   └── 📄 job_roles.py     # Job role definitions
├── 📁 utils/               # Utility modules
│   ├── 📄 ai_resume_analyzer.py  # AI analysis engine
│   ├── 📄 resume_analyzer.py      # Basic analysis
│   ├── 📄 resume_builder.py      # Resume builder
│   ├── 📄 resume_parser.py       # Resume parsing
│   ├── 📄 database.py            # Database utilities
│   └── 📄 excel_manager.py       # Excel export
├── 📁 dashboard/           # Dashboard components
├── 📁 feedback/            # Feedback system
├── 📁 jobs/               # Job search functionality
│   ├── 📄 job_search.py    # Job search
│   ├── 📄 linkedin_scraper.py # LinkedIn scraper
│   ├── 📄 companies.py     # Company data
│   ├── 📄 suggestions.py   # Job suggestions
│   └── 📄 job_portals.py   # Job portals
├── 📁 style/              # CSS styles
│   └── 📄 style.css        # Main styles
├── 📁 screenshots/        # Application screenshots
├── 📁 poppler/            # Poppler for PDF processing
└── 📁 venv/              # Virtual environment (gitignored)
```

---

## 🎮 Usage Guide

### 1. Resume Analysis
- Upload your resume (PDF, DOCX, or TXT format)
- Select your target job role and experience level
- Click "Analyze Resume" for comprehensive AI feedback
- Review scores, strengths, and improvement suggestions

### 2. Resume Builder
- Choose from professional templates
- Fill in personal information, experience, and education
- Add skills and projects
- Generate and download your optimized resume

### 3. Dashboard Analytics
- View analysis history and trends
- Track your resume score improvements
- Export data to Excel for further analysis

### 4. Job Search Integration
- Browse job opportunities
- Get personalized job recommendations
- Match your resume with job descriptions

---

## 🤝 Contributing

We welcome contributions! Here's how you can help:

### Development Setup
```bash
# Fork and clone the repository
git clone https://github.com/YOUR_USERNAME/resumeanalyzer_ai.git
cd resumeanalyzer_ai

# Create a new branch
git checkout -b feature/amazing-feature

# Make your changes
# ... code changes ...

# Commit and push
git commit -m "Add amazing feature"
git push origin feature/amazing-feature

# Open a Pull Request
```

### Contribution Guidelines
- 🌟 **Star** the repository if you like it
- 🐛 **Report bugs** with detailed descriptions
- 💡 **Suggest features** in the Issues section
- 📝 **Improve documentation**
- 🔧 **Submit pull requests** with clear descriptions

### Code Style
- Follow PEP 8 guidelines
- Add comments for complex logic
- Include docstrings for functions
- Test your changes before submitting

---

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2026 Lata Mishra

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
```

---

## 🙏 Acknowledgments

### Core Technologies
- **[Streamlit](https://streamlit.io/)** - Amazing web app framework
- **[Google Gemini AI](https://ai.google.dev/)** - Powerful AI analysis capabilities
- **[NLTK](https://www.nltk.org/)** - Natural language processing toolkit
- **[Pyresparser](https://github.com/OmkarPathak/pyresparser)** - Resume parsing library
- **[Plotly](https://plotly.com/)** - Interactive data visualization

### Inspiration & Support
- The open-source community for continuous inspiration
- All contributors and users who help improve this project
- Mentors and peers who provided valuable feedback

---

## 📞 Contact & Support

### 📧 Email
- **Primary**: latamishra987@gmail.com
- **Support**: support@resumeanalyzer.ai

### 🌐 Social Links
- **GitHub**: [latamishra5](https://github.com/latamishra5)
- **LinkedIn**: [Lata Mishra](https://www.linkedin.com/in/latamishra5/)
- **Portfolio**: [Coming Soon]

### 💬 Community
- **Discord**: [Join our Discord](https://discord.gg/resumeanalyzer)
- **Twitter**: [@ResumeAnalyzerAI](https://twitter.com/ResumeAnalyzerAI)

### 📋 Support Channels
- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/latamishra5/resumeanalyzer_ai/issues)
- 💡 **Feature Requests**: [GitHub Discussions](https://github.com/latamishra5/resumeanalyzer_ai/discussions)
- 📧 **Email Support**: latamishra987@gmail.com

---

## 🔄 Version History

| Version | Date | Features |
|---------|------|----------|
| **v1.4.0** | Dec 2026 | ✨ Enhanced UI, 🐛 Bug fixes, 🚀 Performance improvements |
| **v1.3.0** | Nov 2026 | 🔐 Authentication system, 👤 User profiles |
| **v1.2.0** | Oct 2026 | 🎨 Modern UI redesign, 📱 Mobile optimization |
| **v1.1.0** | Sep 2026 | 🤖 Gemini AI integration, 📊 Advanced analytics |
| **v1.0.0** | Aug 2026 | 🎉 Initial release with core features |

---

## ⭐ Show Your Support

If this project helped you, please consider:

- ⭐ **Starring** this repository
- 🍴 **Forking** for your own use
- 📢 **Sharing** with your network
- 💰 **Sponsoring** for continued development
- 🐛 **Reporting** issues to help improve

---

<div align="center">

**🚀 Built with ❤️ using [Streamlit](https://streamlit.io/) and [Python](https://www.python.org/)**

**[⬆️ Back to Top](#-resume-analyzer-ai)**

</div> 
