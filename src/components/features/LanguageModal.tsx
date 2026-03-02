import React from 'react';
import { useLanguage, SUPPORTED_LANGUAGES, type Language } from '../LanguageProvider';

const LanguageModal: React.FC = () => {
  const { hasChosenLanguage, setLanguage } = useLanguage();

  if (hasChosenLanguage) return null;

  const handleSelect = (code: Language) => {
    setLanguage(code);
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-background/95 backdrop-blur-xl">
      {/* Decorative gradient orbs */}
      <div className="absolute top-1/4 left-1/4 w-72 h-72 bg-primary/20 rounded-full blur-3xl animate-pulse" />
      <div className="absolute bottom-1/4 right-1/4 w-72 h-72 bg-secondary/20 rounded-full blur-3xl animate-pulse delay-700" />

      <div className="relative w-full max-w-lg mx-4 text-center">
        {/* Logo */}
        <div className="mb-6">
          <div className="w-20 h-20 mx-auto rounded-2xl bg-gradient-to-br from-primary to-secondary flex items-center justify-center shadow-glow mb-4">
            <span className="text-4xl">🌾</span>
          </div>
          <h1 className="text-3xl font-bold text-text-primary mb-1">Gram Sahayak</h1>
          <p className="text-text-secondary text-sm">Choose your preferred language</p>
          <p className="text-text-tertiary text-xs mt-1">अपनी भाषा चुनें</p>
        </div>

        {/* Language grid */}
        <div className="grid grid-cols-2 gap-3 mb-6">
          {SUPPORTED_LANGUAGES.map((lang) => (
            <button
              key={lang.code}
              onClick={() => handleSelect(lang.code)}
              className="group relative flex flex-col items-center justify-center gap-1 py-5 px-4 rounded-2xl
                         bg-surface-glass backdrop-blur-sm border border-border-light
                         hover:border-primary/50 hover:bg-primary/10 hover:shadow-glow
                         transition-all duration-300 active:scale-95"
            >
              <span className="text-lg font-bold text-text-primary group-hover:text-primary transition-colors">
                {lang.nativeName}
              </span>
              <span className="text-xs text-text-tertiary">
                {lang.englishName}
              </span>
            </button>
          ))}
        </div>

        <p className="text-text-tertiary text-xs">
          You can change this anytime from the header
        </p>
      </div>
    </div>
  );
};

export default LanguageModal;
