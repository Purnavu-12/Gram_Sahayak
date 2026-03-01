export interface UserProfile {
  id: string;
  age: number;
  gender: 'male' | 'female' | 'other';
  state: string;
  district: string;
  occupation: string;
  incomeCategory: 'BPL' | 'APL' | 'AAY';
  familySize: number;
  category?: 'SC' | 'ST' | 'OBC' | 'General';
  createdAt: Date;
  updatedAt: Date;
}

export interface EligibilityCriteria {
  ageMin?: number;
  ageMax?: number;
  gender?: 'male' | 'female' | 'other' | 'any';
  incomeMax?: number;
  occupation?: string[];
  state?: string[];
  category?: string[];
  familySize?: { min?: number; max?: number };
  customRules?: string[];
}

export interface Document {
  name: string;
  nameHindi: string;
  description: string;
  mandatory: boolean;
}

export interface Scheme {
  id: string;
  name: string;
  nameHindi: string;
  description: string;
  descriptionHindi: string;
  category: string;
  state?: string;
  benefits: string[];
  eligibilityCriteria: EligibilityCriteria;
  requiredDocuments: Document[];
  applicationProcess: string;
  officialUrl: string;
}

export interface MatchResult {
  scheme: Scheme;
  eligible: boolean;
  confidence: number;
  matchedCriteria: string[];
  explanation: string;
  explanationHindi: string;
}

export type ConversationStage =
  | 'greeting'
  | 'profile_collection'
  | 'scheme_discovery'
  | 'scheme_details'
  | 'application_guidance';

export interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  intent?: string;
}

export interface ConversationContext {
  stage: ConversationStage;
  currentTopic?: string;
  pendingQuestion?: string;
  userProfile?: Partial<UserProfile>;
  selectedScheme?: string;
  collectedDocuments?: string[];
}

export interface Session {
  id: string;
  userId?: string;
  startTime: Date;
  lastActivity: Date;
  context: ConversationContext;
  history: Message[];
}
