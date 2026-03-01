# Implementation Plan: Gram Sahayak Prototype

## Overview

This implementation plan breaks down the Gram Sahayak prototype into discrete coding tasks. The prototype is a voice-first web application built with React and TypeScript that enables low-literacy rural citizens to discover government welfare schemes through natural conversation. The implementation follows a progressive approach: core infrastructure first, then data layer, conversation logic, voice integration, and finally UI polish.

## Tasks

- [ ] 1. Set up project structure and core infrastructure
  - Initialize React + TypeScript + Vite project
  - Configure Tailwind CSS for styling
  - Set up testing infrastructure (Vitest, React Testing Library, fast-check)
  - Create directory structure for components, services, and types
  - Configure ESLint and TypeScript strict mode
  - _Requirements: 7.1, 7.2, 7.5_

- [ ] 2. Implement data models and type definitions
  - [ ] 2.1 Create TypeScript interfaces for core data models
    - Define UserProfile, Scheme, EligibilityCriteria, Document types
    - Define conversation types (Session, Message, ConversationContext)
    - Define error types (VoiceError, ErrorState)
    - _Requirements: 3.2, 2.2, 8.1_
  
  - [ ]* 2.2 Write property test for data model validation
    - **Property 6: Profile Field Completeness**
    - **Validates: Requirements 3.2**

- [ ] 3. Implement User Profile Manager
  - [ ] 3.1 Create UserProfileManager service
    - Implement createProfile, getProfile, updateProfile, deleteProfile methods
    - Implement localStorage persistence logic
    - Implement profile field validation with ValidationResult
    - Handle localStorage quota exceeded errors
    - _Requirements: 3.2, 3.6, 10.1_
  
  - [ ]* 3.2 Write property test for profile persistence
    - **Property 5: Profile Data Persistence Round-Trip**
    - **Validates: Requirements 3.6**
  
  - [ ] 3.3 Write unit tests for UserProfileManager
    - Test validation for each profile field (age, gender, state, etc.)
    - Test edge cases (age 0, age 120, empty strings)
    - Test localStorage quota exceeded handling
    - _Requirements: 3.2_

- [ ] 4. Implement Scheme Repository
  - [ ] 4.1 Create SchemeRepository service
    - Implement initialize and refreshSchemes methods
    - Implement fetch from myscheme.gov.in API with error handling
    - Implement localStorage caching with 24-hour expiry
    - Implement getAllSchemes, getSchemeById, searchSchemes methods
    - Create scheme indexing by category, state, and eligibility parameters
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_
  
  - [ ]* 4.2 Write property test for scheme data completeness
    - **Property 3: Scheme Data Completeness**
    - **Validates: Requirements 2.2**
  
  - [ ]* 4.3 Write property test for scheme retrieval
    - **Property 4: Scheme Retrieval by Criteria**
    - **Validates: Requirements 2.5**
  
  - [ ] 4.4 Write unit tests for SchemeRepository
    - Test API fetch failure with fallback to cache
    - Test cache expiry logic
    - Test search and filtering operations
    - Mock fetch API responses
    - _Requirements: 2.4, 2.5_

- [ ] 5. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 6. Implement Scheme Matcher and Eligibility Engine
  - [ ] 6.1 Create SchemeMatcher service
    - Implement findEligibleSchemes method with eligibility evaluation logic
    - Implement checkEligibility method for single scheme evaluation
    - Implement rankSchemes method with relevance scoring
    - Generate human-readable explanations for matches and eligibility
    - Handle complex eligibility rules (age ranges, income thresholds, categories)
    - _Requirements: 4.1, 4.2, 4.6, 5.1, 5.2, 5.3, 5.5_
  
  - [ ]* 6.2 Write property test for eligibility matching correctness
    - **Property 9: Eligibility Matching Correctness**
    - **Validates: Requirements 4.1, 5.1**
  
  - [ ]* 6.3 Write property test for scheme ranking order
    - **Property 10: Scheme Ranking Order**
    - **Validates: Requirements 4.2**
  
  - [ ]* 6.4 Write property test for eligibility determination
    - **Property 14: Eligibility Determination Boolean**
    - **Validates: Requirements 5.2**
  
  - [ ]* 6.5 Write property test for ineligibility explanation
    - **Property 15: Ineligibility Explanation Completeness**
    - **Validates: Requirements 5.3**
  
  - [ ] 6.6 Write unit tests for SchemeMatcher
    - Test age boundary conditions (below min, above max, within range)
    - Test income threshold matching
    - Test gender and category matching
    - Test complex multi-criteria scenarios
    - _Requirements: 5.1, 5.5_

