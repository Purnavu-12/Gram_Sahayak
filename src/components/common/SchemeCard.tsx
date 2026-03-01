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
      className="card hover:shadow-2xl cursor-pointer transform hover:-translate-y-1"
      onClick={() => onSelect?.(scheme.id)}
    >
      <div className="flex items-start justify-between mb-3">
        <h3 className="text-xl font-semibold text-primary flex-1">
          {scheme.name}
        </h3>
        {isEligible && (
          <span className="ml-2 px-3 py-1 bg-success text-white text-sm rounded-full">
            ✓ Eligible
          </span>
        )}
      </div>

      <p className="text-text-secondary mb-4 line-clamp-3">
        {scheme.description}
      </p>

      <div className="border-t border-border pt-3">
        <div className="flex items-center justify-between">
          <span className="text-sm text-text-secondary">
            Category: <span className="font-medium text-text-primary">{scheme.category}</span>
          </span>
          <button
            className="text-primary hover:text-primary-dark font-medium text-sm"
            onClick={(e) => {
              e.stopPropagation();
              onSelect?.(scheme.id);
            }}
          >
            Learn More →
          </button>
        </div>
      </div>
    </div>
  );
};

export default SchemeCard;
