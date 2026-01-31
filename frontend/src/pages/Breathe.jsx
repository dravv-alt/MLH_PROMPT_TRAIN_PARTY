import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowLeft, Play, Pause, RotateCcw, Check, X } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

// ... (existing styled components)

const PageContainer = styled.div`
  min-height: 100vh;
  background: linear-gradient(135deg, #D1E8D5 0%, #B8D8E5 100%);
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 2rem;
  position: relative;
  overflow: hidden;
`;

const FloatingOrb = styled(motion.div)`
  position: absolute;
  width: 300px;
  height: 300px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(255,255,255,0.3) 0%, rgba(255,255,255,0) 70%);
  filter: blur(60px);
  pointer-events: none;
`;

const Header = styled.div`
  width: 100%;
  max-width: 600px;
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 2rem;
  z-index: 10;
  
  button {
    background: rgba(255, 255, 255, 0.9);
    border: 1px solid rgba(184, 216, 229, 0.3);
    padding: 0.5rem;
    border-radius: 50%;
    cursor: pointer;
    color: #2D3E50;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.2s;
    
    &:hover {
      transform: scale(1.05);
      background: white;
    }
  }
`;

const ContentCard = styled(motion.div)`
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 40px;
  padding: 3rem;
  max-width: 600px;
  width: 100%;
  box-shadow: 0 20px 60px rgba(0,0,0,0.08);
  border: 1px solid rgba(255, 255, 255, 0.6);
  z-index: 10;
  text-align: center;
`;

const Title = styled.h1`
  font-size: 2.5rem;
  color: #2D3E50;
  margin-bottom: 1rem;
`;

const Subtitle = styled.p`
  color: #64748B;
  font-size: 1.1rem;
  margin-bottom: 3rem;
`;

const BreathingCircle = styled(motion.div)`
  width: 250px;
  height: 250px;
  margin: 0 auto 3rem;
  border-radius: 50%;
  background: linear-gradient(135deg, #B8D8E5 0%, #D1E8D5 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 10px 40px rgba(184, 216, 229, 0.4);
  position: relative;
  
  &::before {
    content: '';
    position: absolute;
    width: 100%;
    height: 100%;
    border-radius: 50%;
    border: 2px solid rgba(184, 216, 229, 0.5);
    animation: pulse 4s ease-in-out infinite;
  }
  
  @keyframes pulse {
    0%, 100% { transform: scale(1); opacity: 0.5; }
    50% { transform: scale(1.1); opacity: 0.8; }
  }
`;

const InstructionText = styled(motion.p)`
  font-size: 1.8rem;
  font-weight: 600;
  color: #2D3E50;
  margin: 0;
`;

const CounterText = styled(motion.span)`
  font-size: 3rem;
  font-weight: 700;
  color: #5D7B89;
`;

const ControlsRow = styled.div`
  display: flex;
  gap: 1rem;
  justify-content: center;
  margin-top: 2rem;
`;

const ControlButton = styled(motion.button)`
  background: ${props => props.primary ? 'var(--accent-sky)' : 'white'};
  color: ${props => props.primary ? '#1F3846' : '#64748B'};
  border: 1px solid ${props => props.primary ? 'transparent' : '#E2E8F0'};
  padding: 1rem 2rem;
  border-radius: 50px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  transition: all 0.2s;
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  }
  
  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
`;

const TechniqueSelector = styled.div`
  display: flex;
  gap: 1rem;
  justify-content: center;
  margin-bottom: 2rem;
`;

const TechniqueButton = styled.button`
  background: ${props => props.$active ? 'var(--accent-sky)' : 'white'};
  color: ${props => props.$active ? '#1F3846' : '#64748B'};
  border: 1px solid ${props => props.$active ? 'transparent' : '#E2E8F0'};
  padding: 0.75rem 1.5rem;
  border-radius: 20px;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  
  &:hover {
    background: ${props => props.$active ? 'var(--accent-sky)' : '#F8FAFC'};
  }
`;

const FeedbackModal = styled(motion.div)`
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  z-index: 20;
  border-radius: 40px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem;
`;

const FeedbackTitle = styled.h2`
  color: #2D3E50;
  margin-bottom: 2rem;
`;

const MoodGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1rem;
  margin-bottom: 2rem;