- [ ] 7. Implement Conversation Manager
  - [ ] 7.1 Create ConversationManager service
    - Implement state machine with states: GREETING, PROFILE_COLLECTION, SCHEME_DISCOVERY, SCHEME_DETAILS, APPLICATION_GUIDANCE
    - Implement startSession, endSession, processUserInput methods
    - Implement context management (getContext, updateContext)
    - Implement session persistence (saveSession, loadSession) to sessionStorage
    - Handle conversation history tracking
    - _Requirements: 8.1, 8.2, 8.3, 8.5, 9.2_
  
  - [ ] 7.2 Implement profile collection conversation flow
    - Create prompts for each profile field (age, gender, state, district, occupation, income, family size)
    - Implement one-question-at-a-time logic
    - Implement confirmation echo for user inputs
    - Handle clarification requests and corrections
    - _Requirements: 3.1, 3.3, 3.4, 3.5, 8.4_
  
  - [ ] 7.3 Implement scheme discovery conversation flow
    - Generate simple language descriptions for schemes
    - Implement 3-scheme-at-a-time presentation limit
    - Handle user selection and interest expressions
    - Generate eligibility explanations
    - _Requirements: 4.3, 4.4, 4.5, 4.6_
  
  - [ ] 7.4 Implement application guidance conversation flow
    - List required documents for selected scheme
    - Generate simple explanations for each document
    - Implement document status tracking (have/need to get)
    - Generate next steps summary
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_
  
  - [ ]* 7.5 Write property test for session context persistence
    - **Property 21: Session Context Persistence**
    - **Validates: Requirements 8.1**
  
  - [ ]* 7.6 Write property test for context-aware follow-up
    - **Property 22: Context-Aware Follow-up Processing**
    - **Validates: Requirements 8.2**
  
  - [ ]* 7.7 Write property test for state persistence round-trip
    - **Property 23: State Persistence Round-Trip**
    - **Validates: Requirements 9.2**
  
  - [ ]* 7.8 Write property test for single question constraint
    - **Property 8: Single Question at a Time**
    - **Validates: Requirements 3.4**
  
  - [ ]* 7.9 Write property test for profile confirmation echo
    - **Property 7: Profile Confirmation Echo**
    - **Validates: Requirements 3.3**
  
  - [ ]* 7.10 Write property test for scheme presentation limit
    - **Property 12: Scheme Presentation Limit**
    - **Validates: Requirements 4.4**
  
  - [ ] 7.11 Write unit tests for ConversationManager
    - Test state transitions for all conversation flows
    - Test session save and load with various states
    - Test conversation history preservation
    - Test error recovery and clarification handling
    - _Requirements: 8.1, 8.2, 8.5, 9.2_

- [ ] 8. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 9. Implement Voice Engine with LiveKit integration
  - [ ] 9.1 Create VoiceEngine service
    - Implement LiveKit SDK integration (connect, disconnect)
    - Implement audio capture and streaming (startListening, stopListening)
    - Implement speech-to-text event handling
    - Implement text-to-speech playback (speak method)
    - Implement connection state management
    - Handle microphone permissions
    - _Requirements: 1.1, 1.2, 1.3, 1.6_
  
  - [ ] 9.2 Implement error handling for voice operations
    - Handle CONNECTION_FAILED with retry logic (3 attempts, exponential backoff)
    - Handle PERMISSION_DENIED with user guidance
    - Handle STT_FAILED and TTS_FAILED with retry and fallback
    - Implement VoiceError type with recovery strategies
    - _Requirements: 1.5, 9.1, 9.3, 9.4, 9.5_
  
  - [ ]* 9.3 Write property test for TTS invocation
    - **Property 1: Text-to-Speech Invocation**
    - **Validates: Requirements 1.3**
  
  - [ ]* 9.4 Write property test for listening state feedback
    - **Property 2: Listening State Visual Feedback**
    - **Validates: Requirements 1.4**
  
  - [ ] 9.5 Write unit tests for VoiceEngine
    - Test connection lifecycle with mocked LiveKit SDK
    - Test error scenarios (permission denied, connection failed)
    - Test retry logic with exponential backoff
    - Test audio recording non-persistence
    - _Requirements: 1.1, 1.5, 9.5, 10.5_

