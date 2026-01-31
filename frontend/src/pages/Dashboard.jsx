import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { motion } from 'framer-motion';
import { MessageCircle, PenTool, Wind, BookOpen, AlertCircle, Heart, User, Settings, LogOut, Sun, Moon, Activity, Mic, X, Loader, Zap } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { sendMessageToGemini } from '../services/gemini';
import { startContinuousRecognition, speakText, playAudio } from '../services/voice';
import logo from '../assets/logo.png'; // Make sure this path is correct

// --- Components ---

const DashboardContainer = styled.div`
  min-height: 100vh;
  background: var(--bg-warm);
  padding-bottom: 4rem;
`;

const TopBar = styled.header`
  padding: 1.5rem 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: rgba(254, 252, 248, 0.9);
  backdrop-filter: blur(12px);
  position: sticky;
  top: 0;
  z-index: 50;
`;

const LogoArea = styled.div`
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-family: var(--font-heading);
  font-weight: 700;
  font-size: 1.5rem;
  color: #5D7B89;
  cursor: pointer;
  
  img {
    height: 40px;
  }
`;

const ProfileArea = styled.div`
  display: flex;
  align-items: center;
  gap: 1rem;
`;

const IconButton = styled.button`
  width: 40px;
  height: 40px;
  border-radius: 50%;
  border: 1px solid var(--ui-border);
  background: white;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);
  transition: all 0.2s;
  
  &:hover {
    background: var(--bg-sage);
    color: var(--text-primary);
  }
`;

const GreetingSection = styled.section`
  padding: 2rem;
  max-width: 1200px;
  margin: 0 auto;
  text-align: center;
`;

const Greeting = styled.h1`
  font-size: 2.5rem;
  color: #2D3E50;
  margin-bottom: 0.5rem;
  
  span {
    color: #8BAEB8;
  }
`;

const SubGreeting = styled.p`
  color: var(--text-secondary);
  font-size: 1.1rem;
`;

// Mood Tracker
const MoodSection = styled.div`
  margin-top: 3rem;
  margin-bottom: 4rem;
`;

const MoodLabel = styled.h3`
  font-size: 1.25rem;
  margin-bottom: 1.5rem;
  color: var(--text-primary);
`;

const MoodGrid = styled.div`
  display: flex;
  justify-content: center;
  gap: 1.5rem;
  flex-wrap: wrap;
`;

const MoodButton = styled(motion.button)`
  background: var(--bg-card);
  border: 1px solid var(--ui-border);
  padding: 1rem 1.5rem;
  border-radius: 20px;
  font-size: 2rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  box-shadow: 0 4px 10px rgba(0,0,0,0.02);
  min-width: 100px;
  
  span {
    font-size: 0.9rem;
    font-weight: 500;
    color: var(--text-secondary);
  }
  
  &:hover, &.selected {
    background: var(--bg-sage);
    border-color: #D1E8D5;
    transform: translateY(-5px);
    box-shadow: 0 8px 15px rgba(0,0,0,0.05);
  }
`;

// Features Grid
const GridContainer = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 2rem;
  max-width: 1000px;
  margin: 0 auto;
  padding: 0 2rem;
`;

const DashboardCard = styled(motion.div)`
  background: var(--bg-card);
  padding: 2rem;
  border-radius: 24px;
  border: 1px solid var(--ui-border);
  box-shadow: 0 4px 20px rgba(0,0,0,0.02);
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  cursor: pointer;
  height: 100%;
  
  &:hover {
    box-shadow: 0 10px 30px rgba(184, 216, 229, 0.15);
    border-color: #B8D8E5;
  }
`;

const CardIcon = styled.div`
  width: 56px;
  height: 56px;
  border-radius: 16px;
  background: ${props => props.color || 'var(--bg-sage)'};
  color: ${props => props.$textColor || 'var(--text-primary)'};
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 1.5rem;
`;

const CardTitle = styled.h3`
  font-size: 1.25rem;
  margin-bottom: 0.5rem;
  color: var(--text-primary);
