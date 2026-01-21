class PCMProcessor extends AudioWorkletProcessor {
    constructor(options) {
        super();
        const sourceRate = options.processorOptions.sampleRate || 16000;
        const targetRate = 16000;

        this.ratio = sourceRate / targetRate;
        this.bufferSize = 4096;
        this.buffer = new Int16Array(this.bufferSize);
        this.bufferIndex = 0;
        this.phase = 0;
    }

    process(inputs, outputs, parameters) {
        const input = inputs[0];
        if (!input || !input.length) return true;

        const channelData = input[0]; // Mono
        const inputLength = channelData.length;

        // Downsample and process
        let outputSample;

        while (this.phase < inputLength) {
            const index = Math.floor(this.phase);

            // Simple Nearest Neighbor (robust and fast)
            // Ideally we'd low-pass filter before decimating to avoid aliasing,
            // but for speech recognition this is usually acceptable.
            let sample = channelData[index];

            // Clamp and convert to Int16
            const s = Math.max(-1, Math.min(1, sample));
            outputSample = s < 0 ? s * 0x8000 : s * 0x7FFF;

            this.buffer[this.bufferIndex++] = outputSample;

            if (this.bufferIndex >= this.bufferSize) {
                this.flush();
            }

            this.phase += this.ratio;
        }

        // Adjust phase for next chunk
        this.phase -= inputLength;

        return true;
    }

    flush() {
        // Send data to main thread as raw buffer
        // We must copy the buffer because the underlying ArrayBuffer is detached/transfered
        const outputData = this.buffer.slice(0, this.bufferIndex);

        this.port.postMessage(outputData.buffer, [outputData.buffer]);

        this.bufferIndex = 0;
    }
}

registerProcessor('pcm-processor', PCMProcessor);
