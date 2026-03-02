export interface Scheme {
  id: string;            // slug
  name: string;          // scheme_name
  shortTitle: string;    // scheme_short_title
  description: string;   // brief_description
  ministry: string;      // nodal_ministry_name
  level: string;         // Central / State
  category: string;      // first category
  categories: string[];  // all categories
  tags: string[];
  states: string[];      // beneficiary states list
  state: string;         // human-readable states string
  url: string;           // official URL
  schemeFor: string;     // target beneficiary
  source: 'db' | 'web';
}