- [ ] 10. Implement React UI components
  - [ ] 10.1 Create main App component with routing
    - Set up React Context for global state (user profile, session, schemes)
    - Implement error boundary for application-level error handling
    - Create main layout structure
    - _Requirements: 7.1, 7.6, 9.6_
  
  - [ ] 10.2 Create VoiceButton component
    - Implement prominent microphone button with large touch target
    - Show visual indicator for listening state (pulsing animation)
    - Display connection status
    - Handle click events to start/stop listening
    - _Requirements: 1.1, 1.4, 7.1, 7.2_
  
  - [ ] 10.3 Create TranscriptDisplay component
    - Display real-time speech-to-text transcription
    - Show system responses as text during TTS playback
    - Use large, high-contrast text
    - Auto-scroll to latest message
    - _Requirements: 7.3, 7.4, 7.2_
  
  - [ ] 10.4 Create ConversationView component
    - Display conversation history with user/assistant messages
    - Show visual icons for message types
    - Implement simple navigation (back button only)
    - Display current conversation stage indicator
    - _Requirements: 7.5, 7.6, 8.1_
  
  - [ ] 10.5 Create SchemeCard component
    - Display scheme name, description, and benefits
    - Show eligibility status with visual indicator
    - Implement selection interaction
    - Use high-contrast colors and large text
    - _Requirements: 4.3, 4.4, 7.2_
  
  - [ ] 10.6 Create ErrorDisplay component
    - Show user-friendly error messages in Hindi and English
    - Display appropriate icons for error types
    - Provide retry/action buttons
    - Implement auto-dismiss for non-critical errors
    - _Requirements: 1.5, 9.1, 9.2, 9.3_
  
  - [ ] 10.7 Create OfflineIndicator component
    - Detect online/offline status using navigator.onLine
    - Display prominent offline banner
    - Show reconnection status
    - _Requirements: 9.1, 9.2_
  
  - [ ]* 10.8 Write property test for transcription display sync
    - **Property 18: Transcription Display Synchronization**
    - **Validates: Requirements 7.3**
  
  - [ ]* 10.9 Write property test for response text display sync
    - **Property 19: Response Text Display Synchronization**
    - **Validates: Requirements 7.4**
  
  - [ ]* 10.10 Write property test for navigation depth constraint
    - **Property 20: Navigation Depth Constraint**
    - **Validates: Requirements 7.6**
  
  - [ ] 10.11 Write unit tests for UI components
    - Test component rendering with various props
    - Test user interactions (button clicks, navigation)
    - Test error state display
    - Test responsive behavior
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6_

- [ ] 11. Implement privacy and data security features
  - [ ] 11.1 Create data management utilities
    - Implement clear all data function
    - Implement audio recording cleanup after processing
    - Create privacy notice content (Hindi and English)
    - _Requirements: 10.3, 10.4, 10.5_
  
  - [ ] 11.2 Implement error logging without PII
    - Create logging utility that sanitizes profile data
    - Implement error log structure with component, code, message, timestamp
    - Test PII removal from error logs
    - _Requirements: 9.6, 10.1_
  
  - [ ]* 11.3 Write property test for error logging without PII
    - **Property 24: Error Logging Without PII**
    - **Validates: Requirements 9.6**
  
  - [ ]* 11.4 Write property test for profile storage locality
    - **Property 25: Profile Storage Locality**
    - **Validates: Requirements 10.1, 10.2**
  
  - [ ]* 11.5 Write property test for audio recording non-persistence
    - **Property 26: Audio Recording Non-Persistence**
    - **Validates: Requirements 10.5**

