/**
 * LiveKit Voice Service
 * Handles voice communication with the LiveKit server
 * NOTE: This is a placeholder structure for future integration
 */

import { Room, RoomEvent, Track, RemoteTrack, RemoteParticipant } from 'livekit-client';

export interface LiveKitConfig {
  url: string;
  token: string;
}

export class LiveKitService {
  private room: Room | null = null;
  private isConnected = false;

  /**
   * Connect to LiveKit room
   * @param config LiveKit connection configuration
   */
  async connect(config: LiveKitConfig): Promise<void> {
    if (this.room) {
      console.warn('Already connected to a room');
      return;
    }

    try {
      this.room = new Room();

      // Setup event listeners
      this.setupEventListeners();

      // Connect to the room
      await this.room.connect(config.url, config.token);
      this.isConnected = true;

      console.log('✅ Connected to LiveKit room');
    } catch (error) {
      console.error('❌ Failed to connect to LiveKit:', error);
      this.room = null;
      throw error;
    }
  }

  /**
   * Disconnect from LiveKit room
   */
  async disconnect(): Promise<void> {
    if (!this.room) {
      return;
    }

    try {
      await this.room.disconnect();
      this.room = null;
      this.isConnected = false;
      console.log('Disconnected from LiveKit room');
    } catch (error) {
      console.error('Error disconnecting from LiveKit:', error);
    }
  }

  /**
   * Enable microphone for voice input
   */
  async enableMicrophone(): Promise<void> {
    if (!this.room) {
      throw new Error('Not connected to a room');
    }

    try {
      await this.room.localParticipant.setMicrophoneEnabled(true);
      console.log('Microphone enabled');
    } catch (error) {
      console.error('Failed to enable microphone:', error);
      throw error;
    }
  }

  /**
   * Disable microphone
   */
  async disableMicrophone(): Promise<void> {
    if (!this.room) {
      return;
    }

    try {
      await this.room.localParticipant.setMicrophoneEnabled(false);
      console.log('Microphone disabled');
    } catch (error) {
      console.error('Failed to disable microphone:', error);
    }
  }

  /**
   * Get connection status
   */
  getConnectionStatus(): boolean {
    return this.isConnected && this.room !== null;
  }

  /**
   * Setup event listeners for room events
   */
  private setupEventListeners(): void {
    if (!this.room) return;

    // Track subscribed event
    this.room.on(RoomEvent.TrackSubscribed, (
      track: RemoteTrack,
      _publication: any,
      _participant: RemoteParticipant
    ) => {
      console.log('Track subscribed:', track.kind);

      // If it's an audio track, attach it to play
      if (track.kind === Track.Kind.Audio) {
        const audioElement = track.attach();
        document.body.appendChild(audioElement);
      }
    });

    // Track unsubscribed event
    this.room.on(RoomEvent.TrackUnsubscribed, (
      track: RemoteTrack,
      _publication: any,
      _participant: RemoteParticipant
    ) => {
      console.log('Track unsubscribed:', track.kind);
      track.detach();
    });

    // Connection state changed
    this.room.on(RoomEvent.ConnectionStateChanged, (state) => {
      console.log('Connection state:', state);
    });

    // Disconnected event
    this.room.on(RoomEvent.Disconnected, () => {
      console.log('Disconnected from room');
      this.isConnected = false;
    });
  }
}

// Singleton instance
let livekitService: LiveKitService | null = null;

/**
 * Get or create LiveKit service instance
 */
export function getLivekitService(): LiveKitService {
  if (!livekitService) {
    livekitService = new LiveKitService();
  }
  return livekitService;
}
