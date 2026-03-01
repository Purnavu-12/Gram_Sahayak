import React from 'react';
import { useLanguage } from '../LanguageProvider';

const Header: React.FC = () => {
  const { language, setLanguage } = useLanguage();

  return (
    <header className="relative bg-gradient-to-r from-primary via-primary-dark to-secondary text-white shadow-large">
      <div className="absolute inset-0 bg-gradient-to-r from-primary/90 to-transparent opacity-50"></div>
      <div className="container mx-auto px-4 py-5 relative z-10">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="w-12 h-12 bg-white/20 backdrop-blur-sm rounded-2xl flex items-center justify-center shadow-medium transform hover:scale-110 transition-transform duration-300">
              <span className="text-3xl">🌾</span>
            </div>
            <div>
              <h1 className="text-2xl md:text-3xl font-bold tracking-tight">
                {language === 'hi' ? 'ग्राम सहायक' : 'Gram Sahayak'}
              </h1>
              <p className="text-sm md:text-base opacity-90 font-medium">
                {language === 'hi' ? 'सरकारी योजना सहायक' : 'Government Scheme Assistant'}
              </p>
            </div>
          </div>

          <button
            onClick={() => setLanguage(language === 'en' ? 'hi' : 'en')}
            className="bg-white/20 backdrop-blur-sm hover:bg-white/30 text-white font-semibold text-sm py-2.5 px-5 rounded-xl transition-all duration-300 border border-white/30 hover:border-white/50 shadow-medium hover:shadow-large transform hover:scale-105"
            aria-label="Switch Language"
          >
            {language === 'en' ? '🇮🇳 हिंदी' : '🇬🇧 English'}
          </button>
        </div>
      </div>
    </header>
  );
};

export default Header;
