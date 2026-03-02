import React, { useState, useEffect } from 'react';
import { useLanguage } from '../components/LanguageProvider';
import VoiceButton from '../components/common/VoiceButton';
import SchemeCard from '../components/common/SchemeCard';
import SchemeDetailsModal from '../components/features/SchemeDetailsModal';
import { initDatabase, getFeaturedSchemes, searchSchemes, getDbStats, getAllCategories, getAllStates } from '../services/schemeData';
import { getVoiceService } from '../services/livekitService';
import { Scheme } from '../types';

// Pre-warm LiveKit token + room on module load (before any user interaction)
getVoiceService();

// ── Quick category definitions ──────────────────────────────────────────────
const QUICK_CATEGORIES = [
  { key: 'farmer agriculture', icon: '👨‍🌾', labelKey: 'catFarming' },
  { key: 'health medical', icon: '💊', labelKey: 'catHealth' },
  { key: 'education scholarship', icon: '🎓', labelKey: 'catEducation' },
  { key: 'housing home', icon: '🏠', labelKey: 'catHousing' },
  { key: 'women girl', icon: '👩', labelKey: 'catWomen' },
  { key: 'loan business', icon: '💰', labelKey: 'catFinance' },
  { key: 'pension elderly senior', icon: '👴', labelKey: 'catElderly' },
  { key: 'disability handicap', icon: '♿', labelKey: 'catDisability' },
] as const;

const PER_PAGE = 12;

