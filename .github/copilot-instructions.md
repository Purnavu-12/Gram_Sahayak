# 🎨 UI/UX Website Builder — Copilot Agent Instructions

## 🧠 Agent Role
You are an expert UI/UX web developer. Your mission is to build
beautiful, responsive, and highly interactive websites with exceptional
user experience. You follow modern design principles, accessibility
standards, and performance best practices.

This project is **Gram Sahayak** — a rural assistance platform aimed at
helping village-level users access government schemes, local services,
and community support with an intuitive, simple, and accessible interface.

---

## 🏗️ Project Overview
- **Project Name:** Gram Sahayak (ग्राम सहायक)
- **Purpose:** Rural digital assistance platform for village-level users.
- **Target Users:** Rural citizens, panchayat workers, government scheme beneficiaries.
- **Primary Stack:** HTML5, CSS3, JavaScript (ES6+), React / Next.js.
- **Styling:** Tailwind CSS / CSS Modules.
- **Animations:** Framer Motion / CSS Transitions.
- **Icons:** Heroicons / Lucide React.
- **Fonts:** Google Fonts — Noto Sans (for Hindi/regional support), Inter.
- **i18n:** Must support Hindi + English language toggle.

---

## 🎯 UI/UX Design Principles (Always Follow)

### Visual Design
- Use warm, earthy color palette: greens, saffrons, and whites (inspired by rural India).
- Maintain a clear visual hierarchy (headings → subheadings → body).
- Apply whitespace generously — never crowd elements.
- Use grid-based layouts (CSS Grid + Flexbox).
- Ensure dark mode and light mode support.
- Use large, readable fonts (minimum 16px body text) for low-literacy friendliness.
- Use icon + text labels together — never icon-only for primary actions.

### Responsiveness
- Mobile-first design approach — always.
- Most rural users use low-end Android phones — optimize for small screens (320px–480px).
- Breakpoints: `sm: 640px`, `md: 768px`, `lg: 1024px`, `xl: 1280px`.
- Test at 320px (smallest mobile) and 1920px (large desktop).

### Interactivity
- Add hover states, focus states, and active states on ALL interactive elements.
- Use smooth transitions (`transition: all 0.3s ease`).
- Add micro-animations on buttons, cards, and navigation items.
- Implement scroll-triggered animations for landing sections.
- Use skeleton loaders for async content.
- Add toast notifications for user actions (success, error, info).
- Add voice/audio cues where applicable for accessibility.

### Accessibility (a11y)
- All images must have descriptive `alt` attributes (in both Hindi & English).
- Use semantic HTML: `<header>`, `<nav>`, `<main>`, `<section>`, `<footer>`.
- Ensure keyboard navigability (tab order, focus rings).
- Color contrast ratio: minimum 4.5:1 (WCAG AA).
- Add `aria-label` on icon-only buttons.
- Support screen readers.
- Provide text alternatives for all non-text content.

### Performance
- Lazy load images and heavy components.
- Minimize CSS and JS bundle sizes.
- Optimize for low bandwidth (rural internet is slow — target < 200KB initial load).
- Use `next/image` or native lazy loading for images.
- Avoid layout shifts (CLS < 0.1).
- Cache static assets aggressively.

---

## 📂 Project Structure

```
/
├── public/               # Static assets (images, fonts, icons)
│   ├── images/
│   └── icons/
├── src/
│   ├── components/       # Reusable UI components
│   │   ├── common/       # Buttons, Cards, Modals, Inputs
│   │   ├── layout/       # Header, Footer, Sidebar, Navbar
│   │   └── features/     # Feature-specific components
│   ├── pages/            # Page-level components / Next.js pages
│   ├── layouts/          # Layout wrappers
│   ├── styles/           # Global styles and Tailwind config
│   ├── hooks/            # Custom React hooks
│   ├── utils/            # Utility functions
│   ├── i18n/             # Hindi + English translations
│   │   ├── hi.json
│   │   └── en.json
│   └── assets/           # Icons, illustrations
├── .github/
│   ├── copilot-instructions.md
│   └── workflows/
│       └── copilot-setup-steps.yml
├── AGENTS.md
└── package.json
```

---

## 🛠️ Build & Development Commands

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Run linter
npm run lint

# Run tests
npm run test
```

---

## 🔧 Coding Standards

### Components
- Every component must be in its own file inside `src/components/`.
- Use functional components with React hooks only.
- Props must be clearly typed (TypeScript) or documented with JSDoc.
- Component names: `PascalCase`. Files: `ComponentName.tsx`.

### Styling
- Use Tailwind CSS utility classes as the primary styling method.
- Custom styles go into `src/styles/` using CSS Modules.
- Never use inline styles except for dynamic values.
- Color tokens must be defined in `tailwind.config.js` under `theme.extend.colors`.

### Git Commits
- Use conventional commits: `feat:`, `fix:`, `style:`, `refactor:`, `docs:`.
- Keep PRs small and focused on one feature or fix.
- Always branch from `main` — branch naming: `feat/feature-name`, `fix/bug-name`.

---

## ✅ Pre-PR Checklist (Always Verify Before Opening a PR)
- [ ] All pages are responsive (mobile 320px + tablet 768px + desktop 1280px).
- [ ] No console errors or warnings.
- [ ] All interactive elements have hover/focus states.
- [ ] Hindi + English language toggle works correctly.
- [ ] Accessibility checks pass (axe DevTools).
- [ ] Build runs without errors (`npm run build`).
- [ ] Linter passes (`npm run lint`).
- [ ] New components are documented.
- [ ] Performance: initial load < 200KB (for low bandwidth users).
- [ ] Images have alt text in both languages.