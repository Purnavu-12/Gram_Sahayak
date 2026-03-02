import React, { useState } from 'react';
import { useLanguage, SUPPORTED_LANGUAGES } from '../LanguageProvider';

const Header: React.FC = () => {
  const { language, setLanguage, t } = useLanguage();
  const [showDropdown, setShowDropdown] = useState(false);
  const currentLang = SUPPORTED_LANGUAGES.find(l => l.code === language)!;

  return (
    <header className="sticky top-0 z-50 bg-background/70 backdrop-blur-2xl border-b border-border">
      <div className="container mx-auto px-4 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary to-secondary flex items-center justify-center shadow-glow">
              <span className="text-xl">🌾</span>
            </div>
            <div>
              <h1 className="text-xl font-bold text-text-primary leading-tight tracking-tight">
                {t('header.title')}
              </h1>
              <p className="text-xs text-text-tertiary font-medium">
                {t('header.subtitle')}
              </p>
            </div>
          </div>

          {/* Language dropdown */}
          <div className="relative">
            <button
              onClick={() => setShowDropdown(!showDropdown)}
              className="flex items-center gap-2 text-sm font-semibold px-4 py-2 rounded-lg
                         bg-surface-glass backdrop-blur-sm text-text-primary
                         hover:bg-primary/10 border border-border-light
                         transition-all duration-200 hover:border-primary/30"
              aria-label="Switch Language"
            >
              {currentLang.nativeName}
              <svg className={`w-3.5 h-3.5 transition-transform ${showDropdown ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>

            {showDropdown && (
              <>
                <div className="fixed inset-0 z-40" onClick={() => setShowDropdown(false)} />
                <div className="absolute right-0 top-full mt-2 z-50 w-48 py-1 rounded-xl
                                bg-surface border border-border-light shadow-xl backdrop-blur-xl
                                animate-fade-in">
                  {SUPPORTED_LANGUAGES.map((lang) => (
                    <button
                      key={lang.code}
                      onClick={() => { setLanguage(lang.code); setShowDropdown(false); }}
                      className={`w-full text-left px-4 py-2.5 text-sm flex items-center justify-between
                                  hover:bg-primary/10 transition-colors
                                  ${language === lang.code ? 'text-primary font-semibold' : 'text-text-primary'}`}
                    >
                      <span>{lang.nativeName}</span>
                      <span className="text-xs text-text-tertiary">{lang.englishName}</span>
                    </button>
                  ))}
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;
