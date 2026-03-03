/**
 * LiveKit Voice Service
 * Handles real-time voice communication with the LiveKit agent.
 * Pre-warms connection on page load so the mic button is near-instant.
 */

import {
  Room,
  RoomEvent,
  Track,
  ConnectionState,
  DisconnectReason,
  RoomOptions as LKRoomOptions,
  type RemoteTrack,
  type RemoteParticipant,
  type RemoteTrackPublication,
} from 'livekit-client';

// ── Types ────────────────────────────────────────────────────────────────────

export type VoiceStatus =
  | 'idle'
  | 'connecting'
  | 'connected'
  | 'agent-speaking'
  | 'disconnecting'
  | 'error';

export interface VoiceCallbacks {
  onStatusChange?: (status: VoiceStatus) => void;
  onAgentConnected?: () => void;
  onAgentDisconnected?: () => void;
  onError?: (message: string) => void;
}

interface TokenResponse {
  token: string;
  url: string;
  room: string;
  participant: string;
}

// ── Token fetching ───────────────────────────────────────────────────────────

async function fetchToken(roomName: string, retries = 2): Promise<TokenResponse> {
  const apiBase = '/api';
  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 10000);
      const res = await fetch(`${apiBase}/token?room=${encodeURIComponent(roomName)}`, {
        signal: controller.signal,
      });
      clearTimeout(timeout);
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.error || `Token fetch failed (${res.status})`);
      }
      return res.json();
    } catch (err) {
      if (attempt === retries) throw err;
      console.warn(`[Voice] Token fetch attempt ${attempt + 1} failed, retrying...`);
      await new Promise((r) => setTimeout(r, 1000 * (attempt + 1)));
    }
  }
  throw new Error('Token fetch failed after retries');
}

// ── LiveKit Voice Service ────────────────────────────────────────────────────

class LiveKitVoiceService {
  private room: Room | null = null;
  private audioElements: HTMLAudioElement[] = [];
  private callbacks: VoiceCallbacks = {};
  private _status: VoiceStatus = 'idle';

  /** Pre-warmed token + url cached from page load */
  private _warmToken: Promise<TokenResponse> | null = null;
  private _warmRoom: Room | null = null;

  get status(): VoiceStatus {
    return this._status;
  }

  private setStatus(s: VoiceStatus) {
    this._status = s;
    this.callbacks.onStatusChange?.(s);
  }

  /**
   * Pre-warm: fetch token + create Room object ahead of time.
   * Call this on page load so the mic button press is near-instant.
   */
  preWarm(roomName: string = 'gram-sahayak'): void {
    if (this._warmToken) return; // already warming

    console.log('[Voice] Pre-warming token + room...');
    this._warmToken = fetchToken(roomName).catch((err) => {
      console.warn('[Voice] Pre-warm token fetch failed:', err);
      this._warmToken = null;
      throw err;
    });

    // Pre-create the Room object (no network call, just JS init)
    this._warmRoom = new Room({
      adaptiveStream: true,
      dynacast: true,
      // Audio optimization: lower jitter buffer for reduced latency
      audioCaptureDefaults: {
        autoGainControl: true,
        echoCancellation: true,
        noiseSuppression: true,
      },
      audioOutput: {
        deviceId: 'default',
      },
    } as LKRoomOptions);
  }

  /**
   * Start a voice session — uses pre-warmed token/room if available.
   */
  async connect(
    roomName: string = 'gram-sahayak',
    callbacks: VoiceCallbacks = {},
  ): Promise<void> {
    if (this.room) {
      console.warn('Already in a voice session');
      return;
    }

    this.callbacks = callbacks;
    this.setStatus('connecting');

    try {
      // 1. Use pre-warmed token or fetch fresh
      let tokenData: TokenResponse;
      if (this._warmToken) {
        try {
          tokenData = await this._warmToken;
        } catch {
          tokenData = await fetchToken(roomName);
        }
        this._warmToken = null;
      } else {
        tokenData = await fetchToken(roomName);
      }

      // 2. Use pre-warmed Room or create new
      if (this._warmRoom) {
        this.room = this._warmRoom;
        this._warmRoom = null;
      } else {
        this.room = new Room({
          adaptiveStream: true,
          dynacast: true,
          audioCaptureDefaults: {
            autoGainControl: true,
            echoCancellation: true,
            noiseSuppression: true,
          },
        });
      }

      this.attachRoomListeners();

      // 3. Connect (fast — token is already available)
      await this.room.connect(tokenData.url, tokenData.token);
      console.log('[Voice] Connected to LiveKit room');

      // 4. Publish microphone
      await this.room.localParticipant.setMicrophoneEnabled(true);
      this.setStatus('connected');
    } catch (err: unknown) {
      console.error('[Voice] Connection failed:', err);
      const msg = err instanceof Error ? err.message : 'Connection failed';
      this.setStatus('error');
      this.callbacks.onError?.(msg);
      this.cleanup();
      throw err;
    }
  }