const Home: React.FC = () => {
  const { t } = useLanguage();

  // Data
  const [schemes, setSchemes] = useState<Scheme[]>([]);
  const [webResults, setWebResults] = useState<Scheme[]>([]);
  const [displaySchemes, setDisplaySchemes] = useState<Scheme[]>([]);
  const [selectedScheme, setSelectedScheme] = useState<Scheme | null>(null);
  const [dbStats, setDbStats] = useState({ total: 0, central: 0, state: 0 });

  // Filters
  const [query, setQuery] = useState('');
  const [state, setState] = useState('');
  const [category, setCategory] = useState('');
  const [level, setLevel] = useState('');
  const [stateOptions, setStateOptions] = useState<string[]>([]);
  const [categoryOptions, setCategoryOptions] = useState<string[]>([]);

  // UI state
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [searched, setSearched] = useState(false);

  // ── Init ─────────────────────────────────────────────────────────────
  useEffect(() => {
    (async () => {
      try {
        setLoading(true);
        await initDatabase();
        const [stats, states, categories, featured] = await Promise.all([
          getDbStats(),
          getAllStates(),
          getAllCategories(),
          getFeaturedSchemes(6),
        ]);
        setDbStats(stats);
        setStateOptions(states);
        setCategoryOptions(categories);
        setSchemes(featured);
        setDisplaySchemes(featured);
      } catch (err) {
        console.error('Init failed:', err);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  // ── Search ───────────────────────────────────────────────────────────
  const runSearch = async () => {
    setLoading(true);
    setPage(1);
    setSearched(true);
    try {
      const filters: { state?: string; category?: string; level?: string } = {};
      if (state) filters.state = state;
      if (category) filters.category = category;
      if (level) filters.level = level;
      const { results, webResults: web } = await searchSchemes(query, filters, 100);
      setSchemes(results);
      setWebResults(web);
      setDisplaySchemes(results.slice(0, PER_PAGE));
    } catch {
      setSchemes([]);
      setWebResults([]);
      setDisplaySchemes([]);
    } finally {
      setLoading(false);
    }
  };

  const handleLoadMore = () => {
    const next = page + 1;
    setDisplaySchemes(schemes.slice(0, next * PER_PAGE));
    setPage(next);
  };

  const clearFilters = () => {
    setQuery('');
    setState('');
    setCategory('');
    setLevel('');
    setSearched(false);
    setWebResults([]);
  };

  // Auto-search when filters change
  useEffect(() => {
    if (state || category || level) runSearch();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [state, category, level]);

  const hasMore = displaySchemes.length < schemes.length;

  return (
    <div className="min-h-screen flex flex-col">
      {/* ─── Hero ──────────────────────────────────────────────────────── */}
      <section className="relative flex flex-col items-center justify-center py-20 md:py-28 px-4 overflow-hidden">
        {/* Animated mesh background */}
        <div className="absolute inset-0 -z-10 bg-mesh-gradient opacity-80" />
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[600px] -z-10 bg-gradient-to-b from-primary/8 via-transparent to-transparent blur-3xl rounded-full" />
        {/* Floating orbs */}
        <div className="absolute top-20 left-[10%] w-72 h-72 -z-10 bg-primary/5 rounded-full blur-[100px] animate-float" />
        <div className="absolute bottom-10 right-[15%] w-56 h-56 -z-10 bg-secondary/5 rounded-full blur-[80px] animate-float" style={{ animationDelay: '3s' }} />

        <div className="text-center max-w-3xl mb-12">
          <span className="inline-flex items-center gap-2 px-4 py-1.5 text-xs font-semibold text-primary bg-primary/8 rounded-full border border-primary/15 mb-6 backdrop-blur-sm">
            <span className="w-1.5 h-1.5 bg-accent rounded-full animate-pulse" />
            🇮🇳 Empowering Rural India
          </span>

          <h1 className="text-4xl md:text-6xl font-bold leading-[1.1] mb-5 tracking-tight">
            <span className="gradient-text">{t('welcome')}</span>
          </h1>

          <p className="text-lg md:text-xl text-text-secondary mb-3 leading-relaxed">{t('welcomeSubtitle')}</p>
          <p className="text-sm text-text-tertiary max-w-xl mx-auto">{t('description')}</p>

          {/* Stats */}
          {dbStats.total > 0 && (
            <div className="mt-10 inline-flex items-center gap-6 glass-card px-8 py-5">
              <Stat value={dbStats.total} label={t('schemesAvailable')} color="text-primary" />
              <Divider />
              <Stat value={dbStats.central} label={t('central')} color="text-accent" />
              <Divider />
              <Stat value={dbStats.state} label={t('stateUT')} color="text-secondary" />
            </div>
          )}
        </div>

        {/* Voice CTA */}
        <VoiceButton
          onStartListening={() => console.log('voice started')}
          onStopListening={() => console.log('voice stopped')}
        />

        {/* ─── Search bar ──────────────────────────────────────────────── */}
        <div className="mt-12 w-full max-w-2xl">
          <div className="flex gap-2">
            <input
              type="text"
              placeholder={t('searchPlaceholder')}
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && runSearch()}
              className="flex-1 px-5 py-3 rounded-xl border border-border-light bg-surface text-text-primary text-base
                         placeholder:text-text-tertiary
                         focus:border-primary/50 focus:ring-4 focus:ring-primary/10 outline-none transition-all shadow-soft"
            />
            <button onClick={runSearch} disabled={loading} className="btn-primary px-6 whitespace-nowrap">
              {loading ? (
                <svg className="animate-spin h-5 w-5 mx-auto" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
              ) : t('search')}
            </button>
          </div>

          {/* Filters row */}
          <div className="grid grid-cols-3 gap-3 mt-3">
            <Select value={state} onChange={setState} placeholder={t('allStates')} options={stateOptions} />
            <Select value={category} onChange={setCategory} placeholder={t('allCategories')} options={categoryOptions} />
            <Select value={level} onChange={setLevel} placeholder={t('allLevels')} options={[
              { value: 'Central', label: t('centralSchemes') },
              { value: 'State', label: t('stateSchemes') },
            ]} />
          </div>

          {(state || category || level || query) && (
            <button onClick={clearFilters} className="mt-3 text-sm text-primary font-semibold hover:text-primary-light transition-colors">
              {t('clearFilters')}
            </button>
          )}
        </div>

        {/* ─── Quick Category Buttons (village-friendly) ─────────────── */}
        <div className="mt-10 w-full max-w-3xl">
          <p className="text-center text-sm text-text-tertiary mb-4 font-medium">{t('quickFind')}</p>
          <div className="grid grid-cols-3 md:grid-cols-4 gap-3">
            {QUICK_CATEGORIES.map((cat) => (
              <button
                key={cat.key}
                onClick={() => {
                  setQuery(cat.key);
                  setCategory('');
                  setSearched(true);
                  setLoading(true);
                  setPage(1);
                  searchSchemes(cat.key, {}, 100).then(({ results, webResults: web }) => {
                    setSchemes(results);
                    setWebResults(web);
                    setDisplaySchemes(results.slice(0, PER_PAGE));
                  }).catch(() => {
                    setSchemes([]); setWebResults([]); setDisplaySchemes([]);
                  }).finally(() => setLoading(false));
                }}
                className="group flex flex-col items-center gap-2 py-4 px-2 rounded-2xl
                           bg-surface-glass border border-border hover:border-primary/40
                           hover:bg-primary/8 transition-all duration-300 hover:-translate-y-0.5
                           hover:shadow-glow active:scale-95"
              >
                <span className="text-3xl md:text-4xl group-hover:scale-110 transition-transform">{cat.icon}</span>
                <span className="text-xs md:text-sm font-semibold text-text-secondary group-hover:text-primary transition-colors leading-tight text-center">
                  {t(cat.labelKey)}
                </span>
              </button>
            ))}
          </div>
        </div>

        {/* ─── Feature cards ───────────────────────────────────────────── */}
        <div className="mt-20 grid grid-cols-1 md:grid-cols-3 gap-5 max-w-4xl w-full">
          <FeatureCard icon="🎤" title={t('voiceFirst')} desc={t('voiceFirstDesc')} accent="primary" />
          <FeatureCard icon="🎯" title={t('smartMatching')} desc={t('smartMatchingDesc')} accent="secondary" />
          <FeatureCard icon="📱" title={t('simpleAccessible')} desc={t('simpleAccessibleDesc')} accent="accent" />
        </div>
      </section>

      {/* ─── Schemes grid ──────────────────────────────────────────────── */}
      {(searched || displaySchemes.length > 0) && (
        <section className="py-16 px-4 relative">
          <div className="absolute inset-0 -z-10 bg-gradient-to-b from-transparent via-background-secondary/50 to-transparent" />
          <div className="container mx-auto max-w-6xl">
            <h2 className="text-2xl md:text-3xl font-bold text-center mb-10">
              {searched ? (
                <>
                  <span className="gradient-text">{t('searchResults')}</span>
                  <span className="text-text-tertiary text-lg ml-2">({schemes.length})</span>
                </>
              ) : (
                <span className="gradient-text">{t('eligibleSchemes')}</span>
              )}
            </h2>

            {loading ? (
              <div className="flex justify-center py-16">
                <div className="w-10 h-10 border-2 border-primary/20 border-t-primary rounded-full animate-spin" />
              </div>
            ) : displaySchemes.length === 0 && webResults.length === 0 ? (
              <p className="text-center text-text-secondary py-16">{t('noSchemesFound')}</p>
            ) : (
              <>
                {displaySchemes.length > 0 && (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
                    {displaySchemes.map((s) => (
                      <SchemeCard
                        key={s.id}
                        scheme={s}
                        onSelect={(id) => {
                          const found = [...schemes, ...webResults].find((x) => x.id === id);
                          if (found) setSelectedScheme(found);
                        }}
                        isEligible
                      />
                    ))}
                  </div>
                )}

                {hasMore && (
                  <div className="text-center mt-10">
                    <button onClick={handleLoadMore} className="btn-outline px-8">
                      {t('loadMore')}
                    </button>
                  </div>
                )}

                {/* Web results section */}
                {webResults.length > 0 && (
                  <div className="mt-12">
                    <h3 className="text-xl font-bold text-text-primary mb-6 flex items-center gap-2">
                      <svg className="w-5 h-5 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9" />
                      </svg>
                      Web Results
                    </h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
                      {webResults.map((s) => (
                        <article
                          key={s.id}
                          className="group relative glass-card glow-border p-5 cursor-pointer transition-all duration-300 hover:-translate-y-1"
                          onClick={() => s.url && window.open(s.url, '_blank')}
                        >
                          <span className="inline-block px-2.5 py-1 bg-secondary/10 text-secondary text-xs font-semibold rounded-md border border-secondary/15 mb-3">
                            🌐 Web
                          </span>
                          <h3 className="text-lg font-bold text-text-primary leading-snug mb-2 line-clamp-2 group-hover:text-primary transition-colors">
                            {s.name}
                          </h3>
                          <p className="text-sm text-text-secondary leading-relaxed line-clamp-3">
                            {s.description}
                          </p>
                        </article>
                      ))}
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        </section>
      )}

      {/* Modal */}
      {selectedScheme && (
        <SchemeDetailsModal scheme={selectedScheme} onClose={() => setSelectedScheme(null)} />
      )}
    </div>
  );
};

export default Home;

/* ── Tiny helper components ─────────────────────────────────────────────────── */

function Stat({ value, label, color }: { value: number; label: string; color: string }) {
  return (
    <div className="text-center">
      <p className={`text-2xl font-bold ${color}`}>{value}</p>
      <p className="text-xs text-text-tertiary mt-0.5">{label}</p>
    </div>
  );
}

function Divider() {
  return <div className="w-px h-10 bg-border-light" />;
}

function FeatureCard({ icon, title, desc, accent }: { icon: string; title: string; desc: string; accent: string }) {
  const glowColor = accent === 'primary'
    ? 'group-hover:shadow-glow'
    : accent === 'secondary'
      ? 'group-hover:shadow-glow-pink'
      : 'group-hover:shadow-[0_0_30px_rgba(52,211,153,0.15)]';

  return (
    <div className={`group glass-card glow-border p-6 text-center transition-all duration-300 hover:-translate-y-1 ${glowColor}`}>
      <div className="text-4xl mb-4 animate-float" style={{ animationDelay: `${Math.random() * 2}s` }}>{icon}</div>
      <h3 className="font-bold text-text-primary text-lg mb-2">{title}</h3>
      <p className="text-sm text-text-secondary leading-relaxed">{desc}</p>
    </div>
  );
}

interface SelectProps {
  value: string;
  onChange: (v: string) => void;
  placeholder: string;
  options: string[] | { value: string; label: string }[];
}

function Select({ value, onChange, placeholder, options }: SelectProps) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="w-full px-3 py-2.5 rounded-xl border border-border-light bg-surface text-text-primary text-sm
                 focus:border-primary/50 focus:ring-4 focus:ring-primary/10 outline-none appearance-none cursor-pointer
                 transition-all shadow-soft"
    >
      <option value="">{placeholder}</option>
      {options.map((opt) =>
        typeof opt === 'string' ? (
          <option key={opt} value={opt}>{opt}</option>
        ) : (
          <option key={opt.value} value={opt.value}>{opt.label}</option>
        ),
      )}
    </select>
  );
}
