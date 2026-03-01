import React, { useState, useEffect } from 'react';
import { useLanguage } from '../components/LanguageProvider';
import VoiceButton from '../components/common/VoiceButton';
import SchemeCard from '../components/common/SchemeCard';
import SchemeDetailsModal from '../components/features/SchemeDetailsModal';
import { initDatabase, getFeaturedSchemes, searchSchemes, getDbStats } from '../services/schemeData';
import { Scheme } from '../types';

const Home: React.FC = () => {
  const { t } = useLanguage();
  const [showSchemes, setShowSchemes] = useState(false);
  const [selectedScheme, setSelectedScheme] = useState<Scheme | null>(null);
  const [displaySchemes, setDisplaySchemes] = useState<Scheme[]>([]);
  const [loading, setLoading] = useState(true);
  const [dbStats, setDbStats] = useState({ total: 0, central: 0, state: 0 });
  const [searchQuery, setSearchQuery] = useState('');

  // Initialize database on component mount
  useEffect(() => {
    const init = async () => {
      try {
        setLoading(true);
        await initDatabase();

        // Get database statistics
        const stats = await getDbStats();
        setDbStats(stats);

        // Load featured schemes
        const featured = await getFeaturedSchemes(6);
        setDisplaySchemes(featured);

        console.log(`✅ Loaded ${featured.length} schemes from database (${stats.total} total)`);
      } catch (error) {
        console.error('Failed to initialize database:', error);
      } finally {
        setLoading(false);
      }
    };
    init();
  }, []);

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
    const scheme = displaySchemes.find(s => s.id === schemeId);
    if (scheme) {
      setSelectedScheme(scheme);
    }
  };

  const handleCloseModal = () => {
    setSelectedScheme(null);
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      // If empty search, reload featured schemes
      const featured = await getFeaturedSchemes(6);
      setDisplaySchemes(featured);
      return;
    }

    setLoading(true);
    try {
      const results = await searchSchemes(searchQuery, {}, 12);
      setDisplaySchemes(results);
      setShowSchemes(true);
    } catch (error) {
      console.error('Search failed:', error);
    } finally {
      setLoading(false);
    }
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
          {dbStats.total > 0 && (
            <p className="mt-3 text-sm text-primary font-semibold">
              {dbStats.total} schemes available ({dbStats.central} Central, {dbStats.state} State/UT)
            </p>
          )}
        </div>

        <VoiceButton
          onStartListening={handleStartListening}
          onStopListening={handleStopListening}
        />

        {/* Search Bar */}
        <div className="mt-8 w-full max-w-2xl">
          <div className="flex gap-2">
            <input
              type="text"
              placeholder="Search schemes (e.g., farmer, health, education)..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              className="flex-1 px-4 py-3 rounded-lg border-2 border-gray-300 focus:border-primary focus:outline-none text-lg"
            />
            <button
              onClick={handleSearch}
              className="btn-primary px-6"
              disabled={loading}
            >
              {loading ? 'Searching...' : 'Search'}
            </button>
          </div>
        </div>

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
      {(showSchemes || displaySchemes.length > 0) && (
        <section className="py-12 px-4 bg-surface">
          <div className="container mx-auto max-w-6xl">
            <h2 className="text-3xl font-bold text-center mb-8">
              {searchQuery ? `Search Results (${displaySchemes.length})` : t('eligibleSchemes')}
            </h2>

            {loading ? (
              <div className="text-center py-12">
                <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
                <p className="mt-4 text-text-secondary">Loading schemes...</p>
              </div>
            ) : displaySchemes.length === 0 ? (
              <div className="text-center py-12">
                <p className="text-xl text-text-secondary">
                  {searchQuery ? 'No schemes found matching your search. Try different keywords.' : 'Loading schemes...'}
                </p>
              </div>
            ) : (
              <>
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
                {!searchQuery && dbStats.total > displaySchemes.length && (
                  <div className="text-center mt-8">
                    <p className="text-text-secondary mb-4">
                      Showing {displaySchemes.length} of {dbStats.total} schemes
                    </p>
                    <button
                      className="btn-primary"
                      onClick={() => setSearchQuery(' ')}
                    >
                      Browse All Schemes
                    </button>
                  </div>
                )}
              </>
            )}
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
