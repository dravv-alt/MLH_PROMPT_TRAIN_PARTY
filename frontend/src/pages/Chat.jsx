import React, { useState, useRef, useEffect } from 'react';
import styled from 'styled-components';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowLeft, Send, Mic, MoreVertical, Phone, ShieldAlert } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { sendMessageToGemini } from '../services/gemini';
import { startContinuousRecognition, speakText, playAudio } from '../services/voice';
import { useAuth } from '../context/AuthContext';

// --- Styled Components ---

const ChatContainer = styled.div`
  background: var(--bg-warm);
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  position: relative;
`;

const Header = styled.header`
  padding: 1rem 1.5rem;
  background: rgba(254, 252, 248, 0.95);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--ui-border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  position: sticky;
  top: 0;
  z-index: 50;
`;

const HeaderTitle = styled.div`
  text-align: center;
  h2 {
    font-size: 1.1rem;
    color: #2D3E50;
    margin: 0;
  }
  p {
    font-size: 0.8rem;
    color: #4Ade80; /* Active green dot color idea */
    margin: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 4px;
    
    &::before {
      content: '';
      width: 6px;
      height: 6px;
      background: #4Ade80;
      border-radius: 50%;
    }
  }
`;

const IconButton = styled.button`
  background: transparent;
  border: none;
  color: #64748B;
  padding: 8px;
  border-radius: 50%;
  cursor: pointer;
  transition: background 0.2s;
  
  &:hover {
    background: var(--bg-sage);
    color: #2D3E50;
  }
`;

const MessagesArea = styled.div`
  flex: 1;
  padding: 1.5rem;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  padding-bottom: 100px; /* Space for input */
`;

const MessageBubble = styled(motion.div)`
  max-width: 80%;
  padding: 1rem 1.25rem;
  border-radius: 20px;
  font-size: 1rem;
  line-height: 1.5;
  position: relative;
  word-wrap: break-word;
  
  ${props => props.sender === 'user' ? `
    align-self: flex-end;
    background: var(--accent-sky);
    color: #1F3846;
    border-bottom-right-radius: 4px;
    box-shadow: 0 2px 8px rgba(184, 216, 229, 0.4);
  ` : `
    align-self: flex-start;
    background: var(--bg-card);
    color: var(--text-primary);
    border: 1px solid var(--ui-border);
    border-bottom-left-radius: 4px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.02);
  `}
`;

const InputArea = styled.footer`
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 1rem 1.5rem;
  background: rgba(254, 252, 248, 0.95);
  backdrop-filter: blur(12px);
  border-top: 1px solid var(--ui-border);
  display: flex;
  gap: 1rem;
  align-items: flex-end;
`;

const InputBox = styled.textarea`
  flex: 1;
  background: var(--bg-input);
  border: 1px solid var(--ui-border);
  border-radius: 20px;
  padding: 0.8rem 1rem;
  font-family: inherit;
  font-size: 1rem;
  color: var(--text-primary);
  resize: none;
  max-height: 100px;
  outline: none;
  transition: border-color 0.2s;
  
  &:focus {
    border-color: #B8D8E5;
  }
`;

const SendButton = styled(motion.button)`
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: var(--accent-sky);
  color: #1F3846;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  
  &:disabled {
    background: #E2E8F0;
    color: #94A3B8;
  }
`;

const CrisisBanner = styled(motion.div)`
  background: #FEF2F2;
  border: 1px solid #FECACA;
  padding: 1rem;
  margin: 0 1.5rem 1rem;
  border-radius: 12px;
  display: flex;
  gap: 1rem;
  align-items: center;
  color: #991B1B;
  font-size: 0.9rem;
`;

