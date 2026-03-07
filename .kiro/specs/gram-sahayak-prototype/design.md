# Design Document: Gram Sahayak Prototype

## Overview

Gram Sahayak is a voice-first web application that enables low-literacy rural Indian citizens to discover and understand government welfare schemes through natural conversation. The prototype validates the core value proposition: making 700+ government schemes accessible without requiring reading/writing skills or middlemen assistance.

The system architecture follows a client-side-first approach with minimal backend dependencies. The web application runs entirely in the browser, using LiveKit for real-time voice processing and fetching scheme data from myscheme.gov.in API. This design choice reduces infrastructure complexity for the prototype while enabling rapid iteration on the conversational experience.

Key design principles:
- Voice-first interaction with visual reinforcement
- Progressive information disclosure (one question at a time)
- Graceful degradation for network issues
- Privacy-by-design with local-only data storage
- Simple, high-contrast UI for low digital literacy users

## Architecture

### System Components

The Gram Sahayak prototype consists of five primary components:

1. **Voice Engine**: Handles bidirectional voice communication via LiveKit SDK
   - Speech-to-text (STT) conversion
   - Text-to-speech (TTS) playback
   - Audio capture and streaming
   - Connection management

2. **Conversation Manager**: Orchestrates dialogue flow and maintains context
   - Multi-turn conversation state machine
   - Intent recognition and response generation
   - Context tracking across conversation turns
   - Error recovery and clarification handling

3. **Scheme Repository**: Local cache of government scheme data
   - Fetches and stores scheme information from myscheme.gov.in
   - Indexes schemes by eligibility criteria
   - Handles data refresh and caching
   - Provides search and filtering capabilities

4. **Scheme Matcher**: AI-powered matching engine
   - Evaluates user profile against scheme eligibility criteria
   - Ranks schemes by relevance
   - Generates explanations for matches
   - Handles complex eligibility logic

5. **User Profile Manager**: Manages user demographic data
   - Collects information through conversational prompts
   - Validates and stores profile data
   - Persists data to browser localStorage
   - Provides profile retrieval and updates

### Technology Stack

- **Frontend Framework**: React with TypeScript for type safety
- **Voice Processing**: LiveKit SDK for WebRTC-based voice communication
- **State Management**: React Context API for application state
- **Storage**: Browser localStorage for user profiles and cached schemes
- **HTTP Client**: Fetch API for myscheme.gov.in integration
- **Build Tool**: Vite for fast development and optimized builds
- **Styling**: Tailwind CSS for responsive, accessible UI

### Data Flow

```
User Voice Input → LiveKit STT → Conversation Manager → Intent Processing
                                          ↓
                                    State Update
                                          ↓
                    ┌─────────────────────┴─────────────────────┐
                    ↓                                             ↓
            Scheme Matcher                              User Profile Manager
                    ↓                                             ↓
            Scheme Repository                           localStorage
                    ↓                                             ↓
            Response Generation ←─────────────────────────────────┘
                    ↓
            LiveKit TTS → Audio Playback → User
```

### Deployment Architecture

For the prototype phase:
- Static web application hosted on Vercel/Netlify
- LiveKit Cloud for voice processing infrastructure
- Direct API calls to myscheme.gov.in from browser
- No custom backend server required

## Components and Interfaces

### Voice Engine Component

**Responsibilities:**
- Manage LiveKit connection lifecycle
- Stream audio input to LiveKit STT service
- Receive and play TTS audio from LiveKit
- Provide visual feedback for voice activity
- Handle audio device permissions and errors

**Interface:**

```typescript
interface VoiceEngine {
  // Connection management
  connect(roomName: string, token: string): Promise<void>;
  disconnect(): Promise<void>;
  
  // Voice interaction
  startListening(): Promise<void>;
  stopListening(): void;
  speak(text: string, language: string): Promise<void>;
  
  // Event handlers
  onTranscript(callback: (text: string, isFinal: boolean) => void): void;
  onSpeechEnd(callback: () => void): void;
  onError(callback: (error: VoiceError) => void): void;
  
  // State queries
  isConnected(): boolean;
  isListening(): boolean;
  isSpeaking(): boolean;
}

interface VoiceError {
  code: 'CONNECTION_FAILED' | 'PERMISSION_DENIED' | 'STT_FAILED' | 'TTS_FAILED';
  message: string;
  recoverable: boolean;
}
```

