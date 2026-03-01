import React, { useState, useEffect } from 'react';
import { useLanguage } from '../components/LanguageProvider';
import VoiceButton from '../components/common/VoiceButton';
import SchemeCard from '../components/common/SchemeCard';
import SchemeDetailsModal from '../components/features/SchemeDetailsModal';
import { initDatabase, getFeaturedSchemes, searchSchemes, getDbStats, getAllCategories, getAllStates } from '../services/schemeData';
import { Scheme } from '../types';

const ITEMS_PER_PAGE = 12;

const Home: React.FC = () => {
  const { t } = useLanguage();
  const [showSchemes, setShowSchemes] = useState(false);
  const [selectedScheme, setSelectedScheme] = useState<Scheme | null>(null);
  const [displaySchemes, setDisplaySchemes] = useState<Scheme[]>([]);
  const [loading, setLoading] = useState(true);
  const [dbStats, setDbStats] = useState({ total: 0, central: 0, state: 0 });
  const [searchQuery, setSearchQuery] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [hasMore, setHasMore] = useState(false);
  const [allSchemes, setAllSchemes] = useState<Scheme[]>([]);

  // Filters
  const [selectedState, setSelectedState] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('');
  const [selectedLevel, setSelectedLevel] = useState('');
  const [availableStates, setAvailableStates] = useState<string[]>([]);
  const [availableCategories, setAvailableCategories] = useState<string[]>([]);

  // Initialize database on component mount
  useEffect(() => {
    const init = async () => {
      try {
        setLoading(true);
        await initDatabase();

        // Get database statistics
        const stats = await getDbStats();
        setDbStats(stats);

        // Load filter options
        const [states, categories] = await Promise.all([
          getAllStates(),
          getAllCategories()
        ]);
        setAvailableStates(states);
        setAvailableCategories(categories);

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
    setLoading(true);
    setCurrentPage(1);

    try {
      const filters: { state?: string; category?: string; level?: string } = {};
      if (selectedState) filters.state = selectedState;
      if (selectedCategory) filters.category = selectedCategory;
      if (selectedLevel) filters.level = selectedLevel;

      const limit = 100; // Get more results for pagination
      const results = await searchSchemes(searchQuery || '', filters, limit);
      setAllSchemes(results);
      setDisplaySchemes(results.slice(0, ITEMS_PER_PAGE));
      setHasMore(results.length > ITEMS_PER_PAGE);
      setShowSchemes(true);
    } catch (error) {
      console.error('Search failed:', error);
      setAllSchemes([]);
      setDisplaySchemes([]);
      setHasMore(false);
    } finally {
      setLoading(false);
    }
  };

  const handleLoadMore = () => {
    const nextPage = currentPage + 1;
    const startIndex = nextPage * ITEMS_PER_PAGE;
    const endIndex = startIndex + ITEMS_PER_PAGE;
    const newSchemes = allSchemes.slice(0, endIndex);

    setDisplaySchemes(newSchemes);
    setCurrentPage(nextPage);
    setHasMore(endIndex < allSchemes.length);
  };

  const handleClearFilters = () => {
    setSelectedState('');
    setSelectedCategory('');
    setSelectedLevel('');
    setSearchQuery('');
  };

  // Trigger search when filters change
  useEffect(() => {
    if (selectedState || selectedCategory || selectedLevel) {
      handleSearch();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedState, selectedCategory, selectedLevel]);

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
            {t('description')}
          </p>
          {dbStats.total > 0 && (
            <p className="mt-3 text-sm text-primary font-semibold">
              {dbStats.total} {t('schemesAvailable')} ({dbStats.central} {t('central')}, {dbStats.state} {t('stateUT')})
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
              placeholder={t('searchPlaceholder')}
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
              {loading ? t('searching') : t('search')}
            </button>
          </div>

          {/* Filters */}
          <div className="mt-4 space-y-3">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {/* State Filter */}
              <select
                value={selectedState}
                onChange={(e) => setSelectedState(e.target.value)}
                className="px-4 py-2 rounded-lg border-2 border-gray-300 focus:border-primary focus:outline-none"
              >
                <option value="">{t('allStates')}</option>
                {availableStates.map(state => (
                  <option key={state} value={state}>{state}</option>
                ))}
              </select>

              {/* Category Filter */}
              <select
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
                className="px-4 py-2 rounded-lg border-2 border-gray-300 focus:border-primary focus:outline-none"
              >
                <option value="">{t('allCategories')}</option>
                {availableCategories.map(category => (
                  <option key={category} value={category}>{category}</option>
                ))}
              </select>

              {/* Level Filter */}
              <select
                value={selectedLevel}
                onChange={(e) => setSelectedLevel(e.target.value)}
                className="px-4 py-2 rounded-lg border-2 border-gray-300 focus:border-primary focus:outline-none"
              >
                <option value="">{t('allLevels')}</option>
                <option value="Central">{t('centralSchemes')}</option>
                <option value="State">{t('stateSchemes')}</option>
              </select>
            </div>

            {/* Clear Filters Button */}
            {(selectedState || selectedCategory || selectedLevel || searchQuery) && (
              <button
                onClick={handleClearFilters}
                className="text-sm text-primary hover:text-primary-dark underline"
              >
                {t('clearFilters')}
              </button>
            )}
          </div>
        </div>

        {/* Features */}
        <div className="mt-16 grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl">
          <div className="card text-center">
            <div className="text-4xl mb-3">🎤</div>
            <h3 className="font-semibold mb-2">{t('voiceFirst')}</h3>
            <p className="text-sm text-text-secondary">
              {t('voiceFirstDesc')}
            </p>
          </div>
          <div className="card text-center">
            <div className="text-4xl mb-3">🎯</div>
            <h3 className="font-semibold mb-2">{t('smartMatching')}</h3>
            <p className="text-sm text-text-secondary">
              {t('smartMatchingDesc')}
            </p>
          </div>
          <div className="card text-center">
            <div className="text-4xl mb-3">📱</div>
            <h3 className="font-semibold mb-2">{t('simpleAccessible')}</h3>
            <p className="text-sm text-text-secondary">
              {t('simpleAccessibleDesc')}
            </p>
          </div>
        </div>
      </section>

      {/* Schemes Section */}
      {(showSchemes || displaySchemes.length > 0) && (
        <section className="py-12 px-4 bg-surface">
          <div className="container mx-auto max-w-6xl">
            <h2 className="text-3xl font-bold text-center mb-8">
              {searchQuery ? `${t('searchResults')} (${displaySchemes.length})` : t('eligibleSchemes')}
            </h2>

            {loading ? (
              <div className="text-center py-12">
                <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
                <p className="mt-4 text-text-secondary">{t('loadingSchemes')}</p>
              </div>
            ) : displaySchemes.length === 0 ? (
              <div className="text-center py-12">
                <p className="text-xl text-text-secondary">
                  {searchQuery ? t('noSchemesFound') : t('loadingSchemes')}
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
                {hasMore && (
                  <div className="text-center mt-8">
                    <p className="text-text-secondary mb-4">
                      {t('showing')} {displaySchemes.length} {t('of')} {allSchemes.length}
                    </p>
                    <button
                      className="btn-primary px-8 py-3"
                      onClick={handleLoadMore}
                    >
                      {t('loadMore')}
                    </button>
                  </div>
                )}
                {!hasMore && allSchemes.length > ITEMS_PER_PAGE && (
                  <div className="text-center mt-8">
                    <p className="text-text-secondary">
                      {t('noMoreSchemes')}
                    </p>
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
