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

[Live Demo](#-deployment) · [Report Bug](https://github.com/Purnavu-12/Gram_Sahayak/issues) · [Request Feature](https://github.com/Purnavu-12/Gram_Sahayak/issues)

</div>

---

## 📑 Table of Contents

- [About the Project](#-about-the-project)
- [Key Features](#-key-features)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Getting Started](#-getting-started)
  - [Prerequisites](#prerequisites)
  - [Frontend Setup](#1-frontend-setup)
  - [Backend Setup (AWS EC2)](#2-backend-setup-aws-ec2)
- [Deployment](#-deployment)
  - [Frontend — Vercel](#frontend--vercel)
  - [Backend — AWS EC2](#backend--aws-ec2)
- [API Reference](#-api-reference)
- [Project Structure](#-project-structure)
- [Database Schema](#-database-schema)
- [Internationalization (i18n)](#-internationalization-i18n)
- [Environment Variables](#-environment-variables)
- [Design System](#-design-system)
- [Security](#-security)
- [Contributing](#-contributing)
- [License](#-license)
- [Acknowledgments](#-acknowledgments)

---

## 📖 About the Project

India has hundreds of government welfare schemes, but most rural citizens are unaware of the benefits they are eligible for. **Gram Sahayak** bridges this gap by providing:

- A **voice-first interface** that lets users speak naturally in Hindi or English
- Access to a **comprehensive database of 700+ government schemes** sourced from [myscheme.gov.in](https://www.myscheme.gov.in/)
- **AI-powered scheme matching** using Google Gemini for intelligent recommendations
- A **mobile-first, accessible design** optimized for low-end Android phones and slow rural internet connections

> 💡 The name "ग्राम सहायक" means "Village Helper" — the platform acts as a digital assistant for every rural citizen.

---

## ✨ Key Features

| Feature | Description |
|---------|-------------|
| 🎙️ **Voice-First Interface** | Speak naturally in Hindi or English via LiveKit-powered voice agent |
| 📊 **700+ Government Schemes** | Real database sourced from myscheme.gov.in with full-text search (FTS5) |
| 🔍 **Smart Search & Filtering** | Search by name, category, state, ministry, or tags with instant results |
| 🤖 **AI-Powered Matching** | Google Gemini understands user needs and recommends relevant schemes |
| 🌐 **8 Languages Supported** | English, Hindi, Bengali, Gujarati, Kannada, Marathi, Tamil, Telugu |
| 📱 **Mobile-First Design** | Optimized for 320px+ screens and low-end Android devices |
| ♿ **Accessible UI** | Large fonts (16px+), icon + text labels, WCAG AA contrast ratios |
| 🌍 **Web Search Fallback** | DuckDuckGo integration for real-time scheme details (no API key needed) |

---

## 🏗️ Architecture

Gram Sahayak follows a **decoupled architecture** with the frontend hosted on **Vercel** and the backend services running on **AWS EC2**.

```
┌─────────────────────────────────────────────────────────────────────┐
│                          USERS (Rural India)                        │
│                    Mobile / Desktop Browsers                        │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────────┐
│                     FRONTEND (Vercel)                                │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │  React 19 + TypeScript + Vite 7 + Tailwind CSS                │  │
│  │                                                                │  │
│  │  ┌──────────┐ ┌──────────────┐ ┌────────────┐ ┌────────────┐ │  │
│  │  │  Home    │ │ SchemeCard   │ │ VoiceButton│ │ Language   │ │  │
│  │  │  Page    │ │ Component    │ │ Component  │ │ Modal      │ │  │
│  │  └──────────┘ └──────────────┘ └────────────┘ └────────────┘ │  │
│  │                                                                │  │
│  │  ┌──────────────────┐  ┌──────────────────┐                   │  │
│  │  │ LanguageProvider │  │ LiveKit Client   │                   │  │
│  │  │ (i18n Context)   │  │ (Voice UI)       │                   │  │
│  │  └──────────────────┘  └──────────────────┘                   │  │
│  └────────────────────────────────────────────────────────────────┘  │
│  Vercel Serverless Functions: /api/[...path].js (proxy)             │
└──────────────────────────┬──────────────────────────────────────────┘
                           │  HTTPS API Calls
                           ▼
┌──────────────────────────────────────────────────────────────────────┐
│                     BACKEND (AWS EC2)                                │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │  Token Server (Python — port 8081)                            │  │
│  │  ┌───────────┐ ┌──────────┐ ┌─────────┐ ┌──────────────────┐│  │
│  │  │ /api/token│ │/api/search│ │/api/stats│ │/api/featured    ││  │
│  │  │ JWT Auth  │ │ FTS5     │ │ DB Stats │ │ Popular Schemes ││  │
│  │  └───────────┘ └──────────┘ └─────────┘ └──────────────────┘│  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │  Voice Agent (Python — LiveKit)                               │  │
│  │  ┌──────────────┐ ┌──────────────┐ ┌────────────────────────┐│  │
│  │  │ Google Gemini│ │ LiveKit STT  │ │ DuckDuckGo Search     ││  │
│  │  │ (LLM)       │ │ / TTS        │ │ (Web Fallback)        ││  │
│  │  └──────────────┘ └──────────────┘ └────────────────────────┘│  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │  SQLite Database (schemes.db)                                 │  │
│  │  700+ schemes │ FTS5 Full-Text Search │ Auto-sync support     │  │
│  └────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────┘
```

### How It Works

1. **User visits the app** → Vercel serves the React frontend (fast CDN delivery)
2. **User searches schemes** → Frontend calls `/api/search` → Vercel proxy → AWS EC2 token server → SQLite FTS5 query → Results returned
3. **User activates voice** → Frontend requests JWT token → Connects to LiveKit server → Voice agent (on EC2) processes speech → Google Gemini generates response → TTS plays answer
4. **Scheme database sync** → `schemes_agent.py` on EC2 periodically syncs from myscheme.gov.in API

---

## 🛠️ Tech Stack

### Frontend

| Technology | Purpose | Version |
|-----------|---------|---------|
| [React](https://react.dev) | UI Framework | 19.x |
| [TypeScript](https://www.typescriptlang.org/) | Type Safety | 5.9 |
| [Vite](https://vitejs.dev) | Build Tool & Dev Server | 7.x |
| [Tailwind CSS](https://tailwindcss.com) | Utility-First Styling | 3.4 |
| [LiveKit Client](https://livekit.io) | Real-Time Voice UI | 2.17 |
| [PostCSS](https://postcss.org) | CSS Processing | 8.5 |

### Backend (AWS EC2)

| Technology | Purpose | Details |
|-----------|---------|---------|
| [Python](https://python.org) | Runtime | 3.10+ |
| [LiveKit Agents](https://docs.livekit.io/agents/) | Voice Agent Framework | Real-time voice processing |
| [Google Gemini](https://ai.google.dev/) | LLM for NLU | Natural language understanding |
| [SQLite 3](https://www.sqlite.org/) | Database | 700+ schemes with FTS5 |
| [DuckDuckGo Search](https://pypi.org/project/duckduckgo-search/) | Web Search Fallback | Real-time scheme lookup |
| [LiveKit Plugins](https://docs.livekit.io/agents/plugins/) | STT / TTS / Noise Cancellation | Silero, Google, BVC |

### Deployment

| Component | Platform | Details |
|-----------|----------|---------|
| **Frontend** | [Vercel](https://vercel.com) | CDN-backed, auto-deploy from Git |
| **Backend** | [AWS EC2](https://aws.amazon.com/ec2/) | Token server + Voice agent + Database |
| **Voice Server** | [LiveKit Cloud](https://livekit.io) | Real-time WebRTC infrastructure |

---

## 🚀 Getting Started

### Prerequisites

| Requirement | For | Version |
|------------|-----|---------|
| **Node.js** | Frontend | 18+ |
| **npm** | Frontend | 9+ |
| **Python** | Backend | 3.10+ |
| **pip** | Backend | Latest |
| **Git** | Version Control | Latest |

### 1. Frontend Setup

```bash
# Clone the repository
git clone https://github.com/Purnavu-12/Gram_Sahayak.git
cd Gram_Sahayak

# Install dependencies
npm install

# Start development server (http://localhost:3000)
npm run dev
```

#### Available Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Start Vite dev server on port 3000 |
| `npm run build` | Type-check with `tsc` and build to `dist/` |
| `npm run preview` | Preview production build locally |
| `npm run lint` | Run TypeScript type checking |

### 2. Backend Setup (AWS EC2)

#### Step 1 — Install Python Dependencies

```bash
pip install -r requirements.txt
```

#### Step 2 — Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```bash
# LiveKit Configuration
LIVEKIT_URL=wss://your-livekit-server.com
LIVEKIT_API_KEY=your_livekit_api_key
LIVEKIT_API_SECRET=your_livekit_api_secret

# Google AI Configuration (for Gemini LLM)
GOOGLE_API_KEY=your_google_api_key

# Token Server
TOKEN_SERVER_PORT=8081

# Database
DB_PATH=./schemes.db
```

#### Step 3 — Initialize Schemes Database (Optional)

A pre-built `schemes.db` with 700+ schemes is included. To sync the latest data:

```bash
# One-time sync from myscheme.gov.in API
python schemes_agent.py

# Continuous sync (every hour)
python schemes_agent.py --daemon

# View database statistics
python schemes_agent.py --stats
```

#### Step 4 — Start Backend Services

```bash
# Terminal 1 — Token Server (JWT authentication + Scheme API)
python token_server.py

# Terminal 2 — Voice Agent (LiveKit real-time voice)
python agent.py
```

> **Note:** The voice agent uses DuckDuckGo web search for real-time scheme details — no myscheme.gov.in API key is required for regular operation.

---

## 🌐 Deployment

### Frontend — Vercel

The React frontend is deployed on **Vercel** for fast global CDN delivery.

#### Automatic Deployment

1. Connect the GitHub repository to [Vercel](https://vercel.com)
2. Vercel auto-detects the Vite framework and configures the build

#### Vercel Configuration (`vercel.json`)

```json
{
  "framework": "vite",
  "installCommand": "npm install",
  "buildCommand": "npm run build",
  "outputDirectory": "dist",
  "rewrites": [
    { "source": "/api/:path*", "destination": "/api/:path*" }
  ]
}
```

- **Build Output:** `dist/` directory
- **API Routing:** Serverless functions in `api/` proxy requests to the EC2 backend
- **Ignored Files:** Python backend files are excluded via `.vercelignore`

### Backend — AWS EC2

The Python backend (token server + voice agent + database) runs on an **AWS EC2** instance.

#### EC2 Setup Guide

**1. Launch an EC2 Instance**

- **AMI:** Ubuntu 22.04 LTS (or Amazon Linux 2023)
- **Instance Type:** `t3.medium` or higher (recommended for voice processing)
- **Storage:** 20 GB+ (for database and dependencies)
- **Security Group:** Open ports `8081` (token server) and `443` (HTTPS)

**2. SSH into the Instance and Install Dependencies**

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install Python 3.10+
sudo apt install python3 python3-pip python3-venv -y

# Clone the repository
git clone https://github.com/Purnavu-12/Gram_Sahayak.git
cd Gram_Sahayak

# Create a virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

**3. Configure Environment Variables**

```bash
cp .env.example .env
nano .env
# Fill in your LiveKit, Google AI, and database credentials
```

**4. Run Services with systemd (Production)**

Create a systemd service for the token server:

```bash
sudo nano /etc/systemd/system/gram-sahayak-token.service
```

```ini
[Unit]
Description=Gram Sahayak Token Server
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/Gram_Sahayak
Environment=PATH=/home/ubuntu/Gram_Sahayak/venv/bin
ExecStart=/home/ubuntu/Gram_Sahayak/venv/bin/python token_server.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Create a systemd service for the voice agent:

```bash
sudo nano /etc/systemd/system/gram-sahayak-agent.service
```

```ini
[Unit]
Description=Gram Sahayak Voice Agent
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/Gram_Sahayak
Environment=PATH=/home/ubuntu/Gram_Sahayak/venv/bin
ExecStart=/home/ubuntu/Gram_Sahayak/venv/bin/python agent.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Enable and start the services:

```bash
sudo systemctl daemon-reload
sudo systemctl enable gram-sahayak-token gram-sahayak-agent
sudo systemctl start gram-sahayak-token gram-sahayak-agent

# Check status
sudo systemctl status gram-sahayak-token
sudo systemctl status gram-sahayak-agent
```

**5. Set Up Nginx Reverse Proxy (Recommended)**

```bash
sudo apt install nginx -y
sudo nano /etc/nginx/sites-available/gram-sahayak
```

```nginx
server {
    listen 80;
    server_name your-ec2-public-ip-or-domain;

    location /api/ {
        proxy_pass http://127.0.0.1:8081;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/gram-sahayak /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

> **Tip:** Use [Let's Encrypt](https://letsencrypt.org/) with Certbot to enable HTTPS on your EC2 instance for production.

---

## 📡 API Reference

The token server exposes the following REST API endpoints (running on port `8081`):

| Method | Endpoint | Description | Parameters |
|--------|----------|-------------|------------|
| `GET` | `/api/health` | Health check & system status | — |
| `GET` | `/api/token` | Generate LiveKit JWT token | `room` (optional), `name` (optional) |
| `GET` | `/api/search` | Search government schemes | `q`, `state`, `category`, `level`, `limit` |
| `GET` | `/api/featured` | Get featured/popular schemes | `limit` (default: 6) |
| `GET` | `/api/stats` | Database statistics | — |
| `GET` | `/api/categories` | List all scheme categories | — |
| `GET` | `/api/states` | List all beneficiary states | — |
| `GET` | `/api/scheme` | Get scheme details by slug | `slug` (required) |

#### Example Requests

```bash
# Health check
curl http://localhost:8081/api/health

# Search for education schemes
curl "http://localhost:8081/api/search?q=education&limit=10"

# Get schemes for Maharashtra
curl "http://localhost:8081/api/search?state=Maharashtra"

# Get featured schemes
curl http://localhost:8081/api/featured

# Get specific scheme details
curl "http://localhost:8081/api/scheme?slug=pm-kisan"

# Get a LiveKit token
curl "http://localhost:8081/api/token?room=gram-sahayak&name=user1"
```

#### Example Response — `/api/search`

```json
{
  "results": [
    {
      "id": "abc123",
      "slug": "pm-kisan",
      "name": "PM-KISAN Samman Nidhi",
      "shortTitle": "PM-KISAN",
      "description": "Income support of ₹6,000 per year to farmer families",
      "ministry": "Ministry of Agriculture & Farmers Welfare",
      "level": "Central",
      "categories": ["Agriculture", "Financial Assistance"],
      "states": ["All States"],
      "tags": ["farmer", "income", "agriculture"],
      "url": "https://www.myscheme.gov.in/schemes/pm-kisan"
    }
  ],
  "webResults": [],
  "total": 1,
  "query": "farmer"
}
```

---

## 📁 Project Structure

```
Gram_Sahayak/
│
├── 📂 src/                            # React frontend source code
│   ├── 📂 components/
│   │   ├── 📂 common/                 # Shared UI components
│   │   │   ├── SchemeCard.tsx          #   Scheme display card
│   │   │   └── VoiceButton.tsx         #   Voice interaction button
│   │   ├── 📂 features/               # Feature-specific components
│   │   │   ├── LanguageModal.tsx       #   Language selector (8 languages)
│   │   │   └── SchemeDetailsModal.tsx  #   Full scheme details view
│   │   ├── 📂 layout/                 # Layout components
│   │   │   ├── Header.tsx              #   App header with navigation
│   │   │   └── Footer.tsx              #   App footer
│   │   ├── ErrorBoundary.tsx          # React error boundary
│   │   └── LanguageProvider.tsx       # i18n context provider
│   ├── 📂 pages/
│   │   └── Home.tsx                   # Main landing page
│   ├── 📂 services/
│   │   ├── schemeData.ts              # Scheme data service
│   │   └── livekitService.ts          # LiveKit voice integration
│   ├── 📂 i18n/                       # Translation files
│   │   ├── en.json                    #   English
│   │   ├── hi.json                    #   Hindi (हिंदी)
│   │   ├── bn.json                    #   Bengali (বাংলা)
│   │   ├── gu.json                    #   Gujarati (ગુજરાતી)
│   │   ├── kn.json                    #   Kannada (ಕನ್ನಡ)
│   │   ├── mr.json                    #   Marathi (मराठी)
│   │   ├── ta.json                    #   Tamil (தமிழ்)
│   │   └── te.json                    #   Telugu (తెలుగు)
│   ├── 📂 types/
│   │   └── index.ts                   # TypeScript type definitions
│   ├── 📂 styles/
│   │   └── index.css                  # Global CSS & Tailwind imports
│   ├── main.tsx                       # React entry point
│   └── vite-env.d.ts                  # Vite type declarations
│
├── 📂 api/
│   └── [...path].js                   # Vercel serverless API proxy
│
├── 🐍 agent.py                        # LiveKit voice agent (Gemini + STT/TTS)
├── 🐍 token_server.py                 # JWT token server + Scheme search API
├── 🐍 scheme_lookup.py                # SQLite database query interface
├── 🐍 schemes_agent.py                # myscheme.gov.in data sync agent
├── 🗄️ schemes.db                      # SQLite database (700+ schemes)
│
├── 📄 index.html                      # HTML entry point
├── 📄 package.json                    # Node.js dependencies & scripts
├── 📄 requirements.txt                # Python dependencies
├── 📄 vite.config.ts                  # Vite build configuration
├── 📄 tailwind.config.cjs             # Tailwind CSS configuration
├── 📄 postcss.config.cjs              # PostCSS configuration
├── 📄 tsconfig.json                   # TypeScript configuration
├── 📄 tsconfig.node.json              # TypeScript config (build tools)
├── 📄 vercel.json                     # Vercel deployment configuration
├── 📄 .env.example                    # Environment variables template
├── 📄 .vercelignore                   # Files excluded from Vercel deploy
└── 📄 .gitignore                      # Git ignore rules
```

---

## 📊 Database Schema

The application uses a **SQLite** database (`schemes.db`) with **Full-Text Search (FTS5)** for fast scheme lookups.

### `schemes` Table

| Column | Type | Description |
|--------|------|-------------|
| `id` | TEXT | Elastic ID from myscheme.gov.in API |
| `slug` | TEXT | URL-friendly identifier (primary key in frontend) |
| `scheme_name` | TEXT | Full official scheme name |
| `scheme_short_title` | TEXT | Short title / abbreviation |
| `brief_description` | TEXT | Brief description of the scheme |
| `nodal_ministry_name` | TEXT | Responsible ministry or department |
| `level` | TEXT | `Central` or `State` |
| `scheme_for` | TEXT | `Individual` or `Organization` |
| `beneficiary_states` | TEXT | JSON array of applicable states |
| `scheme_categories` | TEXT | JSON array of categories |
| `tags` | TEXT | JSON array of searchable tags |
| `url` | TEXT | Official myscheme.gov.in URL |
| `first_seen_at` | TEXT | Timestamp — first synced |
| `last_seen_at` | TEXT | Timestamp — last seen in API |
| `updated_at` | TEXT | Timestamp — last updated |

### `schemes_fts` Table

- **FTS5 virtual table** for full-text search across `scheme_name`, `brief_description`, `tags`, and `scheme_categories`
- Automatically synchronized with the `schemes` table via triggers
- Supports prefix queries, phrase matching, and Boolean operators

---

## 🌐 Internationalization (i18n)

Gram Sahayak supports **8 Indian languages** with easy extensibility.

| Code | Language | Script |
|------|----------|--------|
| `en` | English | Latin |
| `hi` | Hindi | देवनागरी |
| `bn` | Bengali | বাংলা |
| `gu` | Gujarati | ગુજરાતી |
| `kn` | Kannada | ಕನ್ನಡ |
| `mr` | Marathi | देवनागरी |
| `ta` | Tamil | தமிழ் |
| `te` | Telugu | తెలుగు |

### Adding Translations

**1.** Add the key to each language file in `src/i18n/`:

```json
// src/i18n/en.json
{ "welcomeMessage": "Welcome to Gram Sahayak" }

// src/i18n/hi.json
{ "welcomeMessage": "ग्राम सहायक में आपका स्वागत है" }
```

**2.** Use in React components:

```tsx
import { useLanguage } from '../components/LanguageProvider';

function MyComponent() {
  const { t } = useLanguage();
  return <h1>{t('welcomeMessage')}</h1>;
}
```

---

## 🔑 Environment Variables

All sensitive configuration is managed via environment variables. Copy `.env.example` to `.env` and fill in your values.

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `LIVEKIT_URL` | Yes | — | LiveKit server WebSocket URL (`wss://...`) |
| `LIVEKIT_API_KEY` | Yes | — | LiveKit API key for authentication |
| `LIVEKIT_API_SECRET` | Yes | — | LiveKit API secret for JWT signing |
| `GOOGLE_API_KEY` | Yes | — | Google AI API key for Gemini LLM |
| `TOKEN_SERVER_PORT` | No | `8081` | Port for the token server |
| `DB_PATH` | No | `./schemes.db` | Path to SQLite database file |
| `MYSCHEME_API_KEY` | No | — | API key for myscheme.gov.in sync (optional) |
| `SYNC_INTERVAL_HOURS` | No | `1` | Database sync interval in hours |

> **Security:** The `.env` file is listed in `.gitignore` and is never committed to version control.

---

## 🎨 Design System

### Color Palette

| Token | Hex | Usage |
|-------|-----|-------|
| **Primary Green** | `#2E7D32` | Trust, nature — suits rural theme |
| **Secondary Saffron** | `#FF6F00` | Energy, warmth — Indian flag inspired |
| **Background** | `#FAFAF7` | Off-white, easy on eyes |
| **Surface** | `#FFFFFF` | Cards, modals |
| **Text Primary** | `#1A1A1A` | Headings, body text |
| **Text Secondary** | `#555555` | Captions, labels |
| **Success** | `#388E3C` | Positive actions |
| **Error** | `#D32F2F` | Error states |
| **Warning** | `#F57C00` | Warning indicators |

### Typography

| Element | Size | Weight | Font |
|---------|------|--------|------|
| Heading 1 | 2.5rem | 700 | Noto Sans / Inter |
| Heading 2 | 2rem | 600 | Noto Sans / Inter |
| Heading 3 | 1.5rem | 600 | Noto Sans / Inter |
| Body | 1rem (16px min) | 400 | Noto Sans / Inter |
| Small | 0.875rem | 400 | Noto Sans / Inter |

> **Noto Sans** is used for Hindi and regional language scripts. **Inter** is used for English text.

### Responsive Breakpoints

| Breakpoint | Width | Target Devices |
|------------|-------|----------------|
| **Mobile** | 320px – 640px | Low-end Android phones (primary) |
| **Tablet** | 640px – 1024px | Tablets, landscape phones |
| **Desktop** | 1024px+ | Laptops, desktops |

---

## 🔒 Security

| Practice | Implementation |
|----------|---------------|
| **API Key Management** | All keys stored in `.env` (gitignored), never committed |
| **JWT Authentication** | LiveKit tokens are short-lived JWTs signed with API secret |
| **SQL Injection Protection** | Parameterized queries in both Python and TypeScript |
| **Input Validation** | User inputs sanitized before database queries |
| **CORS** | Configurable CORS headers on the token server |
| **HTTPS** | Vercel frontend served over HTTPS; EC2 via Nginx + Let's Encrypt |

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feat/amazing-feature`
3. **Make** your changes following the code standards below
4. **Lint** your code: `npm run lint`
5. **Build** to verify: `npm run build`
6. **Commit** your changes: `git commit -m 'feat: add amazing feature'`
7. **Push** to your branch: `git push origin feat/amazing-feature`
8. **Open** a Pull Request with a clear description

### Code Standards

- ✅ Use **TypeScript** for all frontend code
- ✅ Follow **mobile-first** responsive design (test at 320px)
- ✅ Ensure **accessibility** (WCAG AA, semantic HTML, aria labels)
- ✅ Add **i18n keys** for all user-facing text (Hindi + English minimum)
- ✅ Keep **bundle size < 200KB** initial load (for rural internet)
- ✅ Use **Tailwind CSS** utility classes before adding custom CSS
- ✅ Use **conventional commits** (`feat:`, `fix:`, `docs:`, `refactor:`)
- ✅ Always pair **icons with text labels** for primary actions

---

## 📄 License

This project is licensed under the **ISC License**. See the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [**myscheme.gov.in**](https://www.myscheme.gov.in/) — Government schemes database API
- [**LiveKit**](https://livekit.io) — Real-time voice communication infrastructure
- [**Google Gemini**](https://ai.google.dev/) — Large language model for natural conversation
- [**DuckDuckGo**](https://duckduckgo.com) — Web search fallback for scheme details
- [**Vercel**](https://vercel.com) — Frontend hosting and CDN
- [**AWS**](https://aws.amazon.com) — Backend cloud infrastructure

---

<div align="center">

**Made with ❤️ for Rural India 🇮🇳**

**ग्रामीण भारत के लिए बनाया गया**

[⬆ Back to Top](#-gram-sahayak-ग्राम-सहायक)

</div>