export default function Chat() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState([
    { id: 1, text: `Hi ${user?.name || 'there'}. I'm here to listen. How are you feeling right now?`, sender: 'ai' }
  ]);
  const [loading, setLoading] = useState(false);
  const [showCrisis, setShowCrisis] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  // const [isSpeaking, setIsSpeaking] = useState(false); // Removed unused state
  const messagesEndRef = useRef(null);
  const voiceUsedRef = useRef(false);
  const recognitionRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async (textOverride = null) => {
    const textToSend = textOverride || input;
    if (!textToSend.trim()) return;

    const userMsg = { id: Date.now(), text: textToSend, sender: 'user' };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    // Call Gemini
    const responseText = await sendMessageToGemini(
      messages.filter(m => m.id !== 1),
      textToSend
    );

    // Crisis Check (Simple)
    if (responseText.includes('[CRISIS_FLAG]') || responseText.toLowerCase().includes('help line') || responseText.toLowerCase().includes('988')) {
      setShowCrisis(true);
    }

    // Clean flag from text
    const cleanText = responseText.replace('[CRISIS_FLAG]', '').trim();

    const aiMsg = { id: Date.now() + 1, text: cleanText, sender: 'ai' };
    setMessages(prev => [...prev, aiMsg]);
    setLoading(false);

    // Auto-speak AI response if voice was used
    if (voiceUsedRef.current) {
      await speakResponse(cleanText);
      voiceUsedRef.current = false;
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // Voice Recording (STT) using Web Speech API with continuous recognition
  const startRecording = () => {
    try {
      setIsRecording(true);

      const recognition = startContinuousRecognition(
        // onInterim: Update input in real-time as user speaks
        (interimText) => {
          setInput(interimText);
        },
        // onFinal: Called when recognition stops
        (finalText) => {
          if (finalText) {
            setInput(finalText);
            voiceUsedRef.current = false; // Disable voice response for Chat (Text output only)
            // Auto-send for STT convenience
            handleSend(finalText);
          }
          setIsRecording(false);
          recognitionRef.current = null;
        },
        // onError: Handle errors
        (error) => {
          console.error('Speech recognition error:', error);
          alert('Could not use speech recognition. Please check browser support and permissions.');
          setIsRecording(false);
          recognitionRef.current = null;
        }
      );

      recognitionRef.current = recognition;
    } catch (error) {
      console.error('Error starting speech recognition:', error);
      alert('Could not start speech recognition.');
      setIsRecording(false);
    }
  };



  const handleVoiceClick = () => {
    if (!isRecording) {
      startRecording();
    }
    // Note: Web Speech API stops automatically when user stops speaking
  };

  // Text-to-Speech
  const speakResponse = async (text) => {
    // setIsSpeaking(true);
    const audioBlob = await speakText(text);
    if (audioBlob) {
      const audio = playAudio(audioBlob);
      // audio.onended = () => setIsSpeaking(false);
    } else {
      // setIsSpeaking(false);
    }
  };

  return (
    <ChatContainer>
      <Header>
        <IconButton onClick={() => navigate('/dashboard')}>
          <ArrowLeft size={24} />
        </IconButton>
        <HeaderTitle>
          <h2>Sanctuary Companion</h2>
          <p>Online</p>
        </HeaderTitle>
        <IconButton>
          <MoreVertical size={24} />
        </IconButton>
      </Header>

      <MessagesArea>
        <AnimatePresence>
          {showCrisis && (
            <CrisisBanner
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
            >
              <ShieldAlert size={24} />
              <div>
                <strong>You are not alone.</strong> If you're in immediate danger, please call <strong>988</strong> (US) or your local emergency services.
              </div>
            </CrisisBanner>
          )}

          {messages.map((msg) => (
            <MessageBubble
              key={msg.id}
              sender={msg.sender}
              initial={{ opacity: 0, y: 10, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              transition={{ duration: 0.3 }}
            >
              {msg.text}
            </MessageBubble>
          ))}

          {loading && (
            <MessageBubble sender="ai" style={{ width: 'fit-content', minWidth: '60px' }}>
              <div style={{ display: 'flex', gap: '4px', padding: '4px 0' }}>
                <motion.div
                  style={{ width: '8px', height: '8px', background: '#94A3B8', borderRadius: '50%' }}
                  animate={{ y: [0, -5, 0] }}
                  transition={{ repeat: Infinity, duration: 0.6, ease: "easeInOut", delay: 0 }}
                />
                <motion.div
                  style={{ width: '8px', height: '8px', background: '#94A3B8', borderRadius: '50%' }}
                  animate={{ y: [0, -5, 0] }}
                  transition={{ repeat: Infinity, duration: 0.6, ease: "easeInOut", delay: 0.2 }}
                />
                <motion.div
                  style={{ width: '8px', height: '8px', background: '#94A3B8', borderRadius: '50%' }}
                  animate={{ y: [0, -5, 0] }}
                  transition={{ repeat: Infinity, duration: 0.6, ease: "easeInOut", delay: 0.4 }}
                />
              </div>
            </MessageBubble>
          )}
        </AnimatePresence>
        <div ref={messagesEndRef} />
      </MessagesArea>

      <InputArea>
        <IconButton
          style={{
            background: isRecording ? '#FCA5A5' : '#F1F5F9',
            animation: isRecording ? 'pulse 1.5s infinite' : 'none'
          }}
          onClick={handleVoiceClick}
        >
          <Mic size={20} color={isRecording ? '#991B1B' : '#64748B'} />
        </IconButton>
        <InputBox
          placeholder="Type your thoughts..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyPress}
        />
        <SendButton
          whileTap={{ scale: 0.9 }}
          onClick={handleSend}
          disabled={!input.trim() || loading}
        >
          <Send size={20} />
        </SendButton>
      </InputArea>
    </ChatContainer>
  );
}