`;

const CardDescription = styled.p`
  font-size: 0.9rem;
  color: var(--text-secondary);
  margin-bottom: 0;
  line-height: 1.5;
`;

// Insight Preview (Simple Mock)
const InsightBanner = styled(motion.div)`
  max-width: 1000px;
  margin: 3rem auto 0;
  padding: 0 2rem;
`;

const InsightContent = styled.div`
  background: linear-gradient(135deg, #E8E4F0 0%, #FFFFFF 100%);
  border: 1px solid #E2E8F0;
  border-radius: 24px;
  padding: 1.5rem 2.5rem;
  display: flex;
  align-items: center;
  gap: 2rem;
  box-shadow: 0 4px 15px rgba(0,0,0,0.03);
  
   @media (max-width: 768px) {
    flex-direction: column;
    text-align: center;
    padding: 1.5rem;
  }
`;

const VoiceFab = styled(motion.button)`
  position: fixed;
  bottom: 2rem;
  right: 2rem;
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: var(--accent-sky);
  color: #1F3846;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 10px 30px rgba(184, 216, 229, 0.4);
  cursor: pointer;
  z-index: 100;
  
  &:hover {
    transform: scale(1.1);
  }
`;

const VoiceOverlay = styled(motion.div)`
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(45, 62, 80, 0.95);
  backdrop-filter: blur(15px);
  z-index: 200;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: white;
  padding: 2rem;
`;

const PulseCircle = styled(motion.div)`
  width: 120px;
  height: 120px;
  border-radius: 50%;
  background: rgba(255,255,255,0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 2rem;
  position: relative;
  
  &::after {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    border-radius: 50%;
    border: 2px solid rgba(255,255,255,0.2);
    animation: ping 2s cubic-bezier(0, 0, 0.2, 1) infinite;
  }
  
  @keyframes ping {
    75%, 100% {
      transform: scale(2);
      opacity: 0;
    }
  }
`;

export default function Dashboard() {
  const navigate = useNavigate();
  const [selectedMood, setSelectedMood] = useState(() => {
    const saved = localStorage.getItem('mlh_daily_mood');
    if (saved) {
      const { date, mood } = JSON.parse(saved);
      const today = new Date().toISOString().split('T')[0];
      if (date === today) return mood;
    }
    return null;
  });

  const handleMoodSelect = (mood) => {
    setSelectedMood(mood);
    const today = new Date().toISOString().split('T')[0];
    localStorage.setItem('mlh_daily_mood', JSON.stringify({ date: today, mood }));

    // Also log to persistent journal if not already logged?
    // For now, just persisting visual state as requested.
  };
  const [greeting, setGreeting] = useState(() => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good Morning';
    if (hour < 18) return 'Good Afternoon';
    return 'Good Evening';
  });

  // --- Voice Mode State ---
  const [isVoiceMode, setIsVoiceMode] = useState(false);
  const [voiceStatus, setVoiceStatus] = useState('idle'); // idle, listening, processing, speaking
  const [transcript, setTranscript] = useState('');
  const stopRef = React.useRef(null); // Function to stop current recognition
  const loopRef = React.useRef(false); // Flag for loop active

  // Clean on unmount
  useEffect(() => {
    return () => {
      loopRef.current = false;
      if (stopRef.current) stopRef.current();
      window.speechSynthesis.cancel();
    };
  }, []);

  const handleVoiceSession = () => {
    setIsVoiceMode(true);
    setVoiceStatus('listening');
    setTranscript('Listening...');
    loopRef.current = true;
    startLoop();
  };

  const startLoop = () => {
    if (!loopRef.current) return;

    setVoiceStatus('listening');
    const recognition = startContinuousRecognition(
      (interim) => setTranscript(interim), // onInterim
      async (final) => { // onFinal
        // Stop recognition ref is useless now as it stopped itself
        if (!final.trim()) {
          // If silence/empty, restart loop? OR just wait? 
          // Logic: if users starts session they usually speak. 
          // If silence, maybe ask "Are you there?" or just listen again?
          // For now, listen again.
          if (loopRef.current) startLoop();
          return;
        }

        if (!loopRef.current) return;

        setVoiceStatus('processing');
        setTranscript('Thinking...');

        const response = await sendMessageToGemini([], final); // No history for now in dashboard context? Or simple history?

        if (!loopRef.current) return;

        setVoiceStatus('speaking');
        setTranscript(response);

        const audioBlob = await speakText(response);
        if (audioBlob) {
          const audio = playAudio(audioBlob);
          audio.onended = () => {
            // Loop back to listening
            if (loopRef.current) startLoop();
          };
        } else {
          // Fallback if no audio (browser TTS blocks until done in my helper? No, my helper promise resolves when done)
          // Check voice.js: wait, my voice.js promise resolves when ONEND fires.
          // So await speakText(response) works perfect for Browser TTS too.
          if (loopRef.current) startLoop();
        }
      },
      (error) => {
        console.error(error);
        // setTranscript("I didn't catch that. Tap to try again.");
        // setVoiceStatus('idle');
        // Retry on error if loop active? Be careful of infinite loops.
        if (loopRef.current) {
          setTimeout(() => startLoop(), 1000);
        }
      }
    );

    stopRef.current = () => recognition?.stop();
  };

  const endVoiceSession = () => {
    loopRef.current = false;
    setIsVoiceMode(false);
    setVoiceStatus('idle');
    if (stopRef.current) stopRef.current();
    window.speechSynthesis.cancel();
  };

  const moodOptions = [
    { emoji: '😊', label: 'Great' },
    { emoji: '😐', label: 'Okay' },
    { emoji: '😔', label: 'Low' },
    { emoji: '😰', label: 'Anxious' },
    { emoji: '😡', label: 'Upset' },
  ];

  const features = [
    {
      title: 'Talk it out',
      desc: 'Chat with your AI companion designed to listen and support you.',
      icon: <MessageCircle size={28} />,
      color: '#B8D8E5',
      textColor: '#1F3846',
      route: '/chat'
    },
    {
      title: 'Headspace',
      desc: 'Guided breathing and grounding exercises to calm your mind.',
      icon: <Wind size={28} />,
      color: '#D1E8D5',
      textColor: 'var(--text-primary)',
      route: '/breathe'
    },
    {
      title: 'Daily Journal',
      desc: 'Reflect on your day. Voice or text journaling available.',
      icon: <PenTool size={28} />,
      color: '#FFF0EB',
      textColor: '#C04D4D',
      route: '/journal'
    },
    {
      title: 'My Journey',
      desc: 'View your mood patterns and emotional insights over time.',
      icon: <Activity size={28} />,
      color: '#E8E4F0',
      textColor: '#475569',
      route: '/insights'
    },
    {
      title: 'Resources',
      desc: 'Helpful articles and verified crisis support contacts.',
      icon: <BookOpen size={28} />,
      color: '#F2F7F2',
      textColor: 'var(--text-primary)',
      route: '/resources'
    },
    {
      title: 'SOS',
      desc: 'Immediate help if you are feeling overwhelmed right now.',
      icon: <AlertCircle size={28} />,
      color: '#FFE4E4',
      textColor: '#D66D6D',
      route: '/emergency'
    },
  ];

  return (
    <DashboardContainer>
      <TopBar>
        <LogoArea onClick={() => navigate('/')}>
          <img src={logo} alt="Sanctuary" />
          Sanctuary
        </LogoArea>
        <ProfileArea>
          <IconButton onClick={() => navigate('/settings')}><Settings size={20} /></IconButton>
          <IconButton onClick={() => navigate('/profile')}><User size={20} /></IconButton>
        </ProfileArea>
      </TopBar>

      <GreetingSection>
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          <Greeting>{greeting}, <span>Friend</span></Greeting>
          <SubGreeting style={{ color: 'var(--text-secondary)' }}>Take a moment for yourself today.</SubGreeting>
        </motion.div>

        <MoodSection>
          <MoodLabel>How are you feeling right now?</MoodLabel>
          <MoodGrid>
            {moodOptions.map((m, i) => (
              <MoodButton
                key={i}
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.95 }}
                className={selectedMood === i ? 'selected' : ''}
                onClick={() => handleMoodSelect(i)}
              >
                {m.emoji}
                <span>{m.label}</span>
              </MoodButton>
            ))}
          </MoodGrid>
        </MoodSection>
      </GreetingSection>

      <GridContainer>
        {features.map((f, i) => (
          <DashboardCard
            key={i}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.1 }}
            onClick={() => navigate(f.route)}
          >
            <CardIcon color={f.color} $textColor={f.textColor}>{f.icon}</CardIcon>
            <CardTitle>{f.title}</CardTitle>
            <CardDescription>{f.desc}</CardDescription>
          </DashboardCard>
        ))}
      </GridContainer>

      <InsightBanner
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.8 }}
      >
        <InsightContent>
          <div>
            <Heart size={32} color="#D66D6D" fill="#D66D6D" style={{ opacity: 0.6 }} />
          </div>
          <div style={{ textAlign: 'left' }}>
            <h4 style={{ margin: '0 0 0.5rem', color: '#2D3E50' }}>Weekly Insight</h4>
            <p style={{ margin: 0, color: '#64748B', fontSize: '0.95rem' }}>
              You've logged "Great" mood 3 times this week. Morning check-ins seem to correlate with your positive days. Keep it up!
            </p>
          </div>
        </InsightContent>
      </InsightBanner>

      <VoiceFab
        whileTap={{ scale: 0.9 }}
        onClick={handleVoiceSession}
      >
        <Mic size={28} />
      </VoiceFab>

      {isVoiceMode && (
        <VoiceOverlay
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
        >
          <motion.div
            style={{ position: 'absolute', top: '2rem', right: '2rem', cursor: 'pointer' }}
            onClick={endVoiceSession}
            whileTap={{ scale: 0.9 }}
          >
            <X size={32} />
          </motion.div>

          <PulseCircle
            animate={voiceStatus === 'listening' ? { scale: [1, 1.2, 1], opacity: 1 } : { scale: 1 }}
            transition={{ repeat: Infinity, duration: 2 }}
          >
            {voiceStatus === 'processing' ? (
              <Loader size={48} className="animate-spin" /> // Assuming you have standard spin class or just animate it
            ) : voiceStatus === 'speaking' ? (
              <Zap size={48} fill="white" />
            ) : (
              <Mic size={48} />
            )}
          </PulseCircle>

          <h2 style={{ fontSize: '1.5rem', marginBottom: '1rem', fontWeight: 600 }}>
            {voiceStatus === 'listening' ? "Listening..." :
              voiceStatus === 'processing' ? "Thinking..." :
                voiceStatus === 'speaking' ? "Speaking..." : "Tap to Speak"}
          </h2>

          <p style={{ textAlign: 'center', maxWidth: '600px', opacity: 0.8, lineHeight: 1.6 }}>
            {transcript}
          </p>

          {voiceStatus === 'speaking' && (
            <div style={{ display: 'flex', gap: '4px', marginTop: '2rem', height: '20px', alignItems: 'center' }}>
              {[1, 2, 3, 4, 5].map(i => (
                <motion.div
                  key={i}
                  style={{ width: '6px', background: 'white', borderRadius: '4px' }}
                  animate={{ height: [10, 24, 10] }}
                  transition={{ repeat: Infinity, duration: 0.8, delay: i * 0.1 }}
                />
              ))}
            </div>
          )}
        </VoiceOverlay>
      )}
    </DashboardContainer>
  );
}
