# Requirements Document: Gram Sahayak Prototype

## Introduction

Gram Sahayak is a voice-first, dialect-aware AI assistant prototype designed to help rural Indian citizens discover and apply for government welfare schemes through natural conversation. The prototype focuses on demonstrating core value proposition: enabling low-literacy users to access 700+ government schemes through voice interaction, eliminating middlemen dependency and reducing application complexity.

This prototype targets web browsers, integrates with LiveKit for voice capabilities, and fetches scheme data from myscheme.gov.in. The scope is intentionally limited to validate the concept and user experience before building the full system.

## Glossary

- **Gram_Sahayak**: The voice-first AI assistant system for rural welfare scheme access
- **Voice_Engine**: Component handling speech-to-text and text-to-speech processing via LiveKit
- **Scheme_Matcher**: AI component that matches user profiles to eligible government schemes
- **Eligibility_Engine**: Component that determines user qualification for specific schemes
- **Conversation_Manager**: Component orchestrating multi-turn voice dialogues
- **User_Profile**: Stored demographic and personal information about a citizen
- **Scheme_Repository**: Local database of government schemes fetched from myscheme.gov.in
- **Application_Form**: Structured data collected through conversation for scheme application
- **Session**: A single conversation interaction between user and system
- **Dialect**: Regional language variation (prototype supports Hindi as baseline)
- **Low_Literacy_User**: Target user with limited reading/writing ability who prefers voice interaction

## Requirements

### Requirement 1: Voice Interaction Foundation

**User Story:** As a low-literacy rural citizen, I want to interact with the system using my voice, so that I can access government schemes without needing to read or type.

#### Acceptance Criteria

1. WHEN a user clicks the microphone button, THE Voice_Engine SHALL capture audio input via LiveKit
2. WHEN audio is captured, THE Voice_Engine SHALL convert speech to text within 2 seconds
3. WHEN the system generates a response, THE Voice_Engine SHALL convert text to speech and play it to the user
4. WHILE the user is speaking, THE Voice_Engine SHALL display a visual indicator showing active listening
5. IF audio capture fails, THEN THE Gram_Sahayak SHALL display an error message and provide a retry option
6. THE Voice_Engine SHALL support Hindi language for the prototype phase

### Requirement 2: Government Scheme Data Access

**User Story:** As a system administrator, I want to fetch and store government scheme data from myscheme.gov.in, so that users can discover available welfare programs.

#### Acceptance Criteria

1. WHEN the system initializes, THE Scheme_Repository SHALL fetch scheme data from myscheme.gov.in API
2. THE Scheme_Repository SHALL store scheme information including name, description, eligibility criteria, benefits, and required documents
3. WHEN scheme data is older than 24 hours, THE Scheme_Repository SHALL refresh the data automatically
4. IF the API fetch fails, THEN THE Scheme_Repository SHALL use cached data and log the error
5. THE Scheme_Repository SHALL index schemes by category, state, and eligibility parameters for efficient searching

### Requirement 3: User Profile Collection

**User Story:** As a rural citizen, I want to provide my basic information through conversation, so that the system can identify schemes relevant to me.

#### Acceptance Criteria

1. WHEN a new user starts a session, THE Conversation_Manager SHALL ask for essential demographic information through voice prompts
2. THE User_Profile SHALL collect and store: age, gender, state, district, occupation, income category, and family size
3. WHEN the user provides information, THE Gram_Sahayak SHALL confirm understanding by repeating the information back
4. THE Conversation_Manager SHALL ask one question at a time to avoid overwhelming the user
5. IF the user provides unclear information, THEN THE Conversation_Manager SHALL ask clarifying questions
6. THE User_Profile SHALL persist data locally in browser storage for returning users

### Requirement 4: Scheme Discovery and Matching

**User Story:** As a rural citizen, I want to discover government schemes I'm eligible for, so that I can access benefits I didn't know existed.

#### Acceptance Criteria

1. WHEN a User_Profile is complete, THE Scheme_Matcher SHALL identify all schemes matching the user's eligibility criteria
2. THE Scheme_Matcher SHALL rank schemes by relevance based on user demographics and needs
3. WHEN presenting schemes, THE Conversation_Manager SHALL describe each scheme in simple language through voice
4. THE Gram_Sahayak SHALL present a maximum of 3 schemes at a time to avoid information overload
5. WHEN the user expresses interest in a scheme, THE Conversation_Manager SHALL provide detailed information about benefits and requirements
6. THE Scheme_Matcher SHALL explain why the user is eligible for each recommended scheme

### Requirement 5: Eligibility Verification

**User Story:** As a rural citizen, I want to know if I qualify for a specific scheme, so that I don't waste time on applications I'm not eligible for.

#### Acceptance Criteria

