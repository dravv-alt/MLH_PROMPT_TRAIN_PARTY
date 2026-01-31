
const API_KEY = import.meta.env.VITE_GEMINI_API_KEY;
const HOST = 'generativelanguage.googleapis.com';
const URI = `wss://${HOST}/ws/google.ai.generativelanguage.v1alpha.GenerativeService.BidiGenerateContent`;

export class GeminiLiveService {
    constructor() {
        this.websocket = null;
        this.audioContext = null;
        this.mediaRecorder = null;
        this.processor = null;
        this.inputSource = null;
        this.pcmData = [];
        this.isPlaying = false;
        this.audioQueue = [];
        this.onAudioData = null; // Callback for visualizer
    }

    async connect(onMessage, onError) {
        if (!API_KEY) {
            onError(new Error("Missing API Key"));
            return;
        }

        this.websocket = new WebSocket(`${URI}?key=${API_KEY}`);

        this.websocket.onopen = () => {
            console.log("Gemini Live Connected");
            this.sendSetupMessage();
        };

        this.websocket.onmessage = async (event) => {
            if (event.data instanceof Blob) {
                // Handle Blob data if necessary
            } else {
                const data = JSON.parse(event.data);
                this.handleServerMessage(data, onMessage);
            }
        };

        this.websocket.onerror = (error) => {
            console.error("WebSocket Error:", error);
            onError(error);
        };

        this.websocket.onclose = () => {
            console.log("Gemini Live Disconnected");
        };

        await this.startAudioCapture();
    }

    sendSetupMessage() {
        const setupMessage = {
            setup: {
                model: "models/gemini-2.0-flash-exp",
                generation_config: {
                    response_modalities: ["AUDIO"],
                    speech_config: {
                        voice_config: {
                            prebuilt_voice_config: {
                                voice_name: "Aoede"
                            }
                        }
                    }
                },
                // Critical: Wait for user to finish talking (Server VAD)
                turn_detection: {
                    server_vad: {}
                }
            }
        };
        this.websocket.send(JSON.stringify(setupMessage));
    }

    async startAudioCapture() {
        this.audioContext = new (window.AudioContext || window.webkitAudioContext)({
            sampleRate: 16000,
        });

        const stream = await navigator.mediaDevices.getUserMedia({
            audio: {
                channelCount: 1,
                sampleRate: 16000,
            }
        });

        this.inputSource = this.audioContext.createMediaStreamSource(stream);

        // Use ScriptProcessor for raw PCM access 
        this.processor = this.audioContext.createScriptProcessor(512, 1, 1);

        this.processor.onaudioprocess = (e) => {
            const inputData = e.inputBuffer.getChannelData(0);

            // Convert Float32 to Int16 PCM
            const pcm16 = new Int16Array(inputData.length);
            for (let i = 0; i < inputData.length; i++) {
                let s = Math.max(-1, Math.min(1, inputData[i]));
                pcm16[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
            }

            // Upload chunks
            this.sendAudioChunk(this.arrayBufferToBase64(pcm16.buffer));

            // Visualizer callback
            if (this.onAudioData) this.onAudioData(inputData);
        };

        this.inputSource.connect(this.processor);
        this.processor.connect(this.audioContext.destination);
    }

    sendAudioChunk(base64Audio) {
        if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
            const message = {
                realtime_input: {
                    media_chunks: [{
                        mime_type: "audio/pcm",
                        data: base64Audio
                    }]
                }
            };
            this.websocket.send(JSON.stringify(message));
        }
    }

    handleServerMessage(data, onMessage) {
        if (data.serverContent?.modelTurn?.parts) {
            for (const part of data.serverContent.modelTurn.parts) {
                if (part.inlineData && part.inlineData.mimeType.startsWith('audio/')) {
                    const audioData = this.base64ToArrayBuffer(part.inlineData.data);
                    this.queueAudio(audioData);
                }
                if (part.text) {
                    if (onMessage) onMessage(part.text);
                }
            }
        }
    }

    queueAudio(audioBuffer) {
        this.audioQueue.push(audioBuffer);
        if (!this.isPlaying) {
            this.playNextChunk();
        }
    }

    async playNextChunk() {
        if (this.audioQueue.length === 0) {
            this.isPlaying = false;
            return;
        }

        this.isPlaying = true;
        const chunk = this.audioQueue.shift();

        const float32Data = new Float32Array(chunk.byteLength / 2);
        const dataView = new DataView(chunk);

        for (let i = 0; i < float32Data.length; i++) {
            const int16 = dataView.getInt16(i * 2, true);
            float32Data[i] = int16 / 32768.0;
        }

        const audioBuffer = this.audioContext.createBuffer(1, float32Data.length, 24000);
        audioBuffer.getChannelData(0).set(float32Data);

        const source = this.audioContext.createBufferSource();
        source.buffer = audioBuffer;
        source.connect(this.audioContext.destination);
        source.onended = () => {
            this.playNextChunk();
        };
        source.start();
    }

    disconnect() {
        if (this.websocket) {
            this.websocket.close();
        }
        if (this.audioContext) {
            this.audioContext.close();
        }
        if (this.inputSource) {
            this.inputSource.disconnect();
        }
        if (this.processor) {
            this.processor.disconnect();
        }

        this.isPlaying = false;
        this.audioQueue = [];
    }

    arrayBufferToBase64(buffer) {
        let binary = '';
        const bytes = new Uint8Array(buffer);
        const len = bytes.byteLength;
        for (let i = 0; i < len; i++) {
            binary += String.fromCharCode(bytes[i]);
        }
        return window.btoa(binary);
    }

    base64ToArrayBuffer(base64) {
        const binaryString = window.atob(base64);
        const len = binaryString.length;
        const bytes = new Uint8Array(len);
        for (let i = 0; i < len; i++) {
            bytes[i] = binaryString.charCodeAt(i);
        }
        return bytes.buffer;
    }
}

export const liveGemini = new GeminiLiveService();
