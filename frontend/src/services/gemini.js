import { GoogleGenerativeAI } from "@google/generative-ai";

const API_KEY = import.meta.env.VITE_GEMINI_API_KEY;

let genAI = null;
let chatModel = null;
let voiceModel = null;

if (API_KEY) {
    genAI = new GoogleGenerativeAI(API_KEY);

    // Chat AI Agent - Model: Gemini 2.5 Flash
    chatModel = genAI.getGenerativeModel({
        model: "gemini-2.5-flash",
        generationConfig: {
            maxOutputTokens: 15000,
            temperature: 0.9,     // Increased for maximum emotional resonance and creativity
        }
    });

    // Voice AI Agent - Model: Gemini 2.5 Flash
    // Configured for Native Audio Dialog behavior (simulated via high-performance prompt/config)
    voiceModel = genAI.getGenerativeModel({
        model: "gemini-2.5-flash", // Using 2.5 Flash as requested for Voice Agent base
        generationConfig: {
            maxOutputTokens: 8000, // Optimized for conversational length
            temperature: 1.0,     // Higher temperature for more natural speech variation
        }
    });
}

const BASE_PROMPT = `
ROLE:
You are "Sanctuary," a voice-first, emotionally intelligent mental health support assistant. Your responses will be spoken aloud in real time.

CONTEXT:
The user is located in India. Always assume this locale.
- Use culturally relevant examples if needed.
- If providing emergency resources, suggest Indian helplines (e.g., 988 is not applicable; suggest 112, iCall, or Vandrevala Foundation).

SPEECH-REASONING RULES:
1. Prioritize how a human would naturally SAY something, not how it is typed.
2. Expand shorthand for natural speech (e.g., "fr" -> "for real", "idk" -> "I don't know").
3. Pronounce common abbreviations naturally (e.g., "lol" as "lawl", "lmao" as "luh-mao").
4. Avoid spelling out abbreviations letter-by-letter unless it sounds natural.
5. Treat shorthand variants like “lowk” as “lowkey” and speak them naturally.


SAFETY RULES:
1. You are not a medical professional. Do not diagnose or make clinical claims.
2. If distress escalates, shift to calm, grounding language and encourage real-world support.

CRISIS OVERRIDE:
If the user mentions self-harm, suicide, or immediate danger:
1. STOP all other persona logic.
2. Output ONLY the text: "[REDIRECT_SOS]" followed by a very brief, supportive sentence (e.g. "I'm connecting you to immediate help."). 
3. Do not ask follow-up questions. Focus on safety.
`;

const CALM_TONE_PROMPT = `
TONE: CALM MODE
- Use warm, empathetic, and reassuring language.
- Speak clearly and with a steady pace (simulated via tone).
- Avoid slang or modern shorthand.
`;

const GENZ_TONE_PROMPT = `
TONE: GEN-Z MODE
- Use a light, Gen-Z friendly conversational tone suitable for spoken language.
- Sound relatable and human, but remain serious and respectful.
- Never trivialize emotional distress.
- You may use light modern slang with natural speech expansion.
`;

const PROMOTION_PROTOCOL = `
[Suggestion: If the user feels lonely, briefly mention they can talk to you anytime via the Voice Mode dashboard.]
`;

const ORCHESTRATOR_SYSTEM_PROMPT = `
You are a supportive, non-clinical mental health reflection assistant focused on "Logical Empathy."

Your task is to analyze the user's wellness metrics (sleep, stress, mood, breathing), journal themes, and current chat context to offer ONE or TWO brief, gentle observations.

STRICT CONSTRAINTS:
1. **Context-Driven Reasoning**: You must reason out connections specifically relevant to the *current conversation*. Do not make non-relational leaps. If the user is talking about work stress, look for how sleep or breathing sessions specifically relate to that context.
2. **Avoid Generics**: Do not give "one-size-fits-all" advice. Your reflection must feel unique to the data provided.
3. **No Hardcoded Examples**: Base your response entirely on the localized data in the prompt.
4. **Soft Language**: Use "might," "could," "may be connected." Never state conclusions as facts.
5. **Directness**: Start directly with the observation. Avoid "Based on your data..." fillers.
6. **Maximum Length**: 60-100 words. Be deeply concise but meaningful.

Goal: Help the user notice the *logic* behind their patterns (e.g., "The high stress you're feeling in chat today might be linked to the 4 hours of sleep you've averaged recently.").
`;

export const generateReflection = async (summary) => {
    // Reflections are text-based analysis, using the Chat model
    if (!chatModel) {
        if (!API_KEY) return "Error: Missing VITE_GEMINI_API_KEY in .env file.";
        return "Error: Model not initialized.";
    }

    try {
        const userPrompt = `
Here is a summary of recent wellness signals.
Please reflect gently on possible connections without making conclusions.

${JSON.stringify(summary, null, 2)}

Respond in a calm, empathetic tone.
        `;

        const result = await chatModel.generateContent([
            ORCHESTRATOR_SYSTEM_PROMPT,
            userPrompt
        ]);

        const response = await result.response;
        return response.text();

    } catch (error) {
        console.error("Gemini Reflection Error:", error);
        return "I can’t be sure what’s causing this, but being gentle with yourself and noticing patterns can help.";
    }
};

export const sendMessageToGemini = async (history, newMessage, chatTone = 'calm', isVoice = false) => {
    // Select the appropriate model based on the interaction mode
    const currentModel = isVoice ? voiceModel : chatModel;

    if (!currentModel) {
        if (!API_KEY) return "Error: Missing VITE_GEMINI_API_KEY in .env file.";
        return "Error: Model not initialized.";
    }

    try {
        const trimmedHistory = history.slice(-6).map(msg => ({
            role: msg.sender === 'user' ? 'user' : 'model',
            parts: [{ text: msg.text }]
        }));

        const chat = currentModel.startChat({
            history: trimmedHistory,
        });

        // Assemble specialized prompt
        const isCrisisSuspected = newMessage.toLowerCase().includes('help') || newMessage.toLowerCase().includes('unsafe');

        // Safety Override: Use Calm Mode for any high-risk context
        const effectiveTone = isCrisisSuspected ? 'calm' : chatTone;
        const tonePrompt = effectiveTone === 'genz' ? GENZ_TONE_PROMPT : CALM_TONE_PROMPT;

        const systemInstruction = BASE_PROMPT + tonePrompt + PROMOTION_PROTOCOL;

        let promptToSend = newMessage;
        if (history.length === 0) {
            promptToSend = `${systemInstruction}\n\nUser: ${newMessage}`;
        } else {
            // Remind the model of its tone and speech-reasoning even mid-conversation
            promptToSend = `[System Reminder: Maintain ${effectiveTone} voice-first speech instructions. Avoid text-slang in output, expansion required.]\n\nUser: ${newMessage}`;
        }

        const result = await chat.sendMessage(promptToSend);
        const response = await result.response;
        return response.text();

    } catch (error) {
        console.error("Gemini API Error:", error);
        return "I'm having a little trouble connecting right now. But I'm still here with you. Can we try again?";
    }
};
