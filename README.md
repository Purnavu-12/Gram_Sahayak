# Gram Sahayak (ग्राम सहायक)

**Rural Digital Assistance Platform for Government Schemes**

Gram Sahayak is a voice-first web application that helps low-literacy rural Indian citizens discover and understand government welfare schemes through natural conversation. Built with simplicity and accessibility at its core.

## 🌟 Features

- **Voice-First Interface**: Speak naturally in Hindi or English via LiveKit voice agent
- **Real Scheme Database**: Access to 700+ government schemes from myscheme.gov.in
- **Smart Search**: Full-text search across scheme names, descriptions, categories, and tags
- **Smart Scheme Matching**: AI-powered matching based on user profile
- **Simple & Accessible**: Designed for low-literacy users with large text and icons
- **Mobile-First**: Optimized for low-end Android phones (320px+ screens)
- **Bilingual**: Full support for Hindi and English
- **Offline-Ready**: Works with cached data when internet is unavailable

## 🏗️ Architecture

Gram Sahayak consists of two main components:

### 1. React Frontend (Web Application)
- **Purpose**: User interface for browsing and searching schemes
- **Tech**: React 19 + TypeScript + Vite + Tailwind CSS
- **Database**: SQLite (schemes.db) loaded directly in browser via sql.js
- **Features**: Search, filter, scheme details, bilingual support

### 2. Python Backend (Voice Agent)
- **Purpose**: Voice-based conversational interface using LiveKit
- **Tech**: LiveKit Agents + Google Gemini AI + DuckDuckGo Search
- **Features**: Voice recognition, natural conversation, web scraping, scheme recommendations
- **Note**: Runs separately from React frontend

## 🚀 Quick Start

### Prerequisites

- **For Frontend**:
  - Node.js 18+ and npm
  - Modern web browser

- **For Voice Agent** (optional):
  - Python 3.7+
  - LiveKit server (Cloud or self-hosted)
  - Google AI API key

### Frontend Installation

```bash
# Clone the repository
git clone https://github.com/Purnavu-12/Gram_Sahayak.git
cd Gram_Sahayak

# Install dependencies
npm install

# Start development server
npm run dev
```

The application will be available at `http://localhost:3000`

### Frontend Build for Production

```bash
npm run build
npm run preview
```

## 🎙️ Voice Agent Setup (Optional)

The voice agent runs separately and uses LiveKit for real-time voice communication.

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy `.env.example` to `.env` and fill in your API keys:

```bash
cp .env.example .env
```

Edit `.env`:

```bash
# MyScheme.gov.in API Key
MYSCHEME_API_KEY=your_api_key_here

# LiveKit Configuration
LIVEKIT_URL=wss://your-livekit-server.com
LIVEKIT_API_KEY=your_livekit_api_key
LIVEKIT_API_SECRET=your_livekit_api_secret

# Google AI API Key (for Gemini)
GOOGLE_API_KEY=your_google_api_key
```

### 3. Initialize/Update Schemes Database

The database syncs schemes from myscheme.gov.in API:

```bash
# Run once to sync database
python schemes_agent.py

# Run continuously (syncs every hour)
python schemes_agent.py --daemon

# View database statistics
python schemes_agent.py --stats
```

### 4. Run the Voice Agent

```bash
python agent.py
```

The voice agent will:
- Connect to your LiveKit server
- Use Google Gemini for natural language understanding
- Search schemes in the local SQLite database
- Use DuckDuckGo to fetch latest scheme details from the web
- Maintain conversation context per user session

## 🛠️ Tech Stack

### Frontend
- **Framework**: React 19 with TypeScript
- **Build Tool**: Vite 7
- **Styling**: Tailwind CSS 3
- **Database**: sql.js (SQLite in browser)
- **Voice Integration**: LiveKit Client (for voice UI)
- **State Management**: React Context API
- **Storage**: Browser LocalStorage & SessionStorage