`;

const FeedbackMoodBtn = styled.button`
  background: ${props => props.$selected ? 'var(--bg-sage)' : 'white'};
  border: 1px solid ${props => props.$selected ? '#CBD5E1' : '#E2E8F0'};
  padding: 1rem;
  border-radius: 16px;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  
  &:hover {
    background: #F1F5F9;
  }

  span:first-child { font-size: 2rem; }
  span:last-child { font-size: 0.9rem; color: #64748B; font-weight: 500; }
`;

export default function Breathe() {
    const navigate = useNavigate();

    // Breathing technique configurations
    const techniques = {
        box: { name: 'Box Breathing', inhale: 4, hold1: 4, exhale: 4, hold2: 4 },
        '478': { name: '4-7-8 Technique', inhale: 4, hold1: 7, exhale: 8, hold2: 0 },
        calm: { name: 'Calm Breathing', inhale: 4, hold1: 0, exhale: 6, hold2: 0 }
    };

    const [selectedTechnique, setSelectedTechnique] = useState('box');
    const [isActive, setIsActive] = useState(false);
    const [phase, setPhase] = useState('inhale'); // inhale, hold1, exhale, hold2
    const [counter, setCounter] = useState(techniques.box.inhale);
    const [cycleCount, setCycleCount] = useState(0);

    // Feedback State
    const [showFeedback, setShowFeedback] = useState(false);
    const [selectedMood, setSelectedMood] = useState(null);

    const currentTechnique = techniques[selectedTechnique];

    useEffect(() => {
        if (!isActive) return;

        const interval = setInterval(() => {
            setCounter(prev => {
                if (prev > 1) return prev - 1;

                // Move to next phase
                if (phase === 'inhale') {
                    if (currentTechnique.hold1 > 0) {
                        setPhase('hold1');
                        return currentTechnique.hold1;
                    } else {
                        setPhase('exhale');
                        return currentTechnique.exhale;
                    }
                } else if (phase === 'hold1') {
                    setPhase('exhale');
                    return currentTechnique.exhale;
                } else if (phase === 'exhale') {
                    if (currentTechnique.hold2 > 0) {
                        setPhase('hold2');
                        return currentTechnique.hold2;
                    } else {
                        setPhase('inhale');
                        setCycleCount(c => c + 1);
                        return currentTechnique.inhale;
                    }
                } else if (phase === 'hold2') {
                    setPhase('inhale');
                    setCycleCount(c => c + 1);
                    return currentTechnique.inhale;
                }

                return prev;
            });
        }, 1000);

        return () => clearInterval(interval);
    }, [isActive, phase, currentTechnique]);

    const handleStart = () => {
        if (cycleCount === 0) setCycleCount(1);
        setIsActive(true);
    };

    const handlePause = () => {
        setIsActive(false);
    };

    const handleReset = () => {
        setIsActive(false);
        setPhase('inhale');
        setCounter(currentTechnique.inhale);
        setCycleCount(0);
        setShowFeedback(false);
    };

    const handleTechniqueChange = (technique) => {
        setSelectedTechnique(technique);
        setIsActive(false);
        setPhase('inhale');
        setCounter(techniques[technique].inhale);
        setCycleCount(0);
    };

    const handleFinish = () => {
        setIsActive(false);
        setShowFeedback(true);
    };

    const saveSession = () => {
        if (!selectedMood) return;

        const sessionData = {
            id: Date.now(),
            date: new Date().toISOString(),
            technique: techniques[selectedTechnique].name,
            cycles: cycleCount,
            moodAfter: selectedMood
        };

        const existingStats = JSON.parse(localStorage.getItem('mlh_breathe_stats') || '[]');
        localStorage.setItem('mlh_breathe_stats', JSON.stringify([...existingStats, sessionData]));

        // Reset and close
        handleReset();
        // Optional: Navigate away or show success
    };

    const getInstructionText = () => {
        if (phase === 'inhale') return 'Breathe In';
        if (phase === 'hold1' || phase === 'hold2') return 'Hold';
        if (phase === 'exhale') return 'Breathe Out';
    };

    const getCircleScale = () => {
        if (phase === 'inhale') return 1.3;
        if (phase === 'hold1') return 1.3; // Stay expanded
        if (phase === 'exhale') return 0.8;
        if (phase === 'hold2') return 0.8; // Stay contracted
        return 1;
    };

    const moods = [
        { emoji: '😌', label: 'Calm' },
        { emoji: '😊', label: 'Better' },
        { emoji: '😐', label: 'Same' },
        { emoji: '😴', label: 'Sleepy' },
        { emoji: '⚡', label: 'Energized' }
    ];

    return (
        <PageContainer>
            {/* Floating orbs for ambiance */}
            <FloatingOrb
                animate={{ x: [0, 100, 0], y: [0, -50, 0] }}
                transition={{ repeat: Infinity, duration: 20, ease: "easeInOut" }}
                style={{ top: '10%', left: '10%' }}
            />
            <FloatingOrb
                animate={{ x: [0, -80, 0], y: [0, 60, 0] }}
                transition={{ repeat: Infinity, duration: 25, ease: "easeInOut" }}
                style={{ bottom: '20%', right: '15%' }}
            />

            <Header>
                <button onClick={() => navigate('/dashboard')}>
                    <ArrowLeft size={24} />
                </button>
                <span style={{ fontWeight: 600, color: '#2D3E50' }}>Back to Dashboard</span>
            </Header>

            <ContentCard
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6 }}
                style={{ position: 'relative', overflow: 'hidden' }}
            >
                <AnimatePresence>
                    {showFeedback && (
                        <FeedbackModal
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                        >
                            <FeedbackTitle>How do you feel now?</FeedbackTitle>
                            <MoodGrid>
                                {moods.map((m, i) => (
                                    <FeedbackMoodBtn
                                        key={i}
                                        $selected={selectedMood === m.label}
                                        onClick={() => setSelectedMood(m.label)}
                                    >
                                        <span>{m.emoji}</span>
                                        <span>{m.label}</span>
                                    </FeedbackMoodBtn>
                                ))}
                            </MoodGrid>
                            <div style={{ display: 'flex', gap: '1rem' }}>
                                <ControlButton onClick={() => setShowFeedback(false)}>
                                    <X size={20} /> Skip
                                </ControlButton>
                                <ControlButton primary disabled={!selectedMood} onClick={saveSession}>
                                    <Check size={20} /> Save Progress
                                </ControlButton>
                            </div>
                        </FeedbackModal>
                    )}
                </AnimatePresence>

                <Title>Guided Breathing</Title>
                <Subtitle>Take a moment to center yourself. Follow the rhythm.</Subtitle>

                <TechniqueSelector>
                    {Object.keys(techniques).map(key => (
                        <TechniqueButton
                            key={key}
                            $active={selectedTechnique === key}
                            onClick={() => handleTechniqueChange(key)}
                        >
                            {techniques[key].name}
                        </TechniqueButton>
                    ))}
                </TechniqueSelector>

                <BreathingCircle
                    animate={{ scale: getCircleScale() }}
                    transition={{ duration: counter, ease: "easeInOut" }}
                >
                    <div>
                        <InstructionText
                            key={phase}
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            transition={{ duration: 0.5 }}
                        >
                            {getInstructionText()}
                        </InstructionText>
                        <CounterText>{counter}</CounterText>
                    </div>
                </BreathingCircle>

                <p style={{ color: '#94A3B8', marginBottom: '1rem' }}>
                    {isActive || cycleCount > 0 ? (
                        <>Current Cycle: <strong>{cycleCount}</strong></>
                    ) : (
                        <>Ready to Start</>
                    )}
                </p>

                <ControlsRow>
                    {!isActive ? (
                        <ControlButton primary onClick={handleStart} whileTap={{ scale: 0.95 }}>
                            <Play size={20} /> Start
                        </ControlButton>
                    ) : (
                        <ControlButton onClick={handlePause} whileTap={{ scale: 0.95 }}>
                            <Pause size={20} /> Pause
                        </ControlButton>
                    )}
                    {cycleCount > 0 && !isActive ? (
                        <ControlButton onClick={handleFinish} style={{ background: '#F0FDF4', color: '#166534', borderColor: '#BBF7D0' }} whileTap={{ scale: 0.95 }}>
                            <Check size={20} /> Finish
                        </ControlButton>
                    ) : (
                        <ControlButton onClick={handleReset} whileTap={{ scale: 0.95 }}>
                            <RotateCcw size={20} /> Reset
                        </ControlButton>
                    )}
                </ControlsRow>
            </ContentCard>
        </PageContainer>
    );
}

