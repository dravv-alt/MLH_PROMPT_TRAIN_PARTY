// Speech-to-Text using Browser's Web Speech API (Enhanced for full capture)
export const startContinuousRecognition = (onInterim, onFinal, onError) => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
        onError(new Error('Speech recognition not supported in this browser'));
        return null;
    }

    const recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-US';
    recognition.maxAlternatives = 1;

    let finalTranscript = '';
    let silenceTimer = null;

    recognition.onresult = (event) => {
        let interimTranscript = '';

        for (let i = event.resultIndex; i < event.results.length; i++) {
            const transcript = event.results[i][0].transcript;

            if (event.results[i].isFinal) {
                finalTranscript += transcript + ' ';
            } else {
                interimTranscript += transcript;
            }
        }

        // Show interim results in real-time
        onInterim(finalTranscript + interimTranscript);

        // Reset silence timer
        clearTimeout(silenceTimer);

        // Auto-stop after 2 seconds of silence
        silenceTimer = setTimeout(() => {
            recognition.stop();
        }, 2000);
    };

    recognition.onend = () => {
        clearTimeout(silenceTimer);
        onFinal(finalTranscript.trim());
    };

    recognition.onerror = (event) => {
        clearTimeout(silenceTimer);

        if (event.error === 'no-speech') {
            onFinal('');
        } else {
            onError(new Error(`Speech recognition error: ${event.error}`));
        }
    };

    recognition.start();

    return recognition; // Return so it can be stopped manually if needed
};

// Text-to-Speech using ElevenLabs
export const speakTextBackup = async (text) => {
    // ElevenLabs completely removed as requested.
    // Using standard Browser TTS.
    return triggerBrowserTTS(text);
};

// Fallback: Browser's built-in Text-to-Speech
const triggerBrowserTTS = (text) => {
    return new Promise((resolve) => {
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = 0.9;
        utterance.pitch = 1.0;
        utterance.volume = 1.0;

        // Try to find a female voice
        const voices = window.speechSynthesis.getVoices();
        const femaleVoice = voices.find(voice =>
            voice.name.includes('Female') ||
            voice.name.includes('Samantha') ||
            voice.name.includes('Victoria')
        );

        if (femaleVoice) {
            utterance.voice = femaleVoice;
        }

        utterance.onend = () => resolve(null);
        window.speechSynthesis.speak(utterance);
    });
};

// Play audio blob
export const playAudio = (audioBlob) => {
    if (!audioBlob) return null; // Browser TTS already played

    const audioUrl = URL.createObjectURL(audioBlob);
    const audio = new Audio(audioUrl);
    audio.play();

    // Clean up URL after playing
    audio.onended = () => {
        URL.revokeObjectURL(audioUrl);
    };

    return audio;
};
