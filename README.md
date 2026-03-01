# Gram Sahayak (ग्राम सहायक)

**Rural Digital Assistance Platform for Government Schemes**

Gram Sahayak is a voice-first web application that helps low-literacy rural Indian citizens discover and understand government welfare schemes through natural conversation. Built with simplicity and accessibility at its core.

## 🌟 Features

- **Voice-First Interface**: Speak naturally in Hindi or English
- **Smart Scheme Matching**: AI-powered matching based on user profile
- **Simple & Accessible**: Designed for low-literacy users with large text and icons
- **Mobile-First**: Optimized for low-end Android phones (320px+ screens)
- **Bilingual**: Full support for Hindi and English
- **Offline-Ready**: Works with cached data when internet is unavailable

## 🚀 Quick Start

### Prerequisites

- Node.js 18+ and npm
- Modern web browser

### Installation

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

### Build for Production

```bash
npm run build
npm run preview
```

## 🛠️ Tech Stack

- **Frontend Framework**: React 19 with TypeScript
- **Build Tool**: Vite 7
- **Styling**: Tailwind CSS 3
- **Voice Integration**: LiveKit Client (planned)
- **State Management**: React Context API
- **Storage**: Browser LocalStorage & SessionStorage

## 📁 Project Structure

```
Gram_Sahayak/
├── src/
│   ├── components/       # Reusable UI components
│   │   ├── common/       # Buttons, Cards, etc.
│   │   ├── layout/       # Header, Footer
│   │   └── features/     # Feature-specific components
│   ├── pages/            # Page components
│   ├── services/         # Business logic & API calls
│   ├── types/            # TypeScript type definitions
│   ├── i18n/             # Hindi & English translations
│   ├── styles/           # Global styles
│   └── main.tsx          # Entry point
├── .kiro/specs/          # Design documents & requirements
└── public/               # Static assets
```

## 🎨 Design Principles

### Color Palette
- **Primary Green**: `#2E7D32` - Trust, nature
- **Secondary Saffron**: `#FF6F00` - Energy, warmth
- **Background**: `#FAFAF7` - Off-white, easy on eyes
- **Text Primary**: `#1A1A1A`
- **Success**: `#388E3C`
- **Error**: `#D32F2F`

### Typography
- **Font Family**: Noto Sans (Hindi support), Inter
- **Minimum Font Size**: 16px (for low-literacy users)
- **Large Touch Targets**: 44x44px minimum

## 🗺️ Roadmap

### Phase 1: UI Prototype (Current)
- [x] Project setup
- [x] Basic UI components
- [x] Landing page with voice button
- [ ] Scheme data integration
- [ ] Profile collection flow

### Phase 2: Voice Integration
- [ ] LiveKit integration
- [ ] Speech-to-text
- [ ] Text-to-speech
- [ ] Conversation manager

### Phase 3: Backend Services
- [ ] Scheme database
- [ ] User profile management
- [ ] Scheme matching algorithm
- [ ] Application tracking

### Phase 4: Production Ready
- [ ] Performance optimization
- [ ] Accessibility audit
- [ ] Security hardening
- [ ] Deployment

## 📖 Documentation

- [Requirements](/.kiro/specs/gram-sahayak-prototype/requirements.md)
- [Design Document](/.kiro/specs/gram-sahayak-prototype/design.md)
- [Implementation Tasks](/.kiro/specs/gram-sahayak-prototype/tasks.md)
- [Agent Instructions](/AGENTS.md)

## 🤝 Contributing

This is currently a prototype project. Contributions are welcome!

1. Fork the repository
2. Create a feature branch (`git checkout -b feat/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feat/amazing-feature`)
5. Open a Pull Request

### Code Standards

- Use TypeScript for type safety
- Follow mobile-first responsive design
- Ensure accessibility (WCAG AA minimum)
- Add i18n for all user-facing text
- Keep bundle size under 200KB for initial load

## 📄 License

ISC License

## 👥 Authors

Built with ❤️ for rural India

---

**Note**: This is a prototype version. Voice capabilities and backend services are under development.
