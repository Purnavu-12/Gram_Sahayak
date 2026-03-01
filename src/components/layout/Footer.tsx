import React from 'react';

const Footer: React.FC = () => {
  return (
    <footer className="relative bg-gradient-to-r from-slate-900 to-slate-800 text-white py-8 mt-auto overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-br from-primary/10 to-secondary/10 opacity-50"></div>
      <div className="container mx-auto px-4 relative z-10">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-6">
          <div>
            <div className="flex items-center space-x-3 mb-3">
              <div className="w-10 h-10 bg-primary/20 rounded-xl flex items-center justify-center">
                <span className="text-2xl">🌾</span>
              </div>
              <h3 className="text-xl font-bold">Gram Sahayak</h3>
            </div>
            <p className="text-sm text-slate-300">
              Empowering rural India with easy access to government schemes and services.
            </p>
          </div>

          <div>
            <h4 className="font-semibold mb-3 text-lg">Quick Links</h4>
            <ul className="space-y-2 text-sm text-slate-300">
              <li><a href="#" className="hover:text-primary-light transition-colors">About Us</a></li>
              <li><a href="#" className="hover:text-primary-light transition-colors">Schemes</a></li>
              <li><a href="#" className="hover:text-primary-light transition-colors">How It Works</a></li>
            </ul>
          </div>

          <div>
            <h4 className="font-semibold mb-3 text-lg">Contact</h4>
            <ul className="space-y-2 text-sm text-slate-300">
              <li>📧 support@gramsahayak.in</li>
              <li>📱 1800-XXX-XXXX</li>
              <li>🌐 myscheme.gov.in</li>
            </ul>
          </div>
        </div>

        <div className="border-t border-white/10 pt-6 text-center">
          <p className="text-slate-300 text-sm">
            &copy; 2026 Gram Sahayak. Built with ❤️ for rural India 🇮🇳 | ग्रामीण भारत के लिए बनाया गया
          </p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