### Backend (Voice Agent)
- **Framework**: LiveKit Agents
- **LLM**: Google Gemini (via LiveKit Google plugin)
- **Voice**: Text-to-Speech and Speech-to-Text via LiveKit
- **Database**: SQLite 3 with FTS5 (Full-Text Search)
- **Web Search**: DuckDuckGo Search API (ddgs)
- **Conversation Memory**: In-memory SQLite per session
- **Noise Cancellation**: LiveKit BVC/Telephony plugins

### Data Source
- **Primary**: myscheme.gov.in API (700+ schemes)
- **Sync**: Automated hourly sync via schemes_agent.py
- **Fallback**: DuckDuckGo web search for latest updates

## 📁 Project Structure

```
Gram_Sahayak/
├── src/                          # React frontend source
│   ├── components/               # Reusable UI components
│   │   ├── common/               # Buttons, Cards, etc.
│   │   ├── layout/               # Header, Footer
│   │   └── features/             # Feature-specific components
│   ├── pages/                    # Page components
│   ├── services/                 # Business logic & API calls
│   │   ├── schemeData.ts         # Scheme service wrapper
│   │   └── schemeDatabase.ts     # SQLite database service
│   ├── types/                    # TypeScript type definitions
│   ├── i18n/                     # Hindi & English translations
│   ├── styles/                   # Global styles
│   └── main.tsx                  # Entry point
├── public/                       # Static assets
│   └── schemes.db                # SQLite database (5.3MB, 700+ schemes)
├── agent.py                      # LiveKit voice agent
├── scheme_lookup.py              # Database query interface
├── schemes_agent.py              # myscheme.gov.in sync agent
├── schemes.db                    # SQLite database (used by Python backend)
├── .kiro/specs/                  # Design documents & requirements
├── .env.example                  # Environment variables template
├── requirements.txt              # Python dependencies
└── package.json                  # Node.js dependencies
```

## 🎨 Design Principles

### Color Palette
- **Primary Green**: `#2E7D32` - Trust, nature (suits rural theme)
- **Secondary Saffron**: `#FF6F00` - Energy, warmth (Indian flag)
- **Background**: `#FAFAF7` - Off-white, easy on eyes
- **Surface**: `#FFFFFF`
- **Text Primary**: `#1A1A1A`
- **Text Secondary**: `#555555`
- **Success**: `#388E3C`
- **Error**: `#D32F2F`
- **Warning**: `#F57C00`

### Typography
- **Font Family**: Noto Sans (Hindi support), Inter (English)
- **Minimum Font Size**: 16px (for low-literacy users)
- **Large Touch Targets**: 44x44px minimum for mobile
- **Font Weights**: 400 (regular), 600 (semibold), 700 (bold)

### Responsive Breakpoints
- **Mobile**: 320px - 640px (default/primary)
- **Tablet**: 640px - 1024px
- **Desktop**: 1024px+

## 🌐 Internationalization (i18n)

The app supports Hindi and English with a language toggle in the header.

### Adding New Translations

1. Add keys to `src/i18n/en.json`:
```json
{
  "newKey": "English text"
}
```

2. Add corresponding Hindi translation to `src/i18n/hi.json`:
```json
{
  "newKey": "हिंदी पाठ"
}
```

3. Use in components:
```tsx
const { t } = useLanguage();
return <p>{t('newKey')}</p>;
```

## 📊 Database Schema

### schemes table
- `id` - Elastic ID from API
- `slug` - URL-friendly identifier (used as primary key in frontend)
- `scheme_name` - Full scheme name
- `scheme_short_title` - Short title
- `brief_description` - Brief description
- `nodal_ministry_name` - Ministry responsible
- `level` - Central / State
- `scheme_for` - Individual / Organization
- `beneficiary_states` - JSON array of states
- `scheme_categories` - JSON array of categories
- `tags` - JSON array of tags
- `url` - Official myscheme.gov.in URL
- `first_seen_at`, `last_seen_at`, `updated_at` - Timestamps

### schemes_fts table
- FTS5 virtual table for full-text search
- Automatically synchronized via triggers

## 🔒 Security

