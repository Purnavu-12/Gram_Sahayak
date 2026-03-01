# Changelog

All notable changes to Gram Sahayak will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **SQLite Database Integration**: Integrated schemes.db (700+ schemes) directly into React frontend using sql.js
- **Real Scheme Data**: Replaced mock data with real government schemes from myscheme.gov.in
- **Search Functionality**: Added full-text search across scheme names, descriptions, categories, and tags
- **Database Statistics**: Display total schemes count (Central vs State/UT) on homepage
- **Environment Configuration**: Added .env.example with all required environment variables
- **Comprehensive Documentation**: Completely rewritten README with setup instructions, architecture overview, and deployment guide
- **Complete i18n Coverage**: Added 25+ new translation keys for Hindi and English
- **Python Environment Support**: Database sync agent now uses environment variables for API keys

### Changed
- **Home Page**: Updated to load schemes from SQLite database instead of mock data
- **Search UI**: Enhanced search bar with real-time database queries
- **Scheme Display**: Shows 6 featured schemes by default, expandable to browse all
- **Translation Keys**: All hardcoded UI strings now use i18n translation system
- **Bundle Size**: Optimized to 253KB (82KB gzipped) for production build

### Security
- **Fixed**: Moved hardcoded myscheme.gov.in API key from source code to environment variable
- **Fixed**: Added .env to .gitignore to prevent accidental commits of secrets
- **Added**: Input sanitization for database queries using parameterized statements

### Documentation
- Comprehensive README with architecture overview
- Voice agent setup guide with LiveKit configuration
- Database schema documentation
- Environment variables reference
- Development and deployment guides
- i18n implementation guide

### Technical Details
- **Frontend**: React 19 + TypeScript + Vite + Tailwind CSS + sql.js
- **Database**: SQLite 3 with FTS5 full-text search (5.3MB, 700+ schemes)
- **Backend**: LiveKit voice agent with Google Gemini AI (separate component)
- **Languages**: Full Hindi and English support

## [0.1.0] - 2024-03-01 (Initial Prototype)

### Added
- Initial React + TypeScript project setup with Vite
- Basic UI components (VoiceButton, SchemeCard, SchemeDetailsModal)
- Layout components (Header, Footer)
- Mock scheme data (6 sample schemes)
- Bilingual support infrastructure (LanguageProvider)
- Tailwind CSS design system
- Basic i18n for Hindi and English
- Type definitions for schemes, user profiles, and conversations
- Responsive mobile-first design (320px+)

### Python Backend
- LiveKit voice agent implementation (agent.py)
- Scheme lookup service with FTS5 search (scheme_lookup.py)
- myscheme.gov.in sync agent (schemes_agent.py)
- Conversation memory management
- DuckDuckGo web search integration
- Google Gemini AI for natural language understanding

## Project Status

### Completed ✅
- Core frontend UI and navigation
- Real database integration (700+ schemes)
- Full-text search functionality
- Complete i18n coverage (Hindi + English)
- Security fixes (API key protection)
- Comprehensive documentation
- Production build optimization

### In Progress 🚧
- LiveKit voice integration in frontend
- User profile collection flow
- Scheme recommendation algorithm

### Planned 📋
- Eligibility verification
- Application guidance
- Saved schemes/favorites
- Performance optimization
- Accessibility audit (WCAG AA)
- CI/CD pipeline
- Production deployment

---

**Note**: This project aims to help rural Indian citizens discover government schemes through voice-first interaction.
