/**
 * An audio worklet processor that forwards raw PCM data from the microphone.
 */
class PCMRecorderProcessor extends AudioWorkletProcessor {
  constructor() {
    super();
  }

  process(inputs, outputs, parameters) {
    // Check if there's input audio data
    if (inputs.length > 0 && inputs[0].length > 0 && inputs[0][0].length > 0) {
      // Use the first channel of the first input
      const inputChannel = inputs[0][0];
      
      // Create a copy of the Float32Array data to send to the main thread.
      // This is important because the underlying ArrayBuffer might be recycled.
      const inputCopy = new Float32Array(inputChannel);
      
      // Post the Float32Array data to the main thread.
      // The main thread will be responsible for converting it to 16-bit PCM
      // and then to Base64 before sending over WebSocket.
      this.port.postMessage(inputCopy);
    }
    // Keep the processor alive
    return true;
  }
}

registerProcessor('pcm-recorder-processor', PCMRecorderProcessor);
