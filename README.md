# LegalBot - AI-Powered Judiciary Reference System

A sophisticated legal assistant chatbot that helps users find relevant Indian legal sections (IPC, CrPC, etc.) using PDF-based document search, vector embeddings, and AI-powered answer generation.

## 🎯 Features

- 🔐 **Secure Authentication**: JWT tokens + bcrypt password hashing with PostgreSQL
- 💬 **Natural Language Queries**: Ask legal questions in plain English
- 📚 **PDF-Based Search**: Semantic search through pre-seeded legal documents using FAISS
- 🤖 **AI-Powered Answers**: Google Gemini API for intelligent, contextual responses
- 📊 **Citation Tracking**: View exact sources with page numbers
- ⭐ **Feedback System**: Rate responses to improve the system
- 💾 **Chat History**: All conversations stored in PostgreSQL database

## 🏗️ Technology Stack

- **Frontend**: Streamlit
- **Backend**: Python, Prisma ORM
- **Database**: PostgreSQL
- **Authentication**: JWT (PyJWT) + bcrypt
- **PDF Processing**: PyPDF2, pdfplumber
- **Vector Search**: FAISS + Sentence Transformers
- **AI Model**: Google Gemini Pro
- **Embeddings**: all-MiniLM-L6-v2

## 📁 Project Structure

```
Sneha Bot/
├── backend/
│   ├── auth_prisma.py          # JWT authentication with Prisma
│   ├── ingestion_prisma.py     # PDF processing pipeline
│   ├── retrieval_prisma.py     # FAISS search with database
│   └── llm_handler.py          # Gemini API integration
├── streamlit_app/
│   └── app_prisma.py           # Main Streamlit UI
├── prisma/
│   └── schema.prisma           # Database schema
├── data/
│   ├── pdfs/                   # Legal PDF documents
│   └── index/                  # FAISS index storage
├── requirements.txt            # Python dependencies
├── setup.py                    # Automated setup script
├── verify_setup.py            # System verification
├── .env.example               # Environment template
├── SETUP_GUIDE.md             # Detailed setup instructions
└── README.md                   # This file
```

## 🚀 Quick Start

### 0. **Activate Virtual Environment (IMPORTANT!)**

**Windows:**
```bash
# First time - create venv
setup_venv.bat

# Or manually
python -m venv venv
venv\Scripts\activate
```

**Linux/Mac:**
```bash
# First time - create venv
./setup_venv.sh

# Or manually
python3 -m venv venv
source venv/bin/activate
```

**✅ You'll see (venv) at the start of your command line when activated!**

> 📖 **Need help?** See [HOW_TO_ACTIVATE_VENV.md](HOW_TO_ACTIVATE_VENV.md) for detailed instructions

### 1. Install Dependencies

**Make sure venv is activated first!**

```bash
pip install -r requirements.txt
```

### 2. Setup PostgreSQL

**Option A: Local Installation**
```bash
# Install PostgreSQL, then create database
createdb legalbot
```

