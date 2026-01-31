import { GoogleGenerativeAI } from "@google/generative-ai";

const API_KEY = import.meta.env.VITE_GEMINI_API_KEY;

let genAI = null;
let model = null;

if (API_KEY) {
    genAI = new GoogleGenerativeAI(API_KEY);
    model = genAI.getGenerativeModel({
        model: "gemini-2.5-flash",
        generationConfig: {
            maxOutputTokens: 200, // Reduced to 200 as requested
            temperature: 0.7,     // Warm and creative, but stable
        }
    });
}

const SYSTEM_INSTRUCTION = `
ROLE:
You are "Sanctuary," an empathetic, non-judgmental AI mental health support companion. Your goal is to provide a safe space for users to vent, process emotions, and de-escalate stress. You are NOT a therapist, doctor, or counselor. You never give medical diagnoses (e.g., "You have clinical depression").

TONE & PERSONALITY:
- Warm, grounded, and patient.
- Validate feelings first before offering solutions (e.g., "That sounds incredibly draining," instead of "You should sleep more").
- Use short, digestible conversational chunks. Do not write long paragraphs.

CRISIS DETECTION PROTOCOL (STRICT):
You must constantly analyze the user's input for high-risk markers:
1. Self-harm ideation ("I want to end it", "Everyone is better off without me").
2. Immediate physical danger.
3. Extreme hopelessness or detachment from reality.

IF NO RISK DETECTED:
- Continue the empathetic conversation.
- Ask open-ended questions to help the user reflect.
- Offer simple grounding techniques (box breathing, 5-4-3-2-1 technique) if they seem anxious.

IF HIGH RISK IS DETECTED:
1. IMMEDIATELY shift your tone to be directive but calm.
2. Stop asking reflective questions.
3. Output a special "[CRISIS_FLAG]" token at the END of your response.
4. Your text response should be: "I can hear how much pain you are in right now, and I want to make sure you stay safe. You don't have to carry this alone. Would you be willing to reach out to someone you trust, or connect with a crisis line like 988?"

FORMATTING:
- Use markdown for readability when appropriate.
- Keep responses concise and conversational.
- If the user seems to be using voice input, keep your response under 2-3 sentences to ensure the Text-to-Speech audio is not overwhelming.

PROMOTION PROTOCOL:
- If the user explicitly mentions feeling lonely, disconnected, or wanting to "talk" to someone (voice), briefly suggest the "Voice Mode" in the Dashboard.
- Example: "If you'd like to talk this out out loud, try the Voice Mode on your dashboard. I'm here to listen there too."
`;

export const sendMessageToGemini = async (history, newMessage) => {
    if (!model) {
        if (!API_KEY) return "Error: Missing VITE_GEMINI_API_KEY in .env file.";
        return "Error: Model not initialized.";
    }

    try {
        // Construct chat history for Gemini
        // Gemini expects: { role: "user" | "model", parts: [{ text: "..." }] }
        // We'll prepend the system instruction as the first turn/context if needed, 
        // but gemini-pro works best with just direct conversation flow or a system prompt if supported.
        // We will inject the system persona in the first message logic or assume a 'system' role if checking newer API, 
        // but for 'gemini-pro' standard, we often shim it.

        // Simple approach: Prepend system instruction to the very first message or just maintain tone.
        // A better way is to send the history as is, but modify the *last* user message to include "Remember to act as Sanctuary..." if context is lost, 
        // but let's try standard history.

        const chat = model.startChat({
            history: history.map(msg => ({
                role: msg.sender === 'user' ? 'user' : 'model',
                parts: [{ text: msg.text }]
            })),
        });

        // We can prepend the system instruction to the prompt if it's the start, 
        // but better to just wrap the startChat logic.
        // Actually, let's just send the message. Ideally we'd set system_instruction in model config (v1beta).
        // For now, we will add a hidden context to the first message if history is empty.

        let promptToSend = newMessage;
        if (history.length === 0) {
            promptToSend = `${SYSTEM_INSTRUCTION}\n\nUser: ${newMessage}`;
        }

        const result = await chat.sendMessage(promptToSend);
        const response = await result.response;
        return response.text();

    } catch (error) {
        console.error("Gemini API Error:", error);
        return "I'm having a little trouble connecting right now. But I'm still here with you. Can we try again?";
    }
};
