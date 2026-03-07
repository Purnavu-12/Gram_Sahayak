<div align="center">

# 🌾 Gram Sahayak (ग्राम सहायक)

### _Rural Digital Assistance Platform for Government Schemes_

[![Frontend](https://img.shields.io/badge/Frontend-Vercel-000000?style=for-the-badge&logo=vercel&logoColor=white)](https://vercel.com)
[![Backend](https://img.shields.io/badge/Backend-AWS%20EC2-FF9900?style=for-the-badge&logo=amazonec2&logoColor=white)](https://aws.amazon.com/ec2/)
[![React](https://img.shields.io/badge/React-19-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.9-3178C6?style=for-the-badge&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-3.4-06B6D4?style=for-the-badge&logo=tailwindcss&logoColor=white)](https://tailwindcss.com)
[![License](https://img.shields.io/badge/License-ISC-green?style=for-the-badge)](LICENSE)

**Gram Sahayak** is a voice-first web application that helps rural Indian citizens discover and understand **700+ government welfare schemes** through natural voice conversation. Designed for low-literacy users with large text, icons, and multilingual support across **8 Indian languages**.

[Report Bug](https://github.com/Purnavu-12/Gram_Sahayak/issues) · [Request Feature](https://github.com/Purnavu-12/Gram_Sahayak/issues)

</div>

---

## ✨ Key Features

- 🎙️ **Voice-First Interface** — Speak naturally in Hindi or English via LiveKit-powered voice agent
- 📊 **700+ Government Schemes** — Real database sourced from myscheme.gov.in with full-text search
- 🔍 **Smart Search & Filtering** — Keyword search across name, ministry, tags, etc. plus filters for state, category, and level
- 🤖 **AI-Powered Matching** — Google Gemini recommends relevant schemes based on user needs
- 🌐 **8 Languages** — English, Hindi, Bengali, Gujarati, Kannada, Marathi, Tamil, Telugu
- 📱 **Mobile-First** — Optimized for 320px+ screens and low-end Android devices
- ♿ **Accessible UI** — Large fonts (16px+), icon + text labels, WCAG AA contrast

---

## 🏗️ Architecture

| Layer | Platform | What it runs |
|-------|----------|-------------|
| **Frontend** | Vercel | React 19 + TypeScript + Vite + Tailwind CSS |
| **Backend** | AWS EC2 | Python token server (port 8081) + LiveKit voice agent |
| **Database** | AWS EC2 | SQLite with FTS5 (700+ schemes) |
| **Voice** | LiveKit Cloud | Real-time WebRTC (STT / TTS) |
| **LLM** | Google Gemini | Natural language understanding |

**Flow:** User → Vercel (React SPA) → `/api` proxy → AWS EC2 (token server + voice agent + SQLite)

---

## 🛠️ Tech Stack

**Frontend:** React 19 · TypeScript 5.9 · Vite 7 · Tailwind CSS 3.4 · LiveKit Client

**Backend:** Python 3.10+ · LiveKit Agents · Google Gemini · SQLite 3 (FTS5) · DuckDuckGo Search

**Deployment:** Vercel (frontend) · AWS EC2 (backend) · LiveKit Cloud (voice)

---

## 🚀 Getting Started

### Prerequisites

- **Frontend:** Node.js 18+, npm
- **Backend:** Python 3.10+, pip

### Frontend

```bash
git clone https://github.com/Purnavu-12/Gram_Sahayak.git
cd Gram_Sahayak
npm install
npm run dev          # → http://localhost:3000
```

| Command | Description |
|---------|-------------|
| `npm run dev` | Start dev server |
| `npm run build` | Type-check + production build |
| `npm run preview` | Preview production build |
| `npm run lint` | TypeScript type checking |

### Backend (AWS EC2)

```bash
pip install -r requirements.txt
cp .env.example .env   # fill in your keys
python token_server.py  # Terminal 1 — API + JWT tokens
python agent.py         # Terminal 2 — Voice agent
```

---

## 🌐 Deployment

### Frontend — Vercel

1. Connect the GitHub repo to [Vercel](https://vercel.com)
2. Vercel auto-detects the Vite framework
3. API calls are proxied to EC2 via serverless functions in `api/`

### Backend — AWS EC2

1. Launch an EC2 instance (Ubuntu 22.04, `t3.medium` recommended)
2. Install Python 3.10+, clone the repo, install dependencies
3. Configure `.env` with LiveKit + Google AI credentials
4. Run `token_server.py` and `agent.py` (use systemd for production)

---

## 🔑 Environment Variables

Copy `.env.example` → `.env` and fill in your values:

| Variable | Required | Description |
|----------|----------|-------------|
| `LIVEKIT_URL` | Yes | LiveKit server WebSocket URL |
| `LIVEKIT_API_KEY` | Yes | LiveKit API key |
| `LIVEKIT_API_SECRET` | Yes | LiveKit API secret |
| `GOOGLE_API_KEY` | Yes | Google AI API key (Gemini) |
| `TOKEN_SERVER_PORT` | No | Token server port (default: `8081`) |
| `DB_PATH` | No | SQLite database path (default: `./schemes.db`) |
| `EC2_BACKEND_URL` | Yes (Vercel) | Base URL of the AWS EC2 backend for `/api/*` proxy requests (set in your Vercel project Environment Variables to avoid using the hardcoded fallback URL). |

---

## 📁 Project Structure

```
Gram_Sahayak/
├── src/                     # React frontend
│   ├── components/          #   UI components (common, features, layout)
│   ├── pages/               #   Page components (Home)
│   ├── services/            #   API & voice services
│   ├── i18n/                #   Translation files (8 languages)
│   ├── types/               #   TypeScript types
│   └── styles/              #   Global CSS
├── api/                     # Vercel serverless proxy
├── agent.py                 # LiveKit voice agent
├── token_server.py          # JWT token server + scheme API
├── scheme_lookup.py         # SQLite query interface
├── schemes_agent.py         # Database sync agent
├── schemes.db               # SQLite database (700+ schemes)
├── vercel.json              # Vercel deployment config
├── .env.example             # Environment variables template
└── requirements.txt         # Python dependencies
```

---

## 🤝 Contributing

1. Fork the repo
2. Create a feature branch: `git checkout -b feat/your-feature`
3. Commit changes: `git commit -m 'feat: add your feature'`
4. Push and open a Pull Request

---

## 📄 License

ISC License

---

## 🙏 Acknowledgments

[myscheme.gov.in](https://www.myscheme.gov.in/) · [LiveKit](https://livekit.io) · [Google Gemini](https://ai.google.dev/) · [DuckDuckGo](https://duckduckgo.com) · [Vercel](https://vercel.com) · [AWS](https://aws.amazon.com)

---

<div align="center">

**Made with ❤️ for Rural India 🇮🇳 | ग्रामीण भारत के लिए बनाया गया**

</div>