### Conversation Manager Component

**Responsibilities:**
- Maintain conversation state and context
- Route user intents to appropriate handlers
- Generate contextually appropriate responses
- Handle conversation flow (greetings, confirmations, clarifications)
- Manage conversation history for context

**Interface:**

```typescript
interface ConversationManager {
  // Conversation lifecycle
  startSession(userId?: string): Session;
  endSession(sessionId: string): void;
  
  // Message processing
  processUserInput(sessionId: string, transcript: string): Promise<Response>;
  
  // Context management
  getContext(sessionId: string): ConversationContext;
  updateContext(sessionId: string, updates: Partial<ConversationContext>): void;
  
  // State persistence
  saveSession(sessionId: string): Promise<void>;
  loadSession(sessionId: string): Promise<Session>;
}

interface Session {
  id: string;
  userId?: string;
  startTime: Date;
  lastActivity: Date;
  context: ConversationContext;
  history: Message[];
}

interface ConversationContext {
  stage: 'greeting' | 'profile_collection' | 'scheme_discovery' | 'scheme_details' | 'application_guidance';
  currentTopic?: string;
  pendingQuestion?: string;
  userProfile?: Partial<UserProfile>;
  selectedScheme?: string;
  collectedDocuments?: string[];
}

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  intent?: string;
}

interface Response {
  text: string;
  action?: 'collect_profile' | 'show_schemes' | 'explain_eligibility' | 'list_documents';
  data?: any;
}
```

### Scheme Repository Component

**Responsibilities:**
- Fetch scheme data from myscheme.gov.in API
- Cache schemes in browser storage
- Provide search and filtering capabilities
- Handle data refresh logic
- Index schemes for efficient querying

**Interface:**

```typescript
interface SchemeRepository {
  // Data management
  initialize(): Promise<void>;
  refreshSchemes(): Promise<void>;
  
  // Querying
  getAllSchemes(): Scheme[];
  getSchemeById(id: string): Scheme | null;
  searchSchemes(query: SchemeQuery): Scheme[];
  
  // Cache management
  getCacheAge(): number;
  clearCache(): void;
}

interface Scheme {
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

interface EligibilityCriteria {
  ageMin?: number;
  ageMax?: number;
  gender?: 'male' | 'female' | 'other' | 'any';
  incomeMax?: number;
  occupation?: string[];
  state?: string[];
  category?: string[]; // SC/ST/OBC/General
  familySize?: { min?: number; max?: number };
  customRules?: string[]; // Complex rules as text
}

interface Document {
  name: string;
  nameHindi: string;
  description: string;
  mandatory: boolean;
}

interface SchemeQuery {
  category?: string;
  state?: string;
  eligibility?: Partial<UserProfile>;
  searchText?: string;
}
```

### Scheme Matcher Component

**Responsibilities:**
- Evaluate user eligibility for schemes
- Rank schemes by relevance
- Generate human-readable explanations
- Handle complex eligibility logic

**Interface:**

```typescript
interface SchemeMatcher {
  // Matching operations
  findEligibleSchemes(profile: UserProfile): MatchResult[];
  checkEligibility(profile: UserProfile, schemeId: string): EligibilityResult;
  
  // Ranking
  rankSchemes(matches: MatchResult[], profile: UserProfile): MatchResult[];
}

interface MatchResult {
  scheme: Scheme;
  eligible: boolean;
  confidence: number; // 0-1
  matchedCriteria: string[];
  explanation: string;
  explanationHindi: string;
}

interface EligibilityResult {
  eligible: boolean;
  matchedCriteria: string[];
  unmatchedCriteria: string[];
  explanation: string;
  explanationHindi: string;
}
```

### User Profile Manager Component

**Responsibilities:**
- Collect user demographic information
- Validate profile data
- Persist to localStorage
- Provide profile CRUD operations

**Interface:**

```typescript
interface UserProfileManager {
  // Profile operations
  createProfile(data: Partial<UserProfile>): UserProfile;
  getProfile(userId: string): UserProfile | null;
  updateProfile(userId: string, updates: Partial<UserProfile>): UserProfile;
  deleteProfile(userId: string): void;
  
  // Validation
  validateProfileField(field: keyof UserProfile, value: any): ValidationResult;
  isProfileComplete(profile: Partial<UserProfile>): boolean;
}

interface UserProfile {
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

interface ValidationResult {
  valid: boolean;
  error?: string;
}
```

