import { Scheme } from '../types';

// Mock government scheme data
// In production, this would be fetched from myscheme.gov.in API
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
  },
  {
    id: 'pm-jay',
    name: 'Ayushman Bharat - PM-JAY',
    nameHindi: 'आयुष्मान भारत - पीएम-जेएवाई',
    description: 'World\'s largest health insurance scheme providing ₹5 lakh coverage per family per year for secondary and tertiary care hospitalization.',
    descriptionHindi: 'दुनिया की सबसे बड़ी स्वास्थ्य बीमा योजना जो माध्यमिक और तृतीयक देखभाल अस्पताल में भर्ती के लिए प्रति परिवार प्रति वर्ष ₹5 लाख का कवरेज प्रदान करती है।',
    category: 'Health',
    benefits: [
      '₹5 lakh coverage per family per year',
      'Cashless treatment at empanelled hospitals',
      'Covers secondary and tertiary care',
      'Pre and post hospitalization coverage'
    ],
    eligibilityCriteria: {
      incomeMax: 100000,
      ageMin: 0
    },
    requiredDocuments: [
      {
        name: 'Ration Card',
        nameHindi: 'राशन कार्ड',
        description: 'Proof of family income category',
        mandatory: true
      },
      {
        name: 'Aadhaar Card',
        nameHindi: 'आधार कार्ड',
        description: 'For all family members',
        mandatory: true
      }
    ],
    applicationProcess: 'Visit nearest Ayushman Mitra or CSC center',
    officialUrl: 'https://pmjay.gov.in'
  },
  {
    id: 'nsap',
    name: 'National Social Assistance Programme',
    nameHindi: 'राष्ट्रीय सामाजिक सहायता कार्यक्रम',
    description: 'Pension support for elderly persons, widows, and persons with disabilities providing financial security.',
    descriptionHindi: 'वृद्ध व्यक्तियों, विधवाओं और विकलांग व्यक्तियों के लिए पेंशन सहायता जो वित्तीय सुरक्षा प्रदान करती है।',
    category: 'Social Welfare',
    state: 'All India',
    benefits: [
      'Monthly pension of ₹200-500',
      'Direct bank transfer',
      'Financial independence'
    ],
    eligibilityCriteria: {
      ageMin: 60,
      incomeMax: 50000
    },
    requiredDocuments: [
      {
        name: 'Age Proof',
        nameHindi: 'आयु प्रमाण',
        description: 'Birth certificate or school leaving certificate',
        mandatory: true
      },
      {
        name: 'BPL Card',
        nameHindi: 'बीपीएल कार्ड',
        description: 'Below Poverty Line ration card',
        mandatory: true
      },
      {
        name: 'Bank Account',
        nameHindi: 'बैंक खाता',
        description: 'Savings account for pension credit',
        mandatory: true
      }
    ],
    applicationProcess: 'Apply through state government social welfare portal',
    officialUrl: 'https://nsap.nic.in'
  },
  {
    id: 'pm-awas',
    name: 'Pradhan Mantri Awas Yojana - Gramin',
    nameHindi: 'प्रधानमंत्री आवास योजना - ग्रामीण',
    description: 'Housing scheme providing financial assistance to construct pucca houses in rural areas.',
    descriptionHindi: 'ग्रामीण क्षेत्रों में पक्के घर बनाने के लिए वित्तीय सहायता प्रदान करने वाली आवास योजना।',
    category: 'Housing',
    benefits: [
      'Up to ₹1.20 lakh assistance in plains',
      'Up to ₹1.30 lakh in hilly states',
      '90:10 cost sharing (Centre:State)',
      'Includes toilet construction'
    ],
    eligibilityCriteria: {
      incomeMax: 300000,
      occupation: ['agricultural laborer', 'farmer', 'daily wage worker'],
      ageMin: 18
    },
    requiredDocuments: [
      {
        name: 'Income Certificate',
        nameHindi: 'आय प्रमाण पत्र',
        description: 'Annual income proof',
        mandatory: true
      },
      {
        name: 'Land Documents',
        nameHindi: 'जमीन के दस्तावेज',
        description: 'Plot ownership or lease documents',
        mandatory: true
      },
      {
        name: 'Aadhaar Card',
        nameHindi: 'आधार कार्ड',
        description: 'Identity proof',
        mandatory: true
      },
      {
        name: 'Caste Certificate',
        nameHindi: 'जाति प्रमाण पत्र',
        description: 'If applicable for SC/ST category',
        mandatory: false
      }
    ],
    applicationProcess: 'Apply through Gram Panchayat or online portal',
    officialUrl: 'https://pmayg.nic.in'
  },
  {
    id: 'mnrega',
    name: 'Mahatma Gandhi National Rural Employment Guarantee Act',
    nameHindi: 'महात्मा गांधी राष्ट्रीय ग्रामीण रोजगार गारंटी अधिनियम',
    description: 'Guarantees 100 days of wage employment per year to rural households whose adult members volunteer to do unskilled manual work.',
    descriptionHindi: 'ग्रामीण परिवारों को प्रति वर्ष 100 दिनों के वेतन रोजगार की गारंटी देता है जिनके वयस्क सदस्य अकुशल शारीरिक काम करने के लिए स्वेच्छा से आते हैं।',
    category: 'Employment',
    benefits: [
      '100 days guaranteed employment',
      'Minimum wage payment',
      'Within 15 days of application',
      'Work within 5 km of residence'
    ],
    eligibilityCriteria: {
      ageMin: 18,
      occupation: ['daily wage worker', 'unemployed', 'agricultural laborer']
    },
    requiredDocuments: [
      {
        name: 'Job Card',
        nameHindi: 'जॉब कार्ड',
        description: 'MGNREGA job card (will be issued if new)',
        mandatory: false
      },
      {
        name: 'Residence Proof',
        nameHindi: 'निवास प्रमाण',
        description: 'Proof of rural residence',
        mandatory: true
      },
      {
        name: 'Bank Account',
        nameHindi: 'बैंक खाता',
        description: 'For wage payment',
        mandatory: true
      }
    ],
    applicationProcess: 'Apply at Gram Panchayat office for job card',
    officialUrl: 'https://nrega.nic.in'
  },
  {
    id: 'pmuy',
    name: 'Pradhan Mantri Ujjwala Yojana',
    nameHindi: 'प्रधानमंत्री उज्ज्वला योजना',
    description: 'Free LPG connections to BPL households to ensure universal coverage of cooking gas.',
    descriptionHindi: 'खाना पकाने की गैस के सार्वभौमिक कवरेज को सुनिश्चित करने के लिए बीपीएल परिवारों को मुफ्त एलपीजी कनेक्शन।',
    category: 'Energy',
    benefits: [
      'Free LPG connection',
      '₹1600 deposit assistance',
      'First refill free or subsidized',
      'EMI facility for stove and regulator'
    ],
    eligibilityCriteria: {
      incomeMax: 100000,
      gender: 'female',
      ageMin: 18,
      familySize: { min: 1 }
    },
    requiredDocuments: [
      {
        name: 'BPL Certificate',
        nameHindi: 'बीपीएल प्रमाण पत्र',
        description: 'Below Poverty Line certificate',
        mandatory: true
      },
      {
        name: 'Address Proof',
        nameHindi: 'पते का प्रमाण',
        description: 'Ration card, electricity bill, or similar',
        mandatory: true
      },
      {
        name: 'Aadhaar Card',
        nameHindi: 'आधार कार्ड',
        description: 'Identity and address verification',
        mandatory: true
      },
      {
        name: 'Bank Account',
        nameHindi: 'बैंक खाता',
        description: 'In woman\'s name',
        mandatory: true
      }
    ],
    applicationProcess: 'Apply at nearest LPG distributor or online',
    officialUrl: 'https://www.pmuy.gov.in'
  }
];

export const getSchemeById = (id: string): Scheme | undefined => {
  return mockSchemes.find(scheme => scheme.id === id);
};

export const getSchemesByCategory = (category: string): Scheme[] => {
  return mockSchemes.filter(scheme =>
    scheme.category.toLowerCase() === category.toLowerCase()
  );
};

export const getAllCategories = (): string[] => {
  const categories = new Set(mockSchemes.map(s => s.category));
  return Array.from(categories);
};
