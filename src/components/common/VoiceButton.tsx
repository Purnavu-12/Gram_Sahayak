import React, { useState } from 'react';
import { useLanguage } from '../LanguageProvider';

interface VoiceButtonProps {
  onStartListening?: () => void;
  onStopListening?: () => void;
}

const VoiceButton: React.FC<VoiceButtonProps> = ({
  onStartListening,
  onStopListening
}) => {
  const [isListening, setIsListening] = useState(false);
  const { t } = useLanguage();

  const handleClick = async () => {
    if (isListening) {
      setIsListening(false);
      onStopListening?.();
    } else {
      // Request microphone permission
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        stream.getTracks().forEach(track => track.stop());

        setIsListening(true);
        onStartListening?.();

        // TODO: Integrate with LiveKit service
        // const livekitService = getLivekitService();
        // await livekitService.connect({ url: LIVEKIT_URL, token: LIVEKIT_TOKEN });
        // await livekitService.enableMicrophone();
      } catch (error) {
        console.error('Microphone permission denied:', error);
        alert(t('errors.micPermission'));
      }
    }
  };

  return (
    <div className="flex flex-col items-center space-y-6">
      <button
        onClick={handleClick}
        className={`
          relative w-32 h-32 md:w-40 md:h-40 rounded-full
          transition-all duration-500 transform
          ${isListening
            ? 'bg-gradient-to-br from-error to-red-600 scale-110 shadow-glow-lg'
            : 'bg-gradient-to-br from-primary via-primary-dark to-secondary hover:scale-105 shadow-large hover:shadow-glow'
          }
          focus:outline-none focus:ring-4 focus:ring-primary/50
          active:scale-95 overflow-hidden
        `}
        aria-label={isListening ? t('listening') : t('tapMicToSpeak')}
        aria-pressed={isListening}
      >
        {/* Animated gradient overlay */}
        <div className={`absolute inset-0 bg-gradient-to-tr from-white/20 to-transparent ${isListening ? 'animate-pulse' : ''}`}></div>

        {/* Microphone icon */}
        <svg
          className="w-16 h-16 md:w-20 md:h-20 mx-auto text-white relative z-10"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"
          />
        </svg>

        {/* Pulse rings for listening state */}
        {isListening && (
          <>
            <span className="absolute inset-0 rounded-full bg-error animate-ping opacity-20" />
            <span className="absolute inset-0 rounded-full bg-error animate-pulse opacity-30" />
          </>
        )}

        {/* Floating particles effect */}
        {!isListening && (
          <div className="absolute inset-0 overflow-hidden rounded-full">
            <div className="absolute w-2 h-2 bg-white/40 rounded-full top-1/4 left-1/4 animate-float"></div>
            <div className="absolute w-1.5 h-1.5 bg-white/30 rounded-full top-1/2 right-1/4 animate-float" style={{ animationDelay: '1s' }}></div>
            <div className="absolute w-2.5 h-2.5 bg-white/20 rounded-full bottom-1/4 left-1/3 animate-float" style={{ animationDelay: '2s' }}></div>
          </div>
        )}
      </button>

      <div className="text-center">
        <p className={`font-bold text-xl md:text-2xl transition-all duration-300 ${
          isListening ? 'text-error animate-pulse' : 'text-primary'
        }`}>
          {isListening ? t('listening') : t('tapMicToSpeak')}
        </p>
        {!isListening && (
          <p className="text-text-secondary text-sm mt-2 max-w-xs">
            Tap the microphone to start your voice conversation
          </p>
        )}
      </div>
    </div>
  );
};

export default VoiceButton;
