import React, { useState } from 'react';
import { useLanguage } from '../components/LanguageProvider';
import VoiceButton from '../components/common/VoiceButton';
import SchemeCard from '../components/common/SchemeCard';
import SchemeDetailsModal from '../components/features/SchemeDetailsModal';
import { mockSchemes, getSchemeById } from '../services/schemeData';
import { Scheme } from '../types';

const Home: React.FC = () => {
  const { t } = useLanguage();
  const [showSchemes, setShowSchemes] = useState(false);
  const [selectedScheme, setSelectedScheme] = useState<Scheme | null>(null);
  const displaySchemes = mockSchemes.slice(0, 6);

  const handleStartListening = () => {
    console.log('Started listening...');
    setTimeout(() => {
      setShowSchemes(true);
    }, 2000);
  };

  const handleStopListening = () => {
    console.log('Stopped listening...');
  };

  const handleSchemeSelect = (schemeId: string) => {
    const scheme = getSchemeById(schemeId);
    if (scheme) {
      setSelectedScheme(scheme);
    }
  };

  const handleCloseModal = () => {
    setSelectedScheme(null);
  };

  return (
    <div className="min-h-screen flex flex-col">
      {/* Hero Section */}
      <section className="flex-1 flex flex-col items-center justify-center py-12 px-4">
        <div className="text-center mb-12 max-w-3xl">
          <h1 className="text-4xl md:text-5xl font-bold text-primary mb-4">
            {t('welcome')}
          </h1>
          <p className="text-xl md:text-2xl text-text-secondary">
            {t('welcomeSubtitle')}
          </p>
          <p className="mt-4 text-text-secondary max-w-2xl mx-auto">
            Discover government schemes you're eligible for through simple voice conversation.
            No reading, no forms - just speak naturally in your language.
          </p>
        </div>

        <VoiceButton
          onStartListening={handleStartListening}
          onStopListening={handleStopListening}
        />

        {/* Features */}
        <div className="mt-16 grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl">
          <div className="card text-center">
            <div className="text-4xl mb-3">🎤</div>
            <h3 className="font-semibold mb-2">Voice First</h3>
            <p className="text-sm text-text-secondary">
              Speak naturally in Hindi or English
            </p>
          </div>
          <div className="card text-center">
            <div className="text-4xl mb-3">🎯</div>
            <h3 className="font-semibold mb-2">Smart Matching</h3>
            <p className="text-sm text-text-secondary">
              Find schemes that match your profile
            </p>
          </div>
          <div className="card text-center">
            <div className="text-4xl mb-3">📱</div>
            <h3 className="font-semibold mb-2">Simple & Accessible</h3>
            <p className="text-sm text-text-secondary">
              Built for low-literacy users
            </p>
          </div>
        </div>
      </section>

      {/* Schemes Section */}
      {showSchemes && (
        <section className="py-12 px-4 bg-surface">
          <div className="container mx-auto max-w-6xl">
            <h2 className="text-3xl font-bold text-center mb-8">
              {t('eligibleSchemes')}
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {displaySchemes.map((scheme) => (
                <SchemeCard
                  key={scheme.id}
                  scheme={scheme}
                  onSelect={handleSchemeSelect}
                  isEligible={true}
                />
              ))}
            </div>
            <div className="text-center mt-8">
              <button className="btn-primary">
                View All {mockSchemes.length} Schemes
              </button>
            </div>
          </div>
        </section>
      )}

      {/* Scheme Details Modal */}
      {selectedScheme && (
        <SchemeDetailsModal
          scheme={selectedScheme}
          onClose={handleCloseModal}
        />
      )}
    </div>
  );
};

export default Home;
