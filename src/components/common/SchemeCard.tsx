import React from 'react';
import { Scheme } from '../../types';

interface SchemeCardProps {
  scheme: Scheme;
  onSelect?: (schemeId: string) => void;
  isEligible?: boolean;
}

const SchemeCard: React.FC<SchemeCardProps> = ({
  scheme,
  onSelect,
  isEligible = false
}) => {
  return (
    <div
      className="group relative card-gradient cursor-pointer transform hover:-translate-y-2 transition-all duration-300"
      onClick={() => onSelect?.(scheme.id)}
    >
      {/* Gradient border effect */}
      <div className="absolute inset-0 bg-gradient-to-br from-primary/20 via-secondary/10 to-primary/20 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-300 -z-10 blur-sm"></div>

      <div className="relative bg-white rounded-2xl p-6 h-full border border-border/50 group-hover:border-primary/30 transition-all duration-300">
        <div className="flex items-start justify-between mb-4">
          <div className="flex-1">
            <h3 className="text-xl font-bold text-text-primary group-hover:text-primary transition-colors duration-300 mb-2 line-clamp-2">
              {scheme.name}
            </h3>
          </div>
          {isEligible && (
            <span className="ml-3 px-3 py-1.5 bg-gradient-to-r from-accent to-accent-dark text-white text-xs font-bold rounded-full shadow-soft flex items-center gap-1 flex-shrink-0">
              <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
              </svg>
              Eligible
            </span>
          )}
        </div>

        <p className="text-text-secondary text-sm leading-relaxed mb-4 line-clamp-3">
          {scheme.description}
        </p>

        {/* Category badge */}
        <div className="mb-4">
          <span className="inline-block px-3 py-1 bg-primary/10 text-primary text-xs font-semibold rounded-lg">
            {scheme.category}
          </span>
        </div>

        {/* Bottom section with learn more */}
        <div className="flex items-center justify-between pt-4 border-t border-border/50 mt-auto">
          <div className="flex items-center gap-2 text-xs text-text-secondary">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span>Government Scheme</span>
          </div>

          <button
            className="flex items-center gap-2 text-primary hover:text-primary-dark font-semibold text-sm group/btn transition-all duration-300"
            onClick={(e) => {
              e.stopPropagation();
              onSelect?.(scheme.id);
            }}
          >
            <span>Learn More</span>
            <svg
              className="w-4 h-4 transform group-hover/btn:translate-x-1 transition-transform duration-300"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
};

export default SchemeCard;