- [ ] 12. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 13. Wire components together and implement main application flow
  - [ ] 13.1 Integrate VoiceEngine with ConversationManager
    - Connect STT output to processUserInput
    - Connect response text to TTS input
    - Implement conversation loop (listen → process → respond → listen)
    - Handle voice errors in conversation flow
    - _Requirements: 1.1, 1.2, 1.3, 8.1, 8.2_
  
  - [ ] 13.2 Integrate ConversationManager with SchemeRepository and SchemeMatcher
    - Load schemes on app initialization
    - Call SchemeMatcher when profile is complete
    - Fetch scheme details for conversation responses
    - Handle scheme data refresh
    - _Requirements: 2.1, 2.3, 4.1, 4.2_
  
  - [ ] 13.3 Integrate UserProfileManager with ConversationManager
    - Save profile updates during conversation
    - Load existing profile on session start
    - Handle profile validation errors in conversation
    - _Requirements: 3.1, 3.2, 3.6_
  
  - [ ] 13.4 Implement session management
    - Auto-save session state every 30 seconds
    - Detect 5-minute inactivity and save state
    - Restore session on page reload
    - Handle session expiry (7 days)
    - _Requirements: 8.6, 9.2_
  
  - [ ] 13.5 Implement network error handling
    - Detect connection loss and save state
    - Queue operations during offline mode
    - Retry operations when connection restored
    - Use cached scheme data when API unavailable
    - _Requirements: 9.1, 9.2, 2.4_
  
  - [ ]* 13.6 Write integration tests for main application flow
    - Test complete profile collection flow
    - Test scheme discovery and selection flow
    - Test application guidance flow
    - Test error recovery scenarios
    - _Requirements: 3.1, 4.1, 6.1, 8.1, 9.2_

- [ ] 14. Implement remaining correctness properties as tests
  - [ ]* 14.1 Write property test for scheme description generation
    - **Property 11: Scheme Description Generation**
    - **Validates: Requirements 4.3**
  
  - [ ]* 14.2 Write property test for eligibility explanation presence
    - **Property 13: Eligibility Explanation Presence**
    - **Validates: Requirements 4.6**
  
  - [ ]* 14.3 Write property test for document explanation generation
    - **Property 16: Document Explanation Generation**
    - **Validates: Requirements 6.2**
  
  - [ ]* 14.4 Write property test for document status tracking
    - **Property 17: Document Status Tracking**
    - **Validates: Requirements 6.4**

- [ ] 15. Final polish and accessibility
  - [ ] 15.1 Implement responsive design
    - Test on mobile, tablet, and desktop viewports
    - Ensure touch targets are minimum 44x44px
    - Optimize layout for small screens
    - _Requirements: 7.2_
  
  - [ ] 15.2 Add loading states and transitions
    - Show loading indicators for API calls
    - Add smooth transitions between conversation states
    - Implement skeleton screens for scheme loading
    - _Requirements: 7.5_
  
  - [ ] 15.3 Implement accessibility features
    - Add ARIA labels for all interactive elements
    - Ensure keyboard navigation works
    - Test with screen readers
    - Verify color contrast ratios (WCAG AA minimum)
    - _Requirements: 7.2, 7.5_
  
  - [ ] 15.4 Add Hindi language support
    - Implement bilingual UI labels (Hindi/English)
    - Configure LiveKit for Hindi STT/TTS
    - Test Hindi voice interaction
    - _Requirements: 1.6, 4.3, 6.2_

- [ ] 16. Final checkpoint - Ensure all tests pass and prototype is ready
  - Run full test suite (unit tests and property tests)
  - Verify all 26 correctness properties are tested
  - Check test coverage meets goals (80% line, 75% branch, 85% function)
  - Test end-to-end user flows manually
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Property tests validate universal correctness properties from the design document
- Unit tests validate specific examples and edge cases
- The implementation follows a bottom-up approach: data layer → business logic → voice integration → UI
- LiveKit integration requires API credentials (to be configured in environment variables)
- myscheme.gov.in API integration may require CORS proxy for browser-based access
- All voice processing happens through LiveKit; no audio is stored locally after processing
