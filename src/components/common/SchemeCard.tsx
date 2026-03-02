import React from 'react';
import { Scheme } from '../../types';

interface SchemeCardProps {
  scheme: Scheme;
  onSelect?: (schemeId: string) => void;
  isEligible?: boolean;
}

const SchemeCard: React.FC<SchemeCardProps> = ({ scheme, onSelect, isEligible = false }) => {
  return (
    <article
      className="group relative glass-card glow-border p-5 cursor-pointer
                 transition-all duration-300 hover:-translate-y-1 hover:shadow-card-hover"
      onClick={() => onSelect?.(scheme.id)}
    >
      {/* Gradient shimmer on hover */}
      <div className="absolute inset-0 rounded-2xl bg-gradient-card opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none" />

      {/* Top row: badge + eligible tag */}
      <div className="relative flex items-start justify-between gap-3 mb-3">
        <span className="inline-block px-2.5 py-1 bg-primary/10 text-primary text-xs font-semibold rounded-md border border-primary/15">
          {scheme.category}
        </span>
        {isEligible && (
          <span className="flex items-center gap-1 px-2 py-0.5 bg-accent/10 text-accent text-xs font-bold rounded-full border border-accent/20">
            <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
            </svg>
            Eligible
          </span>
        )}
      </div>

      {/* Title */}
      <h3 className="relative text-lg font-bold text-text-primary leading-snug mb-2 line-clamp-2 group-hover:text-primary transition-colors">
        {scheme.name}
      </h3>

      {/* Description */}
      <p className="relative text-sm text-text-secondary leading-relaxed mb-4 line-clamp-3">
        {scheme.description}
      </p>

      {/* State tag if available */}
      {scheme.state && (
        <p className="relative text-xs text-text-tertiary mb-4 flex items-center gap-1">
          <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a2 2 0 01-2.828 0l-4.243-4.243a8 8 0 1111.314 0z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
          {scheme.state}
        </p>
      )}

      {/* CTA */}
      <div className="relative pt-3 border-t border-border">
        <button
          className="flex items-center gap-1 text-primary text-sm font-semibold group-hover:gap-2 transition-all"
          onClick={(e) => { e.stopPropagation(); onSelect?.(scheme.id); }}
        >
          Learn more
          <svg className="w-4 h-4 transition-transform group-hover:translate-x-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </button>
      </div>
    </article>
  );
};

export default SchemeCard;
