import React from 'react';
import { useLanguage } from '../LanguageProvider';

const Header: React.FC = () => {
  const { language, setLanguage } = useLanguage();

  return (
    <header className="bg-primary text-white shadow-lg">
      <div className="container mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-secondary rounded-full flex items-center justify-center">
              <span className="text-2xl">🌾</span>
            </div>
            <div>
              <h1 className="text-xl md:text-2xl font-bold">
                {language === 'hi' ? 'ग्राम सहायक' : 'Gram Sahayak'}
              </h1>
              <p className="text-sm opacity-90">
                {language === 'hi' ? 'सरकारी योजना सहायक' : 'Government Scheme Assistant'}
              </p>
            </div>
          </div>

          <button
            onClick={() => setLanguage(language === 'en' ? 'hi' : 'en')}
            className="btn-secondary text-sm py-2 px-4"
            aria-label="Switch Language"
          >
            {language === 'en' ? 'हिंदी' : 'English'}
          </button>
        </div>
      </div>
    </header>
  );
};

export default Header;