## Data Models

### Core Data Structures

**User Profile Storage (localStorage)**

```typescript
// Key: 'gram_sahayak_profile_{userId}'
{
  id: string;
  age: number;
  gender: 'male' | 'female' | 'other';
  state: string;
  district: string;
  occupation: string;
  incomeCategory: 'BPL' | 'APL' | 'AAY';
  familySize: number;
  category?: 'SC' | 'ST' | 'OBC' | 'General';
  createdAt: string; // ISO date
  updatedAt: string; // ISO date
}
```

**Scheme Cache (localStorage)**

```typescript
// Key: 'gram_sahayak_schemes'
{
  schemes: Scheme[];
  lastFetched: string; // ISO date
  version: string;
}
```

**Session State (sessionStorage)**

```typescript
// Key: 'gram_sahayak_session_{sessionId}'
{
  id: string;
  userId?: string;
  startTime: string;
  lastActivity: string;
  context: ConversationContext;
  history: Message[];
}
```

### State Machine for Conversation Flow

The Conversation Manager implements a state machine with the following states:

1. **GREETING**: Initial welcome and introduction
   - Transitions to: PROFILE_COLLECTION

2. **PROFILE_COLLECTION**: Gathering user demographic information
   - Sub-states: age → gender → state → district → occupation → income → family_size
   - Transitions to: SCHEME_DISCOVERY (when profile complete)

3. **SCHEME_DISCOVERY**: Presenting matched schemes
   - Transitions to: SCHEME_DETAILS (user selects scheme)
   - Transitions to: PROFILE_COLLECTION (user wants to update profile)

4. **SCHEME_DETAILS**: Explaining specific scheme
   - Transitions to: APPLICATION_GUIDANCE (user wants to apply)
   - Transitions to: SCHEME_DISCOVERY (user wants other schemes)

5. **APPLICATION_GUIDANCE**: Listing required documents and next steps
   - Transitions to: SCHEME_DISCOVERY (user wants other schemes)
   - Transitions to: END (user is satisfied)

6. **END**: Conversation conclusion
   - Transitions to: GREETING (user starts new conversation)

### Error States and Recovery

Each component maintains error state with recovery strategies:

```typescript
interface ErrorState {
  component: string;
  errorCode: string;
  message: string;
  timestamp: Date;
  retryCount: number;
  recoveryAction: 'retry' | 'fallback' | 'user_action' | 'fatal';
}
```

### Data Validation Rules

**User Profile Validation:**
- Age: 0-120, required
- Gender: enum value, required
- State: valid Indian state name, required
- District: non-empty string, required
- Occupation: non-empty string, required
- Income Category: enum value, required
- Family Size: 1-50, required
- Category: enum value, optional

**Scheme Data Validation:**
- All required fields must be present
- Eligibility criteria must have at least one criterion
- Required documents list cannot be empty
- URLs must be valid HTTP/HTTPS


## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Text-to-Speech Invocation

*For any* response text generated by the system, the Voice Engine SHALL invoke the TTS function and produce audio output.

**Validates: Requirements 1.3**

### Property 2: Listening State Visual Feedback

*For any* Voice Engine state, when the listening flag is true, the UI SHALL display the active listening indicator.

**Validates: Requirements 1.4**

### Property 3: Scheme Data Completeness

*For any* scheme fetched and stored in the Scheme Repository, all required fields (name, description, eligibility criteria, benefits, required documents) SHALL be present and non-empty.

**Validates: Requirements 2.2**

### Property 4: Scheme Retrieval by Criteria

*For any* scheme stored in the repository with specific category, state, or eligibility parameters, querying by those parameters SHALL return that scheme in the results.

**Validates: Requirements 2.5**

### Property 5: Profile Data Persistence Round-Trip

*For any* valid user profile saved to localStorage, retrieving it SHALL return an equivalent profile with all fields intact.

**Validates: Requirements 3.6**

### Property 6: Profile Field Completeness

*For any* completed user profile, all required fields (age, gender, state, district, occupation, income category, family size) SHALL be present and valid.

**Validates: Requirements 3.2**

