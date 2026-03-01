import React from 'react';
import { Scheme } from '../../types';
import { useLanguage } from '../LanguageProvider';

interface SchemeDetailsModalProps {
  scheme: Scheme;
  onClose: () => void;
}

const SchemeDetailsModal: React.FC<SchemeDetailsModalProps> = ({ scheme, onClose }) => {
  const { language } = useLanguage();
  const isHindi = language === 'hi';

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50 overflow-y-auto">
      <div className="card max-w-3xl w-full my-8 max-h-[90vh] overflow-y-auto">
        <div className="flex items-start justify-between mb-6">
          <div className="flex-1">
            <h2 className="text-2xl md:text-3xl font-bold text-primary mb-2">
              {isHindi ? scheme.nameHindi : scheme.name}
            </h2>
            <span className="inline-block px-3 py-1 bg-primary/10 text-primary rounded-full text-sm">
              {scheme.category}
            </span>
          </div>
          <button
            onClick={onClose}
            className="ml-4 text-text-secondary hover:text-text-primary text-3xl font-light"
            aria-label="Close"
          >
            ×
          </button>
        </div>

        <div className="space-y-6">
          {/* Description */}
          <div>
            <h3 className="font-semibold text-lg mb-2">Description</h3>
            <p className="text-text-secondary leading-relaxed">
              {isHindi ? scheme.descriptionHindi : scheme.description}
            </p>
          </div>

          {/* Benefits */}
          <div>
            <h3 className="font-semibold text-lg mb-2">Benefits</h3>
            <ul className="space-y-2">
              {scheme.benefits.map((benefit, index) => (
                <li key={index} className="flex items-start">
                  <span className="text-success mr-2 mt-1">✓</span>
                  <span className="text-text-secondary">{benefit}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Eligibility Criteria */}
          <div>
            <h3 className="font-semibold text-lg mb-2">Eligibility Criteria</h3>
            <div className="bg-background p-4 rounded-lg space-y-2">
              {scheme.eligibilityCriteria.ageMin && (
                <p className="text-text-secondary">
                  <span className="font-medium">Minimum Age:</span> {scheme.eligibilityCriteria.ageMin} years
                </p>
              )}
              {scheme.eligibilityCriteria.ageMax && (
                <p className="text-text-secondary">
                  <span className="font-medium">Maximum Age:</span> {scheme.eligibilityCriteria.ageMax} years
                </p>
              )}
              {scheme.eligibilityCriteria.gender && scheme.eligibilityCriteria.gender !== 'any' && (
                <p className="text-text-secondary">
                  <span className="font-medium">Gender:</span> {scheme.eligibilityCriteria.gender}
                </p>
              )}
              {scheme.eligibilityCriteria.incomeMax && (
                <p className="text-text-secondary">
                  <span className="font-medium">Maximum Income:</span> ₹{scheme.eligibilityCriteria.incomeMax.toLocaleString()} per year
                </p>
              )}
              {scheme.eligibilityCriteria.occupation && (
                <p className="text-text-secondary">
                  <span className="font-medium">Occupation:</span> {scheme.eligibilityCriteria.occupation.join(', ')}
                </p>
              )}
            </div>
          </div>

          {/* Required Documents */}
          {scheme.requiredDocuments.length > 0 && (
            <div>
              <h3 className="font-semibold text-lg mb-2">Required Documents</h3>
              <ul className="space-y-3">
                {scheme.requiredDocuments.map((doc, index) => (
                  <li key={index} className="border-l-4 border-primary pl-4">
                    <p className="font-medium text-text-primary">
                      {isHindi ? doc.nameHindi : doc.name}
                      {doc.mandatory && <span className="text-error ml-1">*</span>}
                    </p>
                    <p className="text-sm text-text-secondary mt-1">{doc.description}</p>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Application Process */}
          <div>
            <h3 className="font-semibold text-lg mb-2">How to Apply</h3>
            <p className="text-text-secondary">{scheme.applicationProcess}</p>
          </div>

          {/* Action Buttons */}
          <div className="flex flex-col sm:flex-row gap-4 pt-4 border-t border-border">
            <a
              href={scheme.officialUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="btn-primary text-center flex-1"
            >
              Visit Official Website
            </a>
            <button className="btn-secondary flex-1">
              Get Voice Assistance
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SchemeDetailsModal;