**Option B: Cloud Database (Easier)**
- [ElephantSQL](https://www.elephantsql.com/) (Free tier)
- [Supabase](https://supabase.com/) (Free tier)
- [Railway](https://railway.app/) (Free tier)

### 3. Configure Environment

```bash
# Copy example file
copy .env .env
```

Edit `.env` with your credentials:

```env
# Get free API key from https://makersuite.google.com/app/apikey
GEMINI_API_KEY=your_actual_api_key

# PostgreSQL connection
DATABASE_URL=postgresql://username:password@localhost:5432/legalbot

# Generate random string (32+ characters)
JWT_SECRET_KEY=your_super_secure_random_string_here
```

### 4. Initialize Database

```bash
# Generate Prisma client
prisma generate

# Create database tables
prisma db push
```

### 5. Add Legal Documents

Place PDF files (IPC, CrPC, etc.) in `data/pdfs/` folder.

**Free legal PDF sources:**
- [India Code](https://www.indiacode.nic.in/)
- [Legislative Department](https://legislative.gov.in/)

### 6. Index Documents

```bash
python backend/ingestion_prisma.py
```

This will parse PDFs, generate embeddings, and create the search index.

### 7. Verify Setup

```bash
python verify_setup.py
```

### 8. Launch Application

```bash
streamlit run streamlit_app/app.py
```

Opens at `http://localhost:8501` 🎉

## 📖 Usage Guide

### Sign Up / Login
1. Create account with email and password
2. Secure JWT token generated automatically
3. All data encrypted and stored in PostgreSQL

### Ask Questions

**PDF + AI Mode** (Recommended):
- Searches indexed legal PDFs first
- Retrieves top 5 most relevant sections
- AI generates comprehensive answer with citations
- Shows exact sources and page numbers

**AI Only Mode**:
- Direct AI response without document search
- Useful for general legal concepts
- No specific citations

### Example Queries
- "What is Section 302 IPC?"
- "Explain bail provisions in CrPC"
- "What are the rights of an arrested person?"
- "Difference between cognizable and non-cognizable offences"
- "Defamation laws in India"

### View Sources
- Click "View Sources" to see referenced documents
- Exact page numbers and text excerpts shown
- Verify AI answers against source material

### Provide Feedback
- 👍 Thumbs up for helpful answers
- 👎 Thumbs down for issues
- Stored in database for system improvement

## 🗄️ Database Schema

### Users
- Email, name, hashed password
- JWT authentication
- Created/updated timestamps

### Conversations
- Linked to user account
- Groups related messages
- Optional title

### Messages
- User queries and AI responses
- Sources stored as JSON
- Rating (positive/negative)
- Conversation relationship

### Documents
- PDF metadata (filename, title, pages)
- File size and upload date

### DocChunks
- Text chunks from PDFs
- Page numbers
- Vector IDs for FAISS lookup
- Document relationship

## 🔧 Advanced Usage

### Add New Documents

```bash
# 1. Add PDF to data/pdfs/
# 2. Re-run ingestion
python backend/ingestion_prisma.py
```

### View Database

```bash
# Open Prisma Studio
prisma studio
```

Access at `http://localhost:5555`

### Database Migrations

```bash
# After schema.prisma changes
prisma db push

# Or create migration
prisma migrate dev --name your_migration_name
```

### Clear Index and Rebuild

```bash
# Delete old index
del data\index\faiss.index

# Re-run ingestion
python backend/ingestion_prisma.py
```

## 🛠️ Troubleshooting

### "Prisma client not found"
```bash
prisma generate
```

### "Cannot connect to database"
```bash
# Test connection
psql -d legalbot

# Verify DATABASE_URL in .env
```

### "FAISS index not found"
```bash
python backend/ingestion_prisma.py
```

### "Gemini API error"
- Verify GEMINI_API_KEY in .env
- Check quota at [Google AI Studio](https://makersuite.google.com/)
- Try "AI Only" mode

## 📊 System Architecture

```
┌─────────────────┐
│  Streamlit UI   │
└────────┬────────┘
         │
    ┌────▼────────────────────┐
    │   Backend Services      │
    │                         │
    │  ┌──────────────────┐  │
    │  │ Auth (JWT+Prisma)│  │
    │  └──────────────────┘  │
    │           │             │
    │  ┌────────▼─────────┐  │
    │  │ Retrieval (FAISS)│  │
    │  └──────────────────┘  │
    │           │             │
    │  ┌────────▼─────────┐  │
    │  │  LLM (Gemini)    │  │
    │  └──────────────────┘  │
    └─────────────────────────┘
         │              │
    ┌────▼────┐    ┌───▼────┐
    │PostgreSQL│    │ FAISS  │
    └──────────┘    └────────┘
```

## 🔐 Security Features

✅ Password hashing with bcrypt  
✅ JWT token-based authentication  
✅ SQL injection prevention (Prisma ORM)  
✅ Secure session management  
✅ Environment variable protection  
✅ Token expiration (24 hours default)

## ⚠️ Important Disclaimers

1. **Not Legal Advice**: This tool is for reference only. Always consult a qualified lawyer.
2. **API Costs**: Monitor Gemini API usage to avoid unexpected charges.
3. **Data Privacy**: User data stored securely but ensure proper database security.
4. **PDF Quality**: OCR or poorly formatted PDFs may have extraction issues.
5. **Accuracy**: AI can make mistakes. Always verify against original sources.

## 📝 Development Timeline

- ✅ Oct 15, 2025: Environment setup
- ✅ Oct 16, 2025: Basic Streamlit UI  
- ✅ Oct 22, 2025: Legal document collection
- ✅ Oct 23, 2025: PDF extraction script
- ✅ Oct 24, 2025: Data processing
- ✅ Oct 27, 2025: Prisma + JWT integration
- ✅ Oct 29, 2025: Complete system deployment

## 🤝 Contributing

This is an educational project. Improvements welcome:
- Better PDF parsing
- Enhanced retrieval algorithms
- UI/UX improvements
- Additional legal document sources

## 📄 License

Educational/Research project. Use responsibly and ethically.

## 📞 Support

For detailed setup instructions, see [SETUP_GUIDE.md](SETUP_GUIDE.md)

---

**Built with ❤️ for legal education and access to justice**