### Property 7: Profile Confirmation Echo

*For any* user input during profile collection, the system SHALL generate a confirmation response that includes the provided information.

**Validates: Requirements 3.3**

### Property 8: Single Question at a Time

*For any* conversation state during profile collection, at most one profile field SHALL be marked as pending/awaiting input.

**Validates: Requirements 3.4**

### Property 9: Eligibility Matching Correctness

*For any* user profile and scheme combination, if the Scheme Matcher returns the scheme as eligible, then the Eligibility Engine SHALL also evaluate it as eligible when checked directly.

**Validates: Requirements 4.1, 5.1**

### Property 10: Scheme Ranking Order

*For any* list of matched schemes returned by the Scheme Matcher, the schemes SHALL be ordered by descending relevance score.

**Validates: Requirements 4.2**

### Property 11: Scheme Description Generation

*For any* scheme in the repository, the Conversation Manager SHALL be able to generate a non-empty description in simple language.

**Validates: Requirements 4.3**

### Property 12: Scheme Presentation Limit

*For any* scheme list presentation, the number of schemes shown at once SHALL not exceed 3.

**Validates: Requirements 4.4**

### Property 13: Eligibility Explanation Presence

*For any* scheme matched to a user profile, the match result SHALL include a non-empty explanation of why the user is eligible.

**Validates: Requirements 4.6**

### Property 14: Eligibility Determination Boolean

*For any* eligibility evaluation result, the eligible field SHALL be either true or false (boolean).

**Validates: Requirements 5.2**

### Property 15: Ineligibility Explanation Completeness

*For any* eligibility evaluation where eligible is false, the result SHALL include a non-empty list of unmatched criteria.

**Validates: Requirements 5.3**

### Property 16: Document Explanation Generation

*For any* required document in a scheme, the system SHALL be able to generate a non-empty explanation in simple terms.

**Validates: Requirements 6.2**

### Property 17: Document Status Tracking

*For any* document in the application guidance flow, the system SHALL allow marking it with a status of either "have" or "need to get".

**Validates: Requirements 6.4**

### Property 18: Transcription Display Synchronization

*For any* speech-to-text transcription event, the transcribed text SHALL be displayed on screen while processing is active.

**Validates: Requirements 7.3**

### Property 19: Response Text Display Synchronization

*For any* text-to-speech event, the spoken text SHALL be displayed on screen simultaneously with audio playback.

**Validates: Requirements 7.4**

### Property 20: Navigation Depth Constraint

*For any* navigation path in the application, the depth SHALL not exceed 2 levels.

**Validates: Requirements 7.6**

### Property 21: Session Context Persistence

*For any* session, adding a message to the conversation history SHALL preserve all previously added messages in order.

**Validates: Requirements 8.1**

### Property 22: Context-Aware Follow-up Processing

*For any* follow-up question in a session, the Conversation Manager SHALL have access to the previous conversation context when generating a response.

**Validates: Requirements 8.2**

### Property 23: State Persistence Round-Trip

*For any* session state saved during inactivity or connection loss, loading the saved state SHALL restore all context fields and conversation history.

**Validates: Requirements 9.2**

### Property 24: Error Logging Without PII

*For any* error logged by the system, the log entry SHALL not contain personally identifiable information (age, gender, state, district, occupation, income, family size).

**Validates: Requirements 9.6**

### Property 25: Profile Storage Locality

*For any* user profile stored by the system, the profile data SHALL exist only in browser localStorage and SHALL not be transmitted to external servers except LiveKit for voice processing.

**Validates: Requirements 10.1, 10.2**

### Property 26: Audio Recording Non-Persistence

*For any* audio processing operation, after the operation completes, no audio recording SHALL remain in browser storage or memory.

**Validates: Requirements 10.5**

## Error Handling

### Error Categories

The Gram Sahayak prototype handles errors across four categories:

1. **Voice Processing Errors**
   - Microphone permission denied
   - LiveKit connection failure
   - Speech-to-text failure
   - Text-to-speech failure
   - Audio device not available

2. **Network Errors**
   - Internet connection lost
   - API fetch failure (myscheme.gov.in)
   - LiveKit service unavailable
   - Timeout errors

3. **Data Errors**
   - Invalid user input
   - Profile validation failure
   - Scheme data corruption
   - localStorage quota exceeded