1. WHEN a user asks about a specific scheme, THE Eligibility_Engine SHALL evaluate all eligibility criteria against the User_Profile
2. THE Eligibility_Engine SHALL provide a clear yes/no eligibility determination
3. WHEN the user is not eligible, THE Eligibility_Engine SHALL explain which criteria are not met
4. WHEN the user is eligible, THE Conversation_Manager SHALL offer to guide them through the application process
5. THE Eligibility_Engine SHALL handle complex eligibility rules including age ranges, income thresholds, and categorical requirements

### Requirement 6: Conversational Application Guidance

**User Story:** As a rural citizen, I want to understand what documents and information I need for an application, so that I can prepare before visiting government offices.

#### Acceptance Criteria

1. WHEN a user selects a scheme to apply for, THE Conversation_Manager SHALL list all required documents through voice
2. THE Conversation_Manager SHALL explain each document requirement in simple terms
3. WHEN the user asks about a specific document, THE Conversation_Manager SHALL provide detailed guidance on how to obtain it
4. THE Gram_Sahayak SHALL allow users to mark documents as "have" or "need to get"
5. WHEN all document requirements are reviewed, THE Conversation_Manager SHALL summarize next steps for application submission

### Requirement 7: Simple and Accessible User Interface

**User Story:** As a low-literacy user, I want a clean interface with large buttons and visual feedback, so that I can navigate the system confidently.

#### Acceptance Criteria

1. THE Gram_Sahayak SHALL display a prominent microphone button as the primary interaction element
2. THE Gram_Sahayak SHALL use large, high-contrast visual elements suitable for users with limited digital literacy
3. WHILE processing voice input, THE Gram_Sahayak SHALL display the transcribed text on screen
4. THE Gram_Sahayak SHALL show the system's spoken response as text simultaneously with audio playback
5. THE Gram_Sahayak SHALL use icons and visual indicators to supplement voice feedback
6. THE Gram_Sahayak SHALL provide a simple navigation structure with no more than 2 levels of depth

### Requirement 8: Session Management and Conversation Flow

**User Story:** As a rural citizen, I want to have natural back-and-forth conversations with the system, so that I can ask questions and get clarifications easily.

#### Acceptance Criteria

1. THE Conversation_Manager SHALL maintain conversation context throughout a Session
2. WHEN a user asks a follow-up question, THE Conversation_Manager SHALL understand references to previous topics
3. THE Conversation_Manager SHALL support common conversational patterns including greetings, confirmations, and corrections
4. WHEN a user says they don't understand, THE Conversation_Manager SHALL rephrase the information in simpler terms
5. THE Conversation_Manager SHALL allow users to go back to previous topics or restart the conversation
6. WHEN a Session is inactive for 5 minutes, THE Gram_Sahayak SHALL save the state and allow resumption

### Requirement 9: Error Handling and Graceful Degradation

**User Story:** As a rural citizen with potentially unstable internet, I want the system to handle errors gracefully, so that I don't lose my progress or get confused.

#### Acceptance Criteria

1. IF the internet connection is lost, THEN THE Gram_Sahayak SHALL display a clear message and save the current state
2. WHEN connection is restored, THE Gram_Sahayak SHALL resume from the saved state
3. IF speech recognition fails to understand input, THEN THE Conversation_Manager SHALL ask the user to repeat in a friendly manner
4. THE Gram_Sahayak SHALL limit retry attempts to 3 before offering alternative input methods
5. IF LiveKit connection fails, THEN THE Gram_Sahayak SHALL display troubleshooting guidance
6. THE Gram_Sahayak SHALL log all errors for debugging while maintaining user privacy

### Requirement 10: Privacy and Data Security

**User Story:** As a rural citizen, I want my personal information to be kept secure, so that I can trust the system with my demographic data.

#### Acceptance Criteria

1. THE Gram_Sahayak SHALL store User_Profile data only in local browser storage for the prototype
2. THE Gram_Sahayak SHALL not transmit personal information to external servers except LiveKit for voice processing
3. WHEN a user wants to clear their data, THE Gram_Sahayak SHALL provide a clear option to delete all stored information
4. THE Gram_Sahayak SHALL display a privacy notice explaining what data is collected and how it's used
5. THE Gram_Sahayak SHALL not store audio recordings after processing is complete

## Prototype Scope Boundaries

The following capabilities are explicitly OUT OF SCOPE for the prototype phase but planned for future iterations:

- Multi-dialect support (only Hindi baseline in prototype)
- Actual application submission to government portals
- Application status tracking
- Integration with government authentication systems (Aadhaar, etc.)
- Offline functionality
- Mobile native applications
- Multi-language support beyond Hindi
- Advanced AI personalization and learning
- Integration with payment systems for fee submission

## Success Metrics for Prototype

- Users can complete profile setup through voice in under 3 minutes
- System successfully matches users to relevant schemes with 80%+ accuracy
- Voice interaction latency remains under 2 seconds for 90% of interactions
- Users can understand scheme eligibility without external help
- Zero critical errors during user testing sessions