- **API Keys**: Never commit API keys to Git. Use `.env` file (gitignored)
- **Environment Variables**: All sensitive config in `.env` (see `.env.example`)
- **CORS**: Configure properly for production deployment
- **Input Validation**: User inputs sanitized before database queries
- **SQL Injection**: Protected by parameterized queries in both Python and JavaScript

## 🧪 Development

### Linting
```bash
npm run lint  # TypeScript type checking
```

### Building
```bash
npm run build  # Builds to /dist directory
```

### Testing Voice Agent
```bash
# View database stats
python schemes_agent.py --stats

# Test scheme lookup
python -c "import scheme_lookup; print(scheme_lookup.search_schemes('farmer'))"
```

## 🗺️ Roadmap

### Phase 1: Core Features ✅
- [x] Project setup
- [x] Basic UI components
- [x] Landing page with voice button
- [x] Real scheme database integration (700+ schemes)
- [x] Search and filter functionality
- [x] Complete i18n coverage

### Phase 2: Voice Integration (In Progress)
- [x] Python voice agent with LiveKit
- [x] Speech-to-text and text-to-speech
- [x] Conversation manager with context
- [ ] Frontend LiveKit integration
- [ ] User profile collection flow

### Phase 3: Enhanced Features
- [ ] Scheme recommendation algorithm
- [ ] Eligibility verification
- [ ] Application guidance
- [ ] Saved schemes/favorites
- [ ] User authentication

### Phase 4: Production Ready
- [ ] Performance optimization
- [ ] Full accessibility audit (WCAG AA)
- [ ] Security hardening
- [ ] CI/CD pipeline
- [ ] Deployment (Vercel/Netlify frontend + Railway/Render backend)

## 📖 Documentation

- [Requirements](/.kiro/specs/gram-sahayak-prototype/requirements.md) - Detailed functional requirements
- [Design Document](/.kiro/specs/gram-sahayak-prototype/design.md) - Architecture and design decisions
- [Agent Instructions](/AGENTS.md) - Guidelines for AI agents/developers
- [Environment Variables](/.env.example) - Configuration template

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feat/amazing-feature`)
3. Make your changes
4. Run linting: `npm run lint`
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feat/amazing-feature`)
7. Open a Pull Request

### Code Standards

- Use TypeScript for type safety
- Follow mobile-first responsive design
- Ensure accessibility (WCAG AA minimum)
- Add i18n for all user-facing text (both Hindi and English)
- Keep bundle size under 200KB for initial load (for rural internet)
- Use existing Tailwind classes before adding custom CSS
- Add comments for complex logic
- Test on mobile viewport (minimum 320px width)

## 🐛 Known Issues

1. **Database Loading**: First load may take 2-3 seconds (5.3MB database download)
2. **Voice Agent**: Requires separate LiveKit server setup (not included)
3. **Hindi Translations**: Some scheme data from API is English-only

## 📝 Environment Variables Reference

See `.env.example` for a complete list. Key variables:

- `MYSCHEME_API_KEY` - API key for myscheme.gov.in (get from their website)
- `LIVEKIT_URL` - Your LiveKit server URL
- `LIVEKIT_API_KEY` - LiveKit API key
- `LIVEKIT_API_SECRET` - LiveKit API secret
- `GOOGLE_API_KEY` - Google AI API key for Gemini
- `DB_PATH` - Path to SQLite database (default: ./schemes.db)
- `SYNC_INTERVAL_HOURS` - How often to sync database (default: 1)

## 📄 License

ISC License

## 👥 Authors

Built with ❤️ for rural India

---

## 🙏 Acknowledgments

- **myscheme.gov.in** - For providing the government schemes API
- **LiveKit** - For real-time voice communication infrastructure
- **Google Gemini** - For natural language understanding
- **DuckDuckGo** - For web search capabilities

---

**Note**: The voice agent component is functional but requires external LiveKit server setup. The React frontend works standalone with the embedded schemes database.

## 📞 Support

For issues or questions:
- GitHub Issues: https://github.com/Purnavu-12/Gram_Sahayak/issues
- Documentation: See `/docs` folder

---

**Made for rural India 🇮🇳 | ग्रामीण भारत के लिए बनाया गया**