4. **Application Errors**
   - Conversation state corruption
   - Unexpected component failure
   - Browser compatibility issues

### Error Handling Strategies

**Voice Processing Errors:**

```typescript
// Microphone Permission Denied
- Display clear message: "We need microphone access to help you"
- Show browser-specific instructions for granting permission
- Provide "Try Again" button
- No automatic retry (requires user action)

// LiveKit Connection Failure
- Retry connection up to 3 times with exponential backoff (1s, 2s, 4s)
- Display connection status indicator
- After 3 failures, show troubleshooting steps:
  - Check internet connection
  - Refresh the page
  - Try a different browser
- Log error details for debugging

// STT/TTS Failure
- Retry the specific operation once
- If retry fails, display error message
- Offer to continue with text input as fallback
- Maintain conversation state
```

**Network Errors:**

```typescript
// Internet Connection Lost
- Detect via navigator.onLine and failed fetch attempts
- Immediately save current session state to sessionStorage
- Display prominent offline indicator
- Queue any pending operations
- When connection restored:
  - Restore session state
  - Retry queued operations
  - Resume conversation from last point

// API Fetch Failure (myscheme.gov.in)
- Use cached scheme data if available
- Display warning: "Using cached data, may not be latest"
- Log error with timestamp
- Retry fetch in background every 5 minutes
- If no cached data available:
  - Display error message
  - Offer to retry manually
  - Provide fallback contact information

// Timeout Errors
- Set timeout of 10 seconds for API calls
- Set timeout of 5 seconds for LiveKit operations
- On timeout, treat as network error and follow above strategy
```

**Data Errors:**

```typescript
// Invalid User Input
- Validate input against expected format
- Provide specific feedback: "Age should be a number between 0 and 120"
- Ask user to provide input again
- Limit to 3 retry attempts
- After 3 attempts, offer to skip field or restart

// Profile Validation Failure
- Check all required fields present
- Validate each field against rules
- Display list of validation errors
- Allow user to correct specific fields
- Do not proceed until profile is valid

// Scheme Data Corruption
- Detect via schema validation on load
- Clear corrupted cache
- Fetch fresh data from API
- If fetch fails, display error and prevent scheme operations
- Log corruption details for debugging

// localStorage Quota Exceeded
- Catch QuotaExceededError
- Clear old session data (older than 7 days)
- Retry storage operation
- If still fails, warn user and operate in memory-only mode
- Inform user that data won't persist
```

**Application Errors:**

```typescript
// Conversation State Corruption
- Detect via state validation checks
- Attempt to recover by resetting to last known good state
- If recovery fails, offer to restart conversation
- Preserve user profile data
- Log corruption details

// Unexpected Component Failure
- Catch errors at component boundary (Error Boundary)
- Display user-friendly error message
- Offer to reload the page
- Log full error stack trace
- Preserve critical data before reload

// Browser Compatibility Issues
- Detect unsupported features on load
- Display compatibility warning with supported browser list
- Gracefully degrade features where possible
- Prevent app load if critical features unavailable
```

### Error Recovery Patterns

**Retry with Exponential Backoff:**
```typescript
async function retryWithBackoff<T>(
  operation: () => Promise<T>,
  maxRetries: number = 3,
  baseDelay: number = 1000
): Promise<T> {
  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      return await operation();
    } catch (error) {
      if (attempt === maxRetries - 1) throw error;
      const delay = baseDelay * Math.pow(2, attempt);
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }
  throw new Error('Max retries exceeded');
}
```

**Graceful Degradation:**
- If voice fails, offer text input
- If API fails, use cached data
- If TTS fails, show text only
- If STT fails, allow typing

**State Preservation:**
- Save session state on every significant update
- Use sessionStorage for temporary state
- Use localStorage for persistent data
- Implement state versioning for migration

### User-Facing Error Messages

All error messages follow these principles:
- Written in simple Hindi and English
- Explain what happened in non-technical terms
- Provide clear next steps
- Avoid blame ("Something went wrong" not "You did something wrong")
- Include visual icons for clarity

Example error messages:

