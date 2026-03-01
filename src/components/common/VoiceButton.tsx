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
    <div className="flex flex-col items-center space-y-4">
      <button
        onClick={handleClick}
        className={`
          relative w-24 h-24 md:w-32 md:h-32 rounded-full
          transition-all duration-300 transform
          ${isListening
            ? 'bg-error scale-110 animate-pulse shadow-2xl'
            : 'bg-primary hover:bg-primary-dark hover:scale-105 shadow-xl'
          }
          focus:outline-none focus:ring-4 focus:ring-primary/50
          active:scale-95
        `}
        aria-label={isListening ? t('listening') : t('tapMicToSpeak')}
        aria-pressed={isListening}
      >
        <svg
          className="w-12 h-12 md:w-16 md:h-16 mx-auto text-white"
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

        {isListening && (
          <span className="absolute inset-0 rounded-full bg-error animate-ping opacity-20" />
        )}
      </button>

      <p className="text-center font-medium text-lg">
        {isListening ? t('listening') : t('tapMicToSpeak')}
      </p>
    </div>
  );
};

export default VoiceButton;
