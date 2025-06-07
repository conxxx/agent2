/**
 * An audio worklet processor that stores the PCM audio data sent from the main thread
 * to a buffer and plays it.
 */
class PCMPlayerProcessor extends AudioWorkletProcessor {
  constructor() {
    super();

    // Init buffer
    this.bufferSize = 24000 * 180;  // 24kHz x 180 seconds
    this.buffer = new Float32Array(this.bufferSize);
    this.writeIndex = 0;
    this.readIndex = 0;
    this.isPlaying = false; // Initialize isPlaying flag
    console.log("PCMPlayerProcessor: isPlaying initialized to false.");
    console.log("[STUTTER_DEBUG PCMPlayer]: Initialized. bufferSize:", this.bufferSize, "isPlaying:", this.isPlaying);

    // Handle incoming messages from main thread
    this.port.onmessage = (event) => {
      // Reset the buffer when 'endOfAudio' message received
      if (event.data.command === 'endOfAudio') {
        this.readIndex = this.writeIndex; // Clear the buffer
        console.log("PCMPlayerProcessor: endOfAudio received, clearing the buffer.");
        console.log("[STUTTER_DEBUG PCMPlayer]: 'endOfAudio' command received. Buffer cleared. readIdx:", this.readIndex, "writeIdx:", this.writeIndex);
        return;
      }

      // Assuming event.data is an ArrayBuffer containing Int16 PCM data
      const dataChunk = event.data; // event.data is expected to be an ArrayBuffer
      console.log(`[STUTTER_DEBUG PCMPlayer]: onmessage: Received data chunk. Type: ${typeof dataChunk}, instanceof ArrayBuffer: ${dataChunk instanceof ArrayBuffer}, byteLength: ${dataChunk ? dataChunk.byteLength : 'N/A'}`);
      if (!(dataChunk instanceof ArrayBuffer)) {
          console.error("[STUTTER_DEBUG PCMPlayer]: onmessage: Received data is NOT an ArrayBuffer. Discarding.");
          return;
      }
      const int16Samples = new Int16Array(dataChunk);
      console.log(`[STUTTER_DEBUG PCMPlayer]: onmessage: Converted to Int16Array, length: ${int16Samples.length}. Current isPlaying: ${this.isPlaying}`);

      // Add the audio data to the buffer
      this._enqueue(int16Samples);
    };
  }

  // Push incoming Int16 data into our ring buffer.
  _enqueue(int16Samples) {
    console.log(`[STUTTER_DEBUG PCMPlayer]: _enqueue called with ${int16Samples.length} samples. Current isPlaying: ${this.isPlaying}, writeIdx: ${this.writeIndex}, readIdx: ${this.readIndex}`);
    if (!this.isPlaying && int16Samples.length > 0) {
      this.isPlaying = true;
      console.log("PCMPlayerProcessor: Playback starting, isPlaying set to true.");
      console.log("[STUTTER_DEBUG PCMPlayer]: _enqueue: Playback starting, isPlaying set to true.");
    }
    for (let i = 0; i < int16Samples.length; i++) {
      // Convert 16-bit integer to float in [-1, 1]
      const floatVal = int16Samples[i] / 32768;

      // Store in ring buffer for left channel only (mono)
      this.buffer[this.writeIndex] = floatVal;
      this.writeIndex = (this.writeIndex + 1) % this.bufferSize;

      // Overflow handling (overwrite oldest samples)
      if (this.writeIndex === this.readIndex) {
        // console.log("[STUTTER_DEBUG PCMPlayer]: _enqueue: Buffer overflow. writeIdx and readIdx are both:", this.writeIndex);
        this.readIndex = (this.readIndex + 1) % this.bufferSize;
        // console.warn("PCMPlayerProcessor: Buffer overflow, overwriting oldest samples.");
      }
    }
    // console.log(`[STUTTER_DEBUG PCMPlayer]: _enqueue finished. New writeIdx: ${this.writeIndex}, readIdx: ${this.readIndex}`);
  }

  // The system calls `process()` ~128 samples at a time (depending on the browser).
  // We fill the output buffers from our ring buffer.
  process(inputs, outputs, parameters) {
    // Write a frame to the output
    const output = outputs[0]; // Assuming mono or taking the first channel group
    const framesPerBlock = output[0].length; // Number of samples in a frame for one channel
    // if (this.readIndex !== this.writeIndex) { // Log only if there's data to process or state changes
    //    console.log(`[STUTTER_DEBUG PCMPlayer]: process() called. framesPerBlock: ${framesPerBlock}, readIdx: ${this.readIndex}, writeIdx: ${this.writeIndex}, isPlaying: ${this.isPlaying}`);
    // }


    for (let frame = 0; frame < framesPerBlock; frame++) {
      if (this.readIndex !== this.writeIndex) {
        // Write the sample(s) into the output buffer
        const sample = this.buffer[this.readIndex];
        for (let channel = 0; channel < output.length; channel++) {
          output[channel][frame] = sample; // Write same sample to all output channels
        }
        this.readIndex = (this.readIndex + 1) % this.bufferSize;
      } else {
        // Buffer is empty
        if (this.isPlaying) {
          // If it was playing and buffer is now empty, playback has finished
          this.port.postMessage({ status: 'playback_finished' });
          console.log("PCMPlayerProcessor: Playback finished, posted 'playback_finished' message.");
          console.log(`[STUTTER_DEBUG PCMPlayer]: process(): Playback finished (buffer empty while isPlaying=true). readIdx: ${this.readIndex}, writeIdx: ${this.writeIndex}. Posting 'playback_finished'.`);
          this.isPlaying = false;
          console.log("PCMPlayerProcessor: isPlaying set to false.");
          console.log("[STUTTER_DEBUG PCMPlayer]: process(): isPlaying set to false.");
        }
        // Output silence
        for (let channel = 0; channel < output.length; channel++) {
          output[channel][frame] = 0;
        }
      }
    }

    // Returning true tells the system to keep the processor alive
    return true;
  }
}

registerProcessor('pcm-player-processor', PCMPlayerProcessor);
