/**
 * Audio Player Worklet Setup
 */
export async function startAudioPlayerWorklet() {
    // 1. Create an AudioContext
    const audioContext = new AudioContext({
        sampleRate: 24000 // Standard sample rate for ADK audio output
    });
    
    // 2. Load your custom processor code
    // Ensure pcm-player-processor.js is in the same directory or provide correct path
    const workletURL = new URL('./pcm-player-processor.js', import.meta.url);
    await audioContext.audioWorklet.addModule(workletURL);
    
    // 3. Create an AudioWorkletNode   
    const audioPlayerNode = new AudioWorkletNode(audioContext, 'pcm-player-processor');

    // 4. Connect to the destination
    audioPlayerNode.connect(audioContext.destination);

    // The audioPlayerNode.port is how we send messages (audio data) to the processor
    return [audioPlayerNode, audioContext];
}

/**
 * Audio Recorder Worklet Setup
 */
export async function startAudioRecorderWorklet(audioRecorderHandler) {
  // Create an AudioContext - let it use the system's default sample rate
  const audioRecorderContext = new AudioContext();
  console.log("AudioContext sample rate for recorder (native):", audioRecorderContext.sampleRate);

  // Load the AudioWorklet module
  // Ensure pcm-recorder-processor.js is in the same directory or provide correct path
  const workletURL = new URL("./pcm-recorder-processor.js", import.meta.url);
  await audioRecorderContext.audioWorklet.addModule(workletURL);

  // Request access to the microphone without sampleRate constraint
  let micStream;
  try {
    micStream = await navigator.mediaDevices.getUserMedia({
      audio: {
        channelCount: 1, // Mono audio
        // sampleRate: 16000 // Constraint removed
      },
    });
  } catch (err) {
    console.error("[audio-modules.js] Error calling getUserMedia:", err);
    throw err;
  }

  const audioTracks = micStream.getAudioTracks();
  if (audioTracks.length > 0) {
    const trackSettings = audioTracks[0].getSettings();
    console.log("[AGENT_WIDGET_DEBUG] Microphone audio track settings:", trackSettings);
    // The actual sampleRate of the track can be found in trackSettings.sampleRate
    console.log("[AGENT_WIDGET_DEBUG] Microphone track native sample rate:", trackSettings.sampleRate);
  }
  const source = audioRecorderContext.createMediaStreamSource(micStream);

  // Create an AudioWorkletNode that uses the PCMRecorderProcessor
  const audioRecorderNode = new AudioWorkletNode(
    audioRecorderContext,
    "pcm-recorder-processor"
  );

  // Connect the microphone source to the worklet.
  source.connect(audioRecorderNode);

  // Handle messages (PCM data) from the recorder worklet
  audioRecorderNode.port.onmessage = (event) => {
    // event.data is Float32Array from pcm-recorder-processor, at native sample rate
    const nativeRateSamples = event.data;
    const sourceSampleRate = audioRecorderContext.sampleRate;
    const targetSampleRate = 16000; // Target 16kHz for ADK Live API

    let samplesToProcess = nativeRateSamples;
    if (sourceSampleRate !== targetSampleRate) {
      // console.log(`Resampling from ${sourceSampleRate}Hz to ${targetSampleRate}Hz`);
      samplesToProcess = resampleBuffer(nativeRateSamples, sourceSampleRate, targetSampleRate);
    }
    
    const pcmDataBuffer = convertFloat32ToPCM(samplesToProcess);
    // Send the ArrayBuffer containing 16-bit PCM data (now at 16kHz) to the handler.
    audioRecorderHandler(pcmDataBuffer);
  };
  return [audioRecorderNode, audioRecorderContext, micStream];
}

/**
 * Resamples a Float32Array buffer from a source sample rate to a target sample rate.
 * This is a basic implementation (nearest neighbor or skipping/duplicating samples).
 * For high-quality resampling, a more sophisticated algorithm (e.g., using sinc interpolation)
 * would be needed, often via a library or more complex AudioWorklet.
 * @param {Float32Array} sourceBuffer The input audio data.
 * @param {number} sourceSampleRate The sample rate of the input audio.
 * @param {number} targetSampleRate The desired output sample rate.
 * @returns {Float32Array} The resampled audio data.
 */
function resampleBuffer(sourceBuffer, sourceSampleRate, targetSampleRate) {
  if (sourceSampleRate === targetSampleRate) {
    return sourceBuffer;
  }

  const ratio = sourceSampleRate / targetSampleRate;
  const outputLength = Math.round(sourceBuffer.length / ratio);
  const outputBuffer = new Float32Array(outputLength);

  for (let i = 0; i < outputLength; i++) {
    // Nearest neighbor (equivalent to picking every Nth sample for downsampling)
    const sourceIndex = Math.round(i * ratio);
    // Ensure sourceIndex is within bounds
    const clampedSourceIndex = Math.min(sourceIndex, sourceBuffer.length - 1);
    outputBuffer[i] = sourceBuffer[clampedSourceIndex];
  }
  // console.log(`Resampled buffer from ${sourceBuffer.length} to ${outputBuffer.length} samples.`);
  return outputBuffer;
}

/**
 * Stop the microphone stream.
 */
export function stopMicrophone(micStream) {
  if (micStream && micStream.getTracks) {
    micStream.getTracks().forEach((track) => track.stop());
    console.log("stopMicrophone(): Microphone stopped.");
  }
}

/**
 * Convert Float32 samples to 16-bit PCM.
 * @param {Float32Array} inputData - The Float32 audio data.
 * @returns {ArrayBuffer} - An ArrayBuffer containing 16-bit PCM data.
 */
function convertFloat32ToPCM(inputData) {
  const pcm16 = new Int16Array(inputData.length);
  for (let i = 0; i < inputData.length; i++) {
    pcm16[i] = Math.max(-32768, Math.min(32767, inputData[i] * 0x7FFF));
  }
  return pcm16.buffer;
}

/**
 * Pause microphone input by disabling audio tracks.
 * @param {MediaStream} micStream - The microphone stream.
 */
export function pauseMicrophoneInput(micStream) {
  if (micStream && micStream.getTracks) {
    micStream.getTracks().forEach((track) => {
      if (track.kind === 'audio') {
        track.enabled = false;
        console.log("[AudioModule] Microphone track disabled (paused). ID:", track.id, "Current enabled state:", track.enabled);
      }
    });
  } else {
    console.warn("[AudioModule] pauseMicrophoneInput: micStream not available or no tracks to pause.");
  }
}

/**
 * Resume microphone input by enabling audio tracks.
 * @param {MediaStream} micStream - The microphone stream.
 */
export function resumeMicrophoneInput(micStream) {
  if (micStream && micStream.getTracks) {
    micStream.getTracks().forEach((track) => {
      if (track.kind === 'audio') {
        track.enabled = true;
        console.log("[AudioModule] Microphone track enabled (resumed). ID:", track.id, "Current enabled state:", track.enabled);
      }
    });
  } else {
    console.warn("[AudioModule] resumeMicrophoneInput: micStream not available or no tracks to resume.");
  }
}
