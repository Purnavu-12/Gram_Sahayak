import React from 'react';
import { LanguageProvider } from './components/LanguageProvider';
import ErrorBoundary from './components/ErrorBoundary';
import Header from './components/layout/Header';
import Footer from './components/layout/Footer';
import Home from './pages/Home';
import LanguageModal from './components/features/LanguageModal';

const App: React.FC = () => {
  return (
    <ErrorBoundary>
      <LanguageProvider>
        <LanguageModal />
        <div className="flex flex-col min-h-screen">
          <Header />
          <main className="flex-1">
            <Home />
          </main>
          <Footer />
        </div>
      </LanguageProvider>
    </ErrorBoundary>
  );
};

export default App;