```
Voice Error:
"हम आपकी आवाज़ नहीं सुन पा रहे हैं। कृपया माइक्रोफ़ोन की अनुमति दें।"
"We cannot hear you. Please allow microphone access."
[Try Again Button]

Network Error:
"इंटरनेट कनेक्शन नहीं है। हम आपकी जानकारी सुरक्षित रख रहे हैं।"
"No internet connection. We are keeping your information safe."
[Retry When Online]

Data Error:
"कृपया सही उम्र बताएं (0 से 120 के बीच)।"
"Please provide a valid age (between 0 and 120)."
[Try Again]
```

## Testing Strategy

### Dual Testing Approach

The Gram Sahayak prototype requires both unit testing and property-based testing to ensure comprehensive correctness:

**Unit Tests** focus on:
- Specific examples and edge cases
- Integration points between components
- Error conditions and recovery
- UI component rendering
- Browser API interactions

**Property-Based Tests** focus on:
- Universal properties that hold for all inputs
- Data transformation correctness
- State machine transitions
- Validation logic across input space
- Round-trip properties (serialization, state persistence)

Both testing approaches are complementary and necessary. Unit tests catch concrete bugs in specific scenarios, while property tests verify general correctness across a wide input space.

### Property-Based Testing Configuration

**Framework Selection:**
- **JavaScript/TypeScript**: Use `fast-check` library for property-based testing
- Integrates well with Jest/Vitest test runners
- Provides rich set of generators for common data types
- Supports custom generators for domain-specific types

**Test Configuration:**
- Each property test MUST run minimum 100 iterations
- Use deterministic seed for reproducibility
- Configure timeout of 30 seconds per property test
- Enable verbose mode for debugging failures

**Property Test Structure:**

```typescript
import fc from 'fast-check';

describe('Feature: gram-sahayak-prototype, Property 5: Profile Data Persistence Round-Trip', () => {
  it('should preserve all profile fields after save and load', () => {
    fc.assert(
      fc.property(
        userProfileArbitrary(), // Custom generator
        (profile) => {
          // Save profile
          const manager = new UserProfileManager();
          manager.saveProfile(profile);
          
          // Load profile
          const loaded = manager.getProfile(profile.id);
          
          // Assert equivalence
          expect(loaded).toEqual(profile);
        }
      ),
      { numRuns: 100 }
    );
  });
});
```

**Custom Generators:**

```typescript
// Generator for valid user profiles
function userProfileArbitrary(): fc.Arbitrary<UserProfile> {
  return fc.record({
    id: fc.uuid(),
    age: fc.integer({ min: 0, max: 120 }),
    gender: fc.constantFrom('male', 'female', 'other'),
    state: fc.constantFrom('Uttar Pradesh', 'Bihar', 'Maharashtra', 'Rajasthan'),
    district: fc.string({ minLength: 1, maxLength: 50 }),
    occupation: fc.constantFrom('farmer', 'laborer', 'shopkeeper', 'student'),
    incomeCategory: fc.constantFrom('BPL', 'APL', 'AAY'),
    familySize: fc.integer({ min: 1, max: 20 }),
    category: fc.option(fc.constantFrom('SC', 'ST', 'OBC', 'General')),
    createdAt: fc.date(),
    updatedAt: fc.date()
  });
}

// Generator for schemes
function schemeArbitrary(): fc.Arbitrary<Scheme> {
  return fc.record({
    id: fc.uuid(),
    name: fc.string({ minLength: 5, maxLength: 100 }),
    nameHindi: fc.string({ minLength: 5, maxLength: 100 }),
    description: fc.string({ minLength: 20, maxLength: 500 }),
    descriptionHindi: fc.string({ minLength: 20, maxLength: 500 }),
    category: fc.constantFrom('health', 'education', 'agriculture', 'housing'),
    state: fc.option(fc.constantFrom('Uttar Pradesh', 'Bihar', 'Maharashtra')),
    benefits: fc.array(fc.string({ minLength: 10, maxLength: 100 }), { minLength: 1, maxLength: 5 }),
    eligibilityCriteria: eligibilityCriteriaArbitrary(),
    requiredDocuments: fc.array(documentArbitrary(), { minLength: 1, maxLength: 10 }),
    applicationProcess: fc.string({ minLength: 50, maxLength: 500 }),
    officialUrl: fc.webUrl()
  });
}

// Generator for eligibility criteria
function eligibilityCriteriaArbitrary(): fc.Arbitrary<EligibilityCriteria> {
  return fc.record({
    ageMin: fc.option(fc.integer({ min: 0, max: 100 })),
    ageMax: fc.option(fc.integer({ min: 0, max: 120 })),
    gender: fc.option(fc.constantFrom('male', 'female', 'other', 'any')),
    incomeMax: fc.option(fc.integer({ min: 10000, max: 1000000 })),
    occupation: fc.option(fc.array(fc.string(), { minLength: 1, maxLength: 5 })),
    state: fc.option(fc.array(fc.string(), { minLength: 1, maxLength: 5 })),
    category: fc.option(fc.array(fc.constantFrom('SC', 'ST', 'OBC', 'General'))),
    familySize: fc.option(fc.record({
      min: fc.option(fc.integer({ min: 1, max: 10 })),
      max: fc.option(fc.integer({ min: 1, max: 20 }))
    }))
  });
}
```

