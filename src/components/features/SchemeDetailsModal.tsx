import React from 'react';
import { Scheme } from '../../types';

interface SchemeDetailsModalProps {
  scheme: Scheme;
  onClose: () => void;
}

const SchemeDetailsModal: React.FC<SchemeDetailsModalProps> = ({ scheme, onClose }) => {
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-md"
      onClick={onClose}
    >
      <div
        className="bg-surface rounded-2xl shadow-large border border-border max-w-2xl w-full max-h-[85vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="sticky top-0 bg-surface/95 backdrop-blur-sm border-b border-border px-6 py-4 rounded-t-2xl flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <h2 className="text-xl md:text-2xl font-bold text-text-primary leading-tight">
              {scheme.name}
            </h2>
            <div className="flex flex-wrap items-center gap-2 mt-2">
              <span className="inline-block px-2.5 py-0.5 bg-primary/10 text-primary rounded-md text-xs font-semibold border border-primary/15">
                {scheme.category}
              </span>
              {scheme.level && (
                <span className="inline-block px-2.5 py-0.5 bg-accent/10 text-accent rounded-md text-xs font-semibold border border-accent/15">
                  {scheme.level}
                </span>
              )}
              {scheme.source === 'web' && (
                <span className="inline-block px-2.5 py-0.5 bg-secondary/10 text-secondary rounded-md text-xs font-semibold border border-secondary/15">
                  🌐 Web Result
                </span>
              )}
            </div>
          </div>
          <button
            onClick={onClose}
            className="shrink-0 w-8 h-8 rounded-lg bg-surface-light hover:bg-primary/10 flex items-center justify-center transition"
            aria-label="Close"
          >
            <svg className="w-4 h-4 text-text-secondary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Body */}
        <div className="px-6 py-5 space-y-6">
          {/* Description */}
          <section>
            <h3 className="text-sm font-semibold text-text-tertiary uppercase tracking-wide mb-2">Description</h3>
            <p className="text-text-primary leading-relaxed">{scheme.description}</p>
          </section>

          {/* Ministry */}
          {scheme.ministry && (
            <section>
              <h3 className="text-sm font-semibold text-text-tertiary uppercase tracking-wide mb-2">Ministry</h3>
              <p className="text-text-primary">{scheme.ministry}</p>
            </section>
          )}

          {/* Beneficiary Info */}
          {scheme.schemeFor && (
            <section>
              <h3 className="text-sm font-semibold text-text-tertiary uppercase tracking-wide mb-2">Scheme For</h3>
              <p className="text-text-primary">{scheme.schemeFor}</p>
            </section>
          )}

          {/* States */}
          {scheme.states && scheme.states.length > 0 && (
            <section>
              <h3 className="text-sm font-semibold text-text-tertiary uppercase tracking-wide mb-2">Beneficiary States</h3>
              <div className="flex flex-wrap gap-2">
                {scheme.states.map((s) => (
                  <span key={s} className="px-2.5 py-1 bg-background-secondary text-text-primary text-xs rounded-lg border border-border">
                    {s}
                  </span>
                ))}
              </div>
            </section>
          )}

          {/* Categories */}
          {scheme.categories && scheme.categories.length > 1 && (
            <section>
              <h3 className="text-sm font-semibold text-text-tertiary uppercase tracking-wide mb-2">Categories</h3>
              <div className="flex flex-wrap gap-2">
                {scheme.categories.map((c) => (
                  <span key={c} className="px-2.5 py-1 bg-primary/8 text-primary text-xs rounded-lg border border-primary/15">
                    {c}
                  </span>
                ))}
              </div>
            </section>
          )}

          {/* Tags */}
          {scheme.tags && scheme.tags.length > 0 && (
            <section>
              <h3 className="text-sm font-semibold text-text-tertiary uppercase tracking-wide mb-2">Tags</h3>
              <div className="flex flex-wrap gap-2">
                {scheme.tags.map((tag) => (
                  <span key={tag} className="px-2.5 py-1 bg-surface-light text-text-secondary text-xs rounded-lg border border-border">
                    #{tag}
                  </span>
                ))}
              </div>
            </section>
          )}
        </div>

        {/* Actions */}
        <div className="sticky bottom-0 bg-surface/95 backdrop-blur-sm border-t border-border px-6 py-4 rounded-b-2xl flex flex-col sm:flex-row gap-3">
          <a
            href={scheme.url}
            target="_blank"
            rel="noopener noreferrer"
            className="btn-primary text-center flex-1"
          >
            Visit Official Website
          </a>
          <button onClick={onClose} className="btn-outline flex-1">
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

export default SchemeDetailsModal;
