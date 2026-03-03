import React, { useState, useCallback } from 'react';
import { useLanguage } from '../LanguageProvider';
import { getVoiceService, type VoiceStatus } from '../../services/livekitService';

interface VoiceButtonProps {
  onStartListening?: () => void;
  onStopListening?: () => void;
}

const STATUS_KEYS: Record<VoiceStatus, string> = {
  idle: 'tapMicToSpeak',
  connecting: 'processing',
  connected: 'listening',
  'agent-speaking': 'speaking',
  disconnecting: 'processing',
  error: 'tapMicToSpeak',
};

const VoiceButton: React.FC<VoiceButtonProps> = ({
  onStartListening,
  onStopListening,
}) => {
  const [status, setStatus] = useState<VoiceStatus>('idle');
  const { t } = useLanguage();

  const isActive = ['connecting', 'connected', 'agent-speaking'].includes(status);

  const handleClick = useCallback(async () => {
    const voice = getVoiceService();

    if (isActive) {
      // Disconnect
      await voice.disconnect();
      setStatus('idle');
      onStopListening?.();
      return;
    }

    // Connect
    try {
      await voice.connect({
        onStatusChange: (s) => setStatus(s),
        onAgentConnected: () => console.log('Agent joined the room'),
        onAgentDisconnected: () => console.log('Agent left the room'),
        onError: (msg) => console.error('Voice error:', msg),
      });
      onStartListening?.();
    } catch {
      // error status is already set by the service
    }
  }, [isActive, onStartListening, onStopListening]);

  const label = t(STATUS_KEYS[status] ?? 'tapMicToSpeak');

  return (
    <div className="flex flex-col items-center gap-6">
      {/* Outer glow ring */}
      <div className="relative">
        {isActive && (
          <>
            <span className="absolute inset-[-16px] rounded-full bg-primary/8 animate-ping" />
            <span className="absolute inset-[-8px] rounded-full bg-primary/15 animate-pulse" />
          </>
        )}

        <button
          onClick={handleClick}
          disabled={status === 'disconnecting'}
          className={`
            relative z-10 w-32 h-32 md:w-40 md:h-40 rounded-full
            transition-all duration-500 transform
            focus:outline-none focus:ring-4 focus:ring-primary/40
            active:scale-95 overflow-hidden
            ${status === 'connecting' || status === 'disconnecting'
              ? 'bg-gradient-to-br from-amber-400 to-amber-600 cursor-wait'
              : isActive
                ? 'bg-gradient-to-br from-red-500 to-rose-600 scale-110 shadow-[0_0_60px_rgba(239,68,68,0.4)]'
                : status === 'error'
                  ? 'bg-gradient-to-br from-red-400 to-red-600 hover:scale-105'
                  : 'bg-gradient-to-br from-primary via-primary-dark to-secondary hover:scale-105 shadow-large hover:shadow-glow'
            }
          `}
          aria-label={isActive ? t('listening') : t('tapMicToSpeak')}
          aria-pressed={isActive}
        >
          {/* Shimmer overlay */}
          <div className="absolute inset-0 bg-gradient-to-tr from-white/20 to-transparent" />

          {/* Icon */}
          {status === 'connecting' || status === 'disconnecting' ? (
            <svg className="w-14 h-14 md:w-18 md:h-18 mx-auto text-white animate-spin relative z-10" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
          ) : isActive ? (
            <svg className="w-16 h-16 md:w-20 md:h-20 mx-auto text-white relative z-10" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <rect x="6" y="6" width="12" height="12" rx="2" strokeWidth={2} fill="currentColor" />
            </svg>
          ) : (
            <svg className="w-16 h-16 md:w-20 md:h-20 mx-auto text-white relative z-10" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"
              />
            </svg>
          )}

          {/* Equalizer bars when agent speaks */}
          {status === 'agent-speaking' && (
            <div className="absolute bottom-4 left-1/2 -translate-x-1/2 flex gap-1 z-10">
              {[0, 1, 2, 3, 4].map((i) => (
                <span
                  key={i}
                  className="w-1 bg-white/80 rounded-full animate-bounce"
                  style={{
                    height: `${12 + Math.random() * 12}px`,
                    animationDelay: `${i * 0.1}s`,
                    animationDuration: '0.6s',
                  }}
                />
              ))}
            </div>
          )}
        </button>
      </div>

      {/* Status label */}
      <div className="text-center min-h-[3rem]">
        <p className={`font-bold text-lg md:text-xl transition-colors duration-300 ${
          isActive ? 'text-red-400' : status === 'error' ? 'text-red-400' : 'text-primary-light'
        }`}>
          {isActive ? t('listening') : status === 'error' ? 'Error' : t('tapMicToSpeak')}
        </p>
        <p className="text-text-tertiary text-sm mt-1 max-w-xs mx-auto">{label}</p>
      </div>
    </div>
  );
};

export default VoiceButton;