### Unit Testing Strategy

**Component Testing:**
- Test each component in isolation with mocked dependencies
- Use React Testing Library for UI components
- Mock LiveKit SDK for voice engine tests
- Mock localStorage for persistence tests

**Integration Testing:**
- Test component interactions
- Test conversation flow through multiple states
- Test error propagation and recovery
- Test data flow from API to UI

**Edge Cases to Test:**
- Empty inputs
- Maximum length inputs
- Special characters in text
- Boundary values (age 0, age 120)
- Missing optional fields
- Malformed API responses
- Concurrent operations

**Example Unit Tests:**

```typescript
describe('UserProfileManager', () => {
  it('should reject age below 0', () => {
    const manager = new UserProfileManager();
    const result = manager.validateProfileField('age', -1);
    expect(result.valid).toBe(false);
    expect(result.error).toContain('age');
  });

  it('should accept valid profile', () => {
    const manager = new UserProfileManager();
    const profile = {
      age: 35,
      gender: 'male',
      state: 'Bihar',
      district: 'Patna',
      occupation: 'farmer',
      incomeCategory: 'BPL',
      familySize: 5
    };
    const created = manager.createProfile(profile);
    expect(created.id).toBeDefined();
    expect(created.age).toBe(35);
  });
});

describe('SchemeMatcher', () => {
  it('should not match scheme when age is below minimum', () => {
    const matcher = new SchemeMatcher(mockRepository);
    const profile = { age: 15, /* other fields */ };
    const scheme = {
      eligibilityCriteria: { ageMin: 18, ageMax: 60 }
    };
    const result = matcher.checkEligibility(profile, scheme.id);
    expect(result.eligible).toBe(false);
    expect(result.unmatchedCriteria).toContain('age');
  });
});
```

### Test Coverage Goals

- **Line Coverage**: Minimum 80%
- **Branch Coverage**: Minimum 75%
- **Function Coverage**: Minimum 85%
- **Property Tests**: All 26 correctness properties implemented
- **Critical Paths**: 100% coverage for voice interaction, eligibility matching, and data persistence

### Testing Tools and Infrastructure

**Test Runner**: Vitest (fast, ESM-native, compatible with Vite)

**Testing Libraries:**
- `@testing-library/react` - Component testing
- `@testing-library/user-event` - User interaction simulation
- `fast-check` - Property-based testing
- `msw` - API mocking
- `vitest-localstorage-mock` - localStorage mocking

**CI/CD Integration:**
- Run all tests on every pull request
- Block merge if tests fail
- Generate coverage reports
- Run property tests with fixed seed for consistency

**Test Organization:**

```
src/
  components/
    VoiceEngine/
      VoiceEngine.tsx
      VoiceEngine.test.tsx
      VoiceEngine.properties.test.tsx
  services/
    SchemeRepository/
      SchemeRepository.ts
      SchemeRepository.test.ts
      SchemeRepository.properties.test.ts
```

### Property Test Tagging

Each property-based test MUST include a comment tag referencing the design document property:

```typescript
/**
 * Feature: gram-sahayak-prototype
 * Property 5: Profile Data Persistence Round-Trip
 * 
 * For any valid user profile saved to localStorage,
 * retrieving it SHALL return an equivalent profile with all fields intact.
 */
describe('Property 5: Profile Data Persistence Round-Trip', () => {
  // test implementation
});
```

This tagging ensures traceability from requirements → design properties → test implementation.

