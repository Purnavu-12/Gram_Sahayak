/**
 * Scheme Data Service
 * This file now serves as a wrapper around the real SQLite database
 * instead of using mock data.
 */

import { Scheme } from '../types';
import * as db from './schemeDatabase';

// Export database functions
export const searchSchemes = db.searchSchemes;
export const getSchemeById = db.getSchemeById;
export const getAllCategories = db.getAllCategories;
export const getAllStates = db.getAllStates;
export const getDbStats = db.getDbStats;
export const getSchemesByCategory = db.getSchemesByCategory;
export const getFeaturedSchemes = db.getFeaturedSchemes;
export const initDatabase = db.initDatabase;

// Fallback mock schemes for offline/error scenarios
export const mockSchemes: Scheme[] = [
  {
    id: 'pm-kisan',
    name: 'Pradhan Mantri Kisan Samman Nidhi',
    nameHindi: 'प्रधानमंत्री किसान सम्मान निधि',
    description: 'Direct income support of ₹6000 per year to all farmer families across the country. The amount is paid in three equal installments of ₹2000 each.',
    descriptionHindi: 'देश भर के सभी किसान परिवारों को प्रति वर्ष ₹6000 की प्रत्यक्ष आय सहायता। राशि तीन समान किस्तों ₹2000 प्रत्येक में दी जाती है।',
    category: 'Agriculture',
    benefits: [
      '₹6000 per year in 3 installments',
      'Direct bank transfer',
      'No middleman involvement'
    ],
    eligibilityCriteria: {
      occupation: ['farmer', 'agricultural laborer'],
      ageMin: 18
    },
    requiredDocuments: [
      {
        name: 'Land ownership documents',
        nameHindi: 'भूमि स्वामित्व दस्तावेज',
        description: 'Proof of land ownership or cultivation rights',
        mandatory: true
      },
      {
        name: 'Aadhaar Card',
        nameHindi: 'आधार कार्ड',
        description: 'Government ID for verification',
        mandatory: true
      },
      {
        name: 'Bank Account Details',
        nameHindi: 'बैंक खाता विवरण',
        description: 'Account number and IFSC code for direct transfer',
        mandatory: true
      }
    ],
    applicationProcess: 'Apply online through PM-Kisan portal or visit nearest CSC',
    officialUrl: 'https://pmkisan.gov.in'
  }
];
