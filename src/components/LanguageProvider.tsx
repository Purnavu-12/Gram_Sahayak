import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import enTranslations from '../i18n/en.json';
import hiTranslations from '../i18n/hi.json';
import taTranslations from '../i18n/ta.json';
import teTranslations from '../i18n/te.json';
import knTranslations from '../i18n/kn.json';
import bnTranslations from '../i18n/bn.json';
import mrTranslations from '../i18n/mr.json';
import guTranslations from '../i18n/gu.json';

export type Language = 'en' | 'hi' | 'ta' | 'te' | 'kn' | 'bn' | 'mr' | 'gu';

export interface LanguageMeta {
  code: Language;
  nativeName: string;
  englishName: string;
  flag: string;
}

export const SUPPORTED_LANGUAGES: LanguageMeta[] = [
  { code: 'en', nativeName: 'English', englishName: 'English', flag: '🇬🇧' },
  { code: 'hi', nativeName: 'हिन्दी', englishName: 'Hindi', flag: '🇮🇳' },
  { code: 'ta', nativeName: 'தமிழ்', englishName: 'Tamil', flag: '🇮🇳' },
  { code: 'te', nativeName: 'తెలుగు', englishName: 'Telugu', flag: '🇮🇳' },
  { code: 'kn', nativeName: 'ಕನ್ನಡ', englishName: 'Kannada', flag: '🇮🇳' },
  { code: 'bn', nativeName: 'বাংলা', englishName: 'Bengali', flag: '🇮🇳' },
  { code: 'mr', nativeName: 'मराठी', englishName: 'Marathi', flag: '🇮🇳' },
  { code: 'gu', nativeName: 'ગુજરાતી', englishName: 'Gujarati', flag: '🇮🇳' },
];

interface LanguageContextType {
  language: Language;
  setLanguage: (lang: Language) => void;
  t: (key: string) => string;
  hasChosenLanguage: boolean;
  setHasChosenLanguage: (v: boolean) => void;
}

const LanguageContext = createContext<LanguageContextType | undefined>(undefined);

const translations: Record<Language, Record<string, unknown>> = {
  en: enTranslations,
  hi: hiTranslations,
  ta: taTranslations,
  te: teTranslations,
  kn: knTranslations,
  bn: bnTranslations,
  mr: mrTranslations,
  gu: guTranslations,
};

const STORAGE_KEY = 'gram-sahayak-lang';

export const LanguageProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const saved = (typeof window !== 'undefined' ? localStorage.getItem(STORAGE_KEY) : null) as Language | null;
  const [language, setLanguageState] = useState<Language>(saved && translations[saved] ? saved : 'en');
  const [hasChosenLanguage, setHasChosenLanguage] = useState<boolean>(!!saved);

  const setLanguage = (lang: Language) => {
    setLanguageState(lang);
    localStorage.setItem(STORAGE_KEY, lang);
    setHasChosenLanguage(true);
  };

  // Sync if localStorage already had a value
  useEffect(() => {
    if (saved && translations[saved]) {
      setLanguageState(saved);
      setHasChosenLanguage(true);
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const t = (key: string): string => {
    const keys = key.split('.');
    let value: unknown = translations[language];

    for (const k of keys) {
      value = (value as Record<string, unknown>)?.[k];
    }

    // Fallback to English
    if (typeof value !== 'string') {
      let fallback: unknown = translations.en;
      for (const k of keys) {
        fallback = (fallback as Record<string, unknown>)?.[k];
      }
      return typeof fallback === 'string' ? fallback : key;
    }

    return value;
  };

  return (
    <LanguageContext.Provider value={{ language, setLanguage, t, hasChosenLanguage, setHasChosenLanguage }}>
      {children}
    </LanguageContext.Provider>
  );
};

export const useLanguage = () => {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error('useLanguage must be used within LanguageProvider');
  }
  return context;
};
