/**
 * An audio worklet processor that stores the PCM audio data sent from the main thread
 * to a buffer and plays it.
 */
class PCMPlayerProcessor extends AudioWorkletProcessor {
  constructor() {
    super();
    console.log("[PCMPlayerDebug] Constructor called.");
    this.bufferSize = 24000 * 180;  // 24kHz x 180 seconds
    this.buffer = new Float32Array(this.bufferSize);
    this.writeIndex = 0;
    this.readIndex = 0;
    this.isPlaying = false;
    console.log("[PCMPlayerDebug] Constructor: isPlaying initialized to false.");

    this.port.onmessage = (event) => {
      if (event.data.command === 'endOfAudio') {
        this.readIndex = this.writeIndex;
        console.log("[PCMPlayerDebug] onmessage: endOfAudio command received, clearing buffer.");
        return;
      }
      // Assuming event.data is ArrayBuffer for audio
      if (!(event.data instanceof ArrayBuffer)) {
        console.warn("[PCMPlayerDebug] onmessage: Received data is not an ArrayBuffer. Ignoring.", event.data);
        return;
      }
      const int16Samples = new Int16Array(event.data);
      this._enqueue(int16Samples);
    };
  }

  _enqueue(int16Samples) {
    if (!this.isPlaying && int16Samples.length > 0) {
      this.isPlaying = true;
      console.log("[PCMPlayerDebug] _enqueue: Playback starting, isPlaying SET to true.");
    }
    for (let i = 0; i < int16Samples.length; i++) {
      const floatVal = int16Samples[i] / 32768;
      this.buffer[this.writeIndex] = floatVal;
      this.writeIndex = (this.writeIndex + 1) % this.bufferSize;
      if (this.writeIndex === this.readIndex) {
        this.readIndex = (this.readIndex + 1) % this.bufferSize;
      }
    }
  }

  process(inputs, outputs, parameters) {
    const output = outputs[0];
    const framesPerBlock = output[0].length;

    for (let frame = 0; frame < framesPerBlock; frame++) {
      if (this.readIndex !== this.writeIndex) {
        const sample = this.buffer[this.readIndex];
        for (let channel = 0; channel < output.length; channel++) {
          output[channel][frame] = sample;
        }
        this.readIndex = (this.readIndex + 1) % this.bufferSize;
      } else {
        if (this.isPlaying) {
          console.log(`[PCMPlayerDebug] process: Buffer empty (readIndex: ${this.readIndex}, writeIndex: ${this.writeIndex}) and was playing. POSTING 'playback_finished'.`);
          this.port.postMessage({ status: 'playback_finished' });
          this.isPlaying = false;
          console.log("[PCMPlayerDebug] process: isPlaying SET to false after posting 'playback_finished'.");
        }
        for (let channel = 0; channel < output.length; channel++) {
          output[channel][frame] = 0;
        }
      }
    }
    return true;
  }
}
registerProcessor('pcm-player-processor', PCMPlayerProcessor);
