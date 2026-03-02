import React from 'react';

const Footer: React.FC = () => {
  return (
    <footer className="bg-background-secondary border-t border-border py-8 mt-auto">
      <div className="container mx-auto px-4">
        <div className="flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <span className="text-lg">🌾</span>
            <span className="font-semibold text-text-primary">Gram Sahayak</span>
          </div>

          <p className="text-sm text-text-secondary text-center">
            Built with ❤️ for rural India 🇮🇳 &middot;{' '}
            <a
              href="https://www.myscheme.gov.in/"
              target="_blank"
              rel="noopener noreferrer"
              className="text-primary hover:text-primary-light hover:underline transition-colors"
            >
              myscheme.gov.in
            </a>
          </p>

          <p className="text-xs text-text-tertiary">&copy; {new Date().getFullYear()} Gram Sahayak</p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
