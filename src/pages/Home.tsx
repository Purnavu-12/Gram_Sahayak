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
      <section className="relative flex-1 flex flex-col items-center justify-center py-16 px-4 overflow-hidden">
        {/* Animated background gradient */}
        <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-secondary/5 to-background -z-10"></div>
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(99,102,241,0.1),transparent_50%)] -z-10"></div>

        <div className="text-center mb-12 max-w-4xl">
          <div className="inline-block mb-6">
            <span className="inline-block px-4 py-2 bg-primary/10 text-primary rounded-full text-sm font-semibold border border-primary/20 shadow-soft">
              🇮🇳 Empowering Rural India
            </span>
          </div>

          <h1 className="text-4xl md:text-6xl font-bold mb-6 leading-tight">
            <span className="gradient-text">{t('welcome')}</span>
          </h1>

          <p className="text-xl md:text-2xl text-text-secondary mb-6 font-medium">
            {t('welcomeSubtitle')}
          </p>

          <p className="text-base md:text-lg text-text-secondary max-w-2xl mx-auto leading-relaxed">
            {t('description')}
          </p>

          {dbStats.total > 0 && (
            <div className="mt-8 inline-flex items-center gap-6 bg-white rounded-2xl shadow-medium p-6 border border-border/50">
              <div className="text-center">
                <p className="text-3xl font-bold text-primary">{dbStats.total}</p>
                <p className="text-sm text-text-secondary mt-1">{t('schemesAvailable')}</p>
              </div>
              <div className="w-px h-12 bg-border"></div>
              <div className="text-center">
                <p className="text-2xl font-bold text-accent">{dbStats.central}</p>
                <p className="text-sm text-text-secondary mt-1">{t('central')}</p>
              </div>
              <div className="w-px h-12 bg-border"></div>
              <div className="text-center">
                <p className="text-2xl font-bold text-secondary">{dbStats.state}</p>
                <p className="text-sm text-text-secondary mt-1">{t('stateUT')}</p>
              </div>
            </div>
          )}
        </div>

        <VoiceButton
          onStartListening={handleStartListening}
          onStopListening={handleStopListening}
        />

        {/* Search Bar */}
        <div className="mt-10 w-full max-w-3xl">
          <div className="flex flex-col md:flex-row gap-3">
            <div className="relative flex-1">
              <input
                type="text"
                placeholder={t('searchPlaceholder')}
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                className="w-full px-6 py-4 rounded-xl border-2 border-border focus:border-primary focus:ring-4 focus:ring-primary/10 focus:outline-none text-lg shadow-soft transition-all duration-300 bg-white"
              />
              <svg className="absolute right-4 top-1/2 -translate-y-1/2 w-5 h-5 text-text-secondary pointer-events-none" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
            <button
              onClick={handleSearch}
              className="btn-primary px-8 md:px-10 whitespace-nowrap"
              disabled={loading}
            >
              {loading ? (
                <span className="flex items-center gap-2">
                  <svg className="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  {t('searching')}
                </span>
              ) : (
                <span className="flex items-center gap-2">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                  {t('search')}
                </span>
              )}
            </button>
          </div>

          {/* Filters */}
          <div className="mt-6 space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* State Filter */}
              <div className="relative">
                <select
                  value={selectedState}
                  onChange={(e) => setSelectedState(e.target.value)}
                  className="w-full px-4 py-3 rounded-xl border-2 border-border focus:border-primary focus:ring-4 focus:ring-primary/10 focus:outline-none appearance-none bg-white shadow-soft transition-all duration-300 cursor-pointer"
                >
                  <option value="">{t('allStates')}</option>
                  {availableStates.map(state => (
                    <option key={state} value={state}>{state}</option>
                  ))}
                </select>
                <svg className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-text-secondary pointer-events-none" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </div>

              {/* Category Filter */}
              <div className="relative">
                <select
                  value={selectedCategory}
                  onChange={(e) => setSelectedCategory(e.target.value)}
                  className="w-full px-4 py-3 rounded-xl border-2 border-border focus:border-primary focus:ring-4 focus:ring-primary/10 focus:outline-none appearance-none bg-white shadow-soft transition-all duration-300 cursor-pointer"
                >
                  <option value="">{t('allCategories')}</option>
                  {availableCategories.map(category => (
                    <option key={category} value={category}>{category}</option>
                  ))}
                </select>
                <svg className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-text-secondary pointer-events-none" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </div>

              {/* Level Filter */}
              <div className="relative">
                <select
                  value={selectedLevel}
                  onChange={(e) => setSelectedLevel(e.target.value)}
                  className="w-full px-4 py-3 rounded-xl border-2 border-border focus:border-primary focus:ring-4 focus:ring-primary/10 focus:outline-none appearance-none bg-white shadow-soft transition-all duration-300 cursor-pointer"
                >
                  <option value="">{t('allLevels')}</option>
                  <option value="Central">{t('centralSchemes')}</option>
                  <option value="State">{t('stateSchemes')}</option>
                </select>
                <svg className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-text-secondary pointer-events-none" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </div>
            </div>

            {/* Clear Filters Button */}
            {(selectedState || selectedCategory || selectedLevel || searchQuery) && (
              <div className="flex justify-center">
                <button
                  onClick={handleClearFilters}
                  className="inline-flex items-center gap-2 text-sm text-primary hover:text-primary-dark font-semibold transition-colors duration-300 px-4 py-2 rounded-lg hover:bg-primary/5"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                  {t('clearFilters')}
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Features */}
        <div className="mt-20 grid grid-cols-1 md:grid-cols-3 gap-8 max-w-6xl w-full">
          <div className="group relative card-gradient text-center transform hover:scale-105 transition-all duration-300">
            <div className="absolute inset-0 bg-gradient-to-br from-primary/10 to-transparent rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
            <div className="relative">
              <div className="text-6xl mb-4 transform group-hover:scale-110 transition-transform duration-300">🎤</div>
              <h3 className="text-xl font-bold mb-3 text-text-primary">{t('voiceFirst')}</h3>
              <p className="text-sm text-text-secondary leading-relaxed">
                {t('voiceFirstDesc')}
              </p>
            </div>
          </div>
          <div className="group relative card-gradient text-center transform hover:scale-105 transition-all duration-300">
            <div className="absolute inset-0 bg-gradient-to-br from-secondary/10 to-transparent rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
            <div className="relative">
              <div className="text-6xl mb-4 transform group-hover:scale-110 transition-transform duration-300">🎯</div>
              <h3 className="text-xl font-bold mb-3 text-text-primary">{t('smartMatching')}</h3>
              <p className="text-sm text-text-secondary leading-relaxed">
                {t('smartMatchingDesc')}
              </p>
            </div>
          </div>
          <div className="group relative card-gradient text-center transform hover:scale-105 transition-all duration-300">
            <div className="absolute inset-0 bg-gradient-to-br from-accent/10 to-transparent rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
            <div className="relative">
              <div className="text-6xl mb-4 transform group-hover:scale-110 transition-transform duration-300">📱</div>
              <h3 className="text-xl font-bold mb-3 text-text-primary">{t('simpleAccessible')}</h3>
              <p className="text-sm text-text-secondary leading-relaxed">
                {t('simpleAccessibleDesc')}
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Schemes Section */}
      {(showSchemes || displaySchemes.length > 0) && (
        <section className="py-16 px-4 bg-gradient-to-b from-background to-white">
          <div className="container mx-auto max-w-7xl">
            <div className="text-center mb-12">
              <h2 className="text-3xl md:text-4xl font-bold mb-4">
                {searchQuery ? (
                  <>
                    <span className="gradient-text">{t('searchResults')}</span>
                    <span className="text-text-secondary ml-2">({displaySchemes.length})</span>
                  </>
                ) : (
                  <span className="gradient-text">{t('eligibleSchemes')}</span>
                )}
              </h2>
              <div className="w-24 h-1 bg-gradient-to-r from-primary to-secondary mx-auto rounded-full"></div>
            </div>

            {loading ? (
              <div className="text-center py-16">
                <div className="inline-flex flex-col items-center gap-4">
                  <div className="relative">
                    <div className="w-16 h-16 border-4 border-primary/20 border-t-primary rounded-full animate-spin"></div>
                    <div className="absolute inset-0 w-16 h-16 border-4 border-transparent border-r-secondary rounded-full animate-spin" style={{ animationDirection: 'reverse', animationDuration: '1s' }}></div>
                  </div>
                  <p className="text-lg text-text-secondary font-medium">{t('loadingSchemes')}</p>
                </div>
              </div>
            ) : displaySchemes.length === 0 ? (
              <div className="text-center py-16">
                <div className="inline-flex flex-col items-center gap-4 max-w-md">
                  <div className="w-24 h-24 bg-gradient-to-br from-primary/10 to-secondary/10 rounded-full flex items-center justify-center">
                    <svg className="w-12 h-12 text-text-secondary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <p className="text-xl font-semibold text-text-primary">
                    {searchQuery ? t('noSchemesFound') : t('loadingSchemes')}
                  </p>
                  <p className="text-sm text-text-secondary">
                    Try adjusting your search or filters to find more schemes
                  </p>
                </div>
              </div>
            ) : (
              <>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 lg:gap-8">
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
                  <div className="text-center mt-12">
                    <div className="inline-flex flex-col items-center gap-4">
                      <p className="text-text-secondary font-medium">
                        {t('showing')} <span className="font-bold text-primary">{displaySchemes.length}</span> {t('of')} <span className="font-bold text-secondary">{allSchemes.length}</span>
                      </p>
                      <button
                        className="btn-outline px-10 py-3.5 flex items-center gap-2"
                        onClick={handleLoadMore}
                      >
                        {t('loadMore')}
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                        </svg>
                      </button>
                    </div>
                  </div>
                )}
                {!hasMore && allSchemes.length > ITEMS_PER_PAGE && (
                  <div className="text-center mt-12">
                    <div className="inline-flex items-center gap-2 px-6 py-3 bg-accent/10 text-accent rounded-xl font-medium">
                      <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                      </svg>
                      {t('noMoreSchemes')}
                    </div>
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
