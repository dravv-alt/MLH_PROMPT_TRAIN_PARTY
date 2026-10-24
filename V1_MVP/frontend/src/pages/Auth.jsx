import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Lock, ArrowRight, User } from 'lucide-react';
import logo from '../assets/logo.png';

const AuthContainer = styled.div`
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  background: var(--bg-warm);
  position: relative;
  overflow: hidden;
`;

const AuroraBackground = styled.div`
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: radial-gradient(circle at 50% 50%, rgba(184, 216, 229, 0.2) 0%, rgba(255, 255, 255, 0) 60%),
              radial-gradient(circle at 80% 20%, rgba(250, 225, 221, 0.2) 0%, rgba(255, 255, 255, 0) 40%);
  filter: blur(80px);
  z-index: 0;
  animation: drift 20s infinite alternate ease-in-out;
`;

const AuthCard = styled(motion.div)`
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(24px);
  padding: 3rem;
  border-radius: 30px;
  box-shadow: 0 10px 40px rgba(166, 200, 216, 0.15);
  border: 1px solid rgba(255, 255, 255, 0.6);
  width: 100%;
  max-width: 420px;
  z-index: 10;
  text-align: center;
`;

const Title = styled.h2`
  font-size: 2rem;
  margin-bottom: 0.5rem;
  color: #2D3E50;
`;

const Subtitle = styled.p`
  color: var(--text-secondary);
  margin-bottom: 2rem;
`;

const InputGroup = styled.div`
  margin-bottom: 1.5rem;
  text-align: left;
  
  label {
    display: block;
    margin-bottom: 0.5rem;
    font-size: 0.9rem;
    color: #475569;
    font-weight: 500;
  }
  
  input {
    width: 100%;
    padding: 1rem;
    border-radius: 12px;
    border: 1px solid var(--ui-border);
    background: rgba(255, 255, 255, 0.9);
    font-size: 1.1rem;
    color: #2D3E50;
    transition: all 0.2s;
    outline: none;
    
    &:focus {
      border-color: var(--accent-sky);
      box-shadow: 0 0 0 3px rgba(184, 216, 229, 0.3);
    }
  }
`;

const ActionButton = styled(motion.button)`
  width: 100%;
  padding: 1rem;
  border-radius: 15px;
  background: var(--accent-sky);
  color: #1F3846;
  border: none;
  font-size: 1.1rem;
  font-weight: 600;
  margin-top: 1rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  
  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
  
  &:hover:not(:disabled) {
    background: #99BCCF;
    transform: translateY(-2px);
  }
`;

const ErrorMessage = styled(motion.div)`
  color: #C04D4D;
  background: #FFE4E4;
  padding: 0.75rem;
  border-radius: 10px;
  margin-bottom: 1.5rem;
  font-size: 0.9rem;
`;

export default function Auth() {
    const { login, signup, userExists, user } = useAuth();
    const navigate = useNavigate();
    const [isLoginMode, setIsLoginMode] = useState(() => userExists());

    const [name, setName] = useState('');
    const [pin, setPin] = useState('');
    const [error, setError] = useState('');

    useEffect(() => {
        // If user is already logged in (in context), redirect to dashboard
        if (user) {
            navigate('/dashboard');
        }
    }, [user, navigate]);

    const handleSubmit = (e) => {
        e.preventDefault();
        setError('');

        if (isLoginMode) {
            if (login(pin)) {
                navigate('/dashboard');
            } else {
                setError("Incorrect PIN. Please try again.");
            }
        } else {
            if (name.trim().length < 2) {
                setError("Please enter a name.");
                return;
            }
            if (pin.length < 4) {
                setError("PIN must be at least 4 digits.");
                return;
            }
            signup(name, pin);
            navigate('/dashboard');
        }
    };

    return (
        <AuthContainer>
            <AuroraBackground />

            <motion.img
                src={logo}
                alt="Sanctuary"
                style={{ height: '64px', marginBottom: '2rem', zIndex: 10 }}
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
            />

            <AuthCard
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ type: 'spring', stiffness: 300, damping: 20 }}
            >
                <Title>{isLoginMode ? 'Welcome Back' : 'Create Sanctuary'}</Title>
                <Subtitle>
                    {isLoginMode
                        ? 'Enter your private key to access your safe space.'
                        : 'Your data stays on this device. Create a profile to get started.'}
                </Subtitle>

                {error && (
                    <ErrorMessage
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                    >
                        {error}
                    </ErrorMessage>
                )}

                <form onSubmit={handleSubmit}>
                    <AnimatePresence mode="wait">
                        {!isLoginMode && (
                            <motion.div
                                key="name-input"
                                initial={{ opacity: 0, height: 0 }}
                                animate={{ opacity: 1, height: 'auto' }}
                                exit={{ opacity: 0, height: 0 }}
                            >
                                <InputGroup>
                                    <label>What should we call you?</label>
                                    <input
                                        type="text"
                                        placeholder="e.g. Alex"
                                        value={name}
                                        onChange={(e) => setName(e.target.value)}
                                    />
                                </InputGroup>
                            </motion.div>
                        )}
                    </AnimatePresence>

                    <InputGroup>
                        <label>{isLoginMode ? 'Your PIN' : 'Create a Privacy PIN'}</label>
                        <input
                            type="password"
                            placeholder="••••"
                            value={pin}
                            onChange={(e) => setPin(e.target.value)}
                            pattern="[0-9]*"
                            inputMode="numeric"
                            maxLength={4}
                        />
                    </InputGroup>

                    <ActionButton
                        whileTap={{ scale: 0.98 }}
                        type="submit"
                        disabled={!pin}
                    >
                        {isLoginMode ? 'Unlock Sanctuary' : 'Create Profile'}
                        {isLoginMode ? <Lock size={18} /> : <ArrowRight size={18} />}
                    </ActionButton>
                </form>

                {isLoginMode && ( // Option to reset if they forgot? For local privacy focus, maybe "Reset" clears data? Too dangerous for now.
                    <p style={{ marginTop: '1.5rem', fontSize: '0.8rem', color: '#94A3B8' }}>
                        Forgot your PIN? Clearing browser data will reset your sanctuary.
                    </p>
                )}
            </AuthCard>
        </AuthContainer>
    );
}