  /**
   * End the voice session.
   */
  async disconnect(): Promise<void> {
    if (!this.room) return;
    this.setStatus('disconnecting');

    try {
      await this.room.disconnect();
    } catch (err) {
      console.error('Error during disconnect:', err);
    }

    this.cleanup();
    this.setStatus('idle');

    // Pre-warm again for next session
    this.preWarm();
  }

  /**
   * Toggle mute on the local microphone.
   */
  async toggleMute(): Promise<boolean> {
    if (!this.room) return false;
    const current = this.room.localParticipant.isMicrophoneEnabled;
    await this.room.localParticipant.setMicrophoneEnabled(!current);
    return !current;
  }

  /**
   * Whether the user is currently in a session.
   */
  get isConnected(): boolean {
    return (
      this.room !== null &&
      this.room.state === ConnectionState.Connected
    );
  }

  // ── Private helpers ──────────────────────────────────────────────────

  private attachRoomListeners(): void {
    if (!this.room) return;
    const room = this.room;

    room.on(
      RoomEvent.TrackSubscribed,
      (track: RemoteTrack, _pub: RemoteTrackPublication, participant: RemoteParticipant) => {
        if (track.kind === Track.Kind.Audio) {
          const el = track.attach();
          el.setAttribute('data-participant', participant.identity);
          // Ensure audio plays even if browser blocks autoplay
          el.autoplay = true;
          (el as any).playsInline = true;
          document.body.appendChild(el);
          this.audioElements.push(el);

          // Force-play to work around browser autoplay policy
          el.play().catch(() => {
            console.warn('[Voice] Autoplay blocked, will retry on user gesture');
          });
        }

        // Any remote participant is treated as the agent
        this.callbacks.onAgentConnected?.();
      },
    );

    room.on(
      RoomEvent.TrackUnsubscribed,
      (track: RemoteTrack, _pub: RemoteTrackPublication, _participant: RemoteParticipant) => {
        const detached = track.detach();
        detached.forEach((el) => {
          el.remove();
          this.audioElements = this.audioElements.filter((a) => a !== el);
        });
      },
    );

    room.on(RoomEvent.ParticipantConnected, (_p: RemoteParticipant) => {
      this.callbacks.onAgentConnected?.();
      this.setStatus('connected');
    });

    room.on(RoomEvent.ParticipantDisconnected, (_p: RemoteParticipant) => {
      this.callbacks.onAgentDisconnected?.();
    });

    room.on(RoomEvent.ActiveSpeakersChanged, (speakers) => {
      if (!this.room) return;
      const agentSpeaking = speakers.some(
        (s) => s.identity !== this.room!.localParticipant.identity,
      );
      if (agentSpeaking) {
        this.setStatus('agent-speaking');
      } else if (this._status === 'agent-speaking') {
        this.setStatus('connected');
      }
    });

    room.on(RoomEvent.Disconnected, (_reason?: DisconnectReason) => {
      this.cleanup();
      this.setStatus('idle');
    });

    room.on(RoomEvent.ConnectionStateChanged, (state: ConnectionState) => {
      console.log('[Voice] Connection state:', state);
    });
  }

  private cleanup(): void {
    this.audioElements.forEach((el) => el.remove());
    this.audioElements = [];
    this.room = null;
  }
}

// ── Singleton ────────────────────────────────────────────────────────────────

let _instance: LiveKitVoiceService | null = null;

export function getVoiceService(): LiveKitVoiceService {
  if (!_instance) {
    _instance = new LiveKitVoiceService();
    // Auto pre-warm on first access (page load)
    _instance.preWarm();
  }
  return _instance;
}
