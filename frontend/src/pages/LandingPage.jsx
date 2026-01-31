import React from 'react';
import { useNavigate } from 'react-router-dom';
import styled from 'styled-components';
import { motion, useScroll, useTransform } from 'framer-motion';
import { Mic, Shield, Heart, Activity, ArrowRight, Menu, BookOpen, MessageCircle } from 'lucide-react';
import logo from '../assets/logo.png';

// --- Components ---

// 1. Navigation Bar
const Navbar = styled(motion.nav)`
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  padding: 1rem 3rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  z-index: 100;
  background: rgba(254, 252, 248, 0.85);
  backdrop-filter: blur(24px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.5);
  transition: all 0.3s ease;
`;

const LogoContainer = styled.div`
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-family: var(--font-heading);
  font-weight: 700;
  font-size: 1.75rem;
  color: #5D7B89;
  
  img {
    height: 64px;
    width: auto;
    object-fit: contain;
  }
`;

const NavLinks = styled.div`
  display: flex;
  gap: 2.5rem;
  align-items: center;
  
  @media (max-width: 768px) {
    display: none;
  }
`;

const NavLink = styled.a`
  font-size: 1rem;
  font-weight: 500;
  color: var(--text-secondary);
  transition: color var(--transition-medium);
  
  &:hover {
    color: var(--text-primary);
  }
`;

const EmergencyButton = styled.a`
  border: 1px solid #FCA5A5;
  color: #C04D4D;
  background: rgba(255, 245, 245, 0.6);
  padding: 0.5rem 1rem;
  border-radius: 50px;
  font-size: 0.9rem;
  font-weight: 600;
  transition: all var(--transition-medium);
  
  &:hover {
    background: #FFF0F0;
    transform: translateY(-1px);
  }
`;

const PrimaryButton = styled(motion.button)`
  background: var(--accent-sky);
  color: #1F3846;
  padding: 0.75rem 1.75rem;
  border-radius: 50px;
  font-weight: 600;
  font-size: 1rem;
  box-shadow: 0 4px 14px rgba(166, 200, 216, 0.4);
  transition: all 0.2s ease;
  
  &:hover {
    background: #99BCCF;
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(166, 200, 216, 0.6);
  }
`;

// 2. Hero Section w/ Aurora Background
const HeroSection = styled.section`
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  text-align: center;
  position: relative;
  overflow: hidden;
  padding-top: 80px;
  background: var(--bg-warm);
`;

const AuroraBackground = styled.div`
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: radial-gradient(circle at 60% 40%, rgba(184, 216, 229, 0.35) 0%, rgba(255, 255, 255, 0) 60%),
              radial-gradient(circle at 20% 20%, rgba(250, 225, 221, 0.3) 0%, rgba(255, 255, 255, 0) 40%);
  filter: blur(80px);
  z-index: 0;
  animation: drift 20s infinite alternate ease-in-out;

  &::after {
    content: '';
    position: absolute;
    top: 20%;
    left: 20%;
    width: 60%;
    height: 60%;
    background: radial-gradient(circle at 50% 60%, rgba(209, 232, 213, 0.35) 0%, rgba(255, 255, 255, 0) 70%);
    animation: breathe 10s infinite alternate ease-in-out;
  }

  @keyframes drift {
    0% { transform: translate(0, 0) rotate(0deg); }
    100% { transform: translate(-20px, 20px) rotate(2deg); }
  }

  @keyframes breathe {
    0% { transform: scale(1); opacity: 0.6; }
    100% { transform: scale(1.1); opacity: 0.9; }
  }
`;

const HeroContent = styled(motion.div)`
  z-index: 10;
  max-width: 900px;
  padding: 0 2rem;
`;

const Headline = styled.h1`
  margin-bottom: 1.5rem;
  color: #2D3E50;
  letter-spacing: -0.03em;
  font-weight: 700;
  line-height: 1.1;
  
  span {
    color: #8BAEB8;
  }
`;

const Subheadline = styled.p`
  font-size: 1.35rem;
  margin-bottom: 2.5rem;
  max-width: 650px;
  margin-left: auto;
  margin-right: auto;
  color: var(--text-secondary);
  font-weight: 400;
`;

const ButtonGroup = styled.div`
  display: flex;
  gap: 1.5rem;
  justify-content: center;
  margin-bottom: 5rem;
`;

const SecondaryButton = styled(PrimaryButton)`
  background: white;
  border: 1px solid #E2E8F0;
  color: var(--text-primary);
  box-shadow: var(--shadow-soft);
  
  &:hover {
    background: #F8FAFC;
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.05);
  }
`;

// 3. Trust Signals
const TrustSection = styled(motion.div)`
  display: flex;
  justify-content: center;
  gap: 2rem;
  flex-wrap: wrap;
  padding: 2rem;
  z-index: 10;
  margin-top: -60px;
  
  @media (max-width: 768px) {
    margin-top: 1rem;
  }
`;

const TrustCard = styled(motion.div)`
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(12px);
  padding: 1.5rem 2rem;
  border-radius: 20px;
  display: flex;
  align-items: center;
  gap: 1rem;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.04);
  max-width: 360px;
  border: 1px solid rgba(255, 255, 255, 0.6);
  transition: transform 0.3s ease;

  &:hover {
    transform: translateY(-5px);
  }
`;

const IconWrapper = styled.div`
  background: #F1F6F9;
  padding: 0.75rem;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #7A9EAF;
`;

// 5. Feature Section
const FeatureSection = styled.section`
  padding: 6rem 2rem;
  max-width: 1200px;
  margin: 0 auto;
`;

const SectionTitle = styled(motion.h2)`
  text-align: center;
  margin-bottom: 1rem;
  font-size: 2.5rem;
  color: #2D3E50;
`;

const SectionSubtitle = styled.p`
  text-align: center;
  max-width: 600px;
  margin: 0 auto 4rem auto;
  font-size: 1.1rem;
`;

const FeaturesGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 2rem;
`;

const FeatureCard = styled(motion.div)`
  background: white;
  padding: 2.5rem;
  border-radius: 30px;
  box-shadow: var(--shadow-soft);
  transition: transform 0.3s ease;
  border: 1px solid #F1F5F9;
  
  &:hover {
    transform: translateY(-8px);
    box-shadow: var(--shadow-float);
  }
  
  h3 {
    margin: 1.5rem 0 0.5rem;
    font-size: 1.25rem;
    color: #2D3E50;
  }
  
  p {
    font-size: 0.95rem;
    line-height: 1.6;
  }
`;

// 5b. Testimonials Section
const TestimonialSection = styled.section`
  padding: 6rem 2rem;
  background: transparent;
`;

const TestimonialGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 2.5rem;
  max-width: 1200px;
  margin: 0 auto;
`;

const TestimonialCard = styled(motion.div)`
  background: var(--bg-sage);
  padding: 2.5rem;
  border-radius: 24px;
  position: relative;
  
  &::before {
    content: '"';
    position: absolute;
    top: 1rem;
    left: 2rem;
    font-size: 5rem;
    color: rgba(166, 200, 216, 0.5);
    font-family: serif;
    line-height: 1;
  }
`;

const UserInfo = styled.div`
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-top: 1.5rem;
`;

const UserAvatar = styled.div`
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: #D8D4E3;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  color: #5D7B89;
  font-size: 1.2rem;
`;

// 6. Voice Feature Section
const VoiceSection = styled.section`
  background: transparent;
  padding: 6rem 2rem;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  position: relative;
`;

const VoiceContent = styled.div`
  max-width: 1100px;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 5rem;
  align-items: center;
  z-index: 2;
  
  @media (max-width: 900px) {
    grid-template-columns: 1fr;
    text-align: center;
  }
`;

const WaveformContainer = styled(motion.div)`
  height: 320px;
  background: white;
  border-radius: 40px;
  box-shadow: 0 20px 60px rgba(166, 200, 216, 0.25);
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
`;

// Main App Component
export default function LandingPage() {
  const navigate = useNavigate();
  // const { scrollYProgress } = useScroll(); // Unused for now
  // const y = useTransform(scrollYProgress, [0, 1], [0, -50]); // Unused

  return (
    <>
      <Navbar
        initial={{ y: -100 }}
        animate={{ y: 0 }}
        transition={{ duration: 0.6, ease: "easeOut" }}
      >
        <LogoContainer style={{ borderRadius: '50px' }}>
          <img src={logo} alt="Sanctuary Logo" />
          Sanctuary
        </LogoContainer>

        <NavLinks>
          <NavLink href="#how-it-works">How it works</NavLink>
          <NavLink href="#safety">Safety</NavLink>
          <NavLink href="#resources">Resources</NavLink>
          <EmergencyButton href="#emergency">Emergency Resources</EmergencyButton>
        </NavLinks>

        <div style={{ display: 'flex', gap: '1rem' }}>
          <SecondaryButton style={{ padding: '0.5rem 1.5rem', border: 'none', background: 'transparent', boxShadow: 'none' }} onClick={() => navigate('/auth')}>Log in</SecondaryButton>
          <PrimaryButton onClick={() => navigate('/auth')}>Get Started</PrimaryButton>
        </div>
      </Navbar>

      <HeroSection>
        <AuroraBackground />

        <HeroContent
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1 }}
        >
          <Headline>
            Finding the right words is hard. <br />
            <span>Finding support shouldn’t be.</span>
          </Headline>
          <Subheadline>
            A calm, private space to talk, reflect, and feel supported — whenever you need it.
          </Subheadline>

          <ButtonGroup>
            <PrimaryButton
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => navigate('/auth')}
            >
              Log in to start chatting
            </PrimaryButton>
            <SecondaryButton
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => navigate('/auth')}
            >
              Create a free account
            </SecondaryButton>
          </ButtonGroup>
        </HeroContent>

        <TrustSection
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4, duration: 0.8 }}
        >
          <TrustCard>
            <IconWrapper><Shield size={24} /></IconWrapper>
            <div>
              <h3>Private by Design</h3>
              <p style={{ margin: 0, fontSize: '0.9rem' }}>Conversations are usually 100% anonymous & private.</p>
            </div>
          </TrustCard>

          <TrustCard>
            <IconWrapper><Heart size={24} /></IconWrapper>
            <div>
              <h3>Empathy First</h3>
              <p style={{ margin: 0, fontSize: '0.9rem' }}>Designed to listen, validate, and support.</p>
            </div>
          </TrustCard>

          <TrustCard>
            <IconWrapper><Activity size={24} /></IconWrapper>
            <div>
              <h3>Low Barrier Access</h3>
              <p style={{ margin: 0, fontSize: '0.9rem' }}>No waiting lists. Start chatting instantly.</p>
            </div>
          </TrustCard>
        </TrustSection>
      </HeroSection>

      <FeatureSection id="how-it-works">
        <SectionTitle
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
        >
          Support that meets you where you are
        </SectionTitle>
        <SectionSubtitle>
          Sanctuary combines empathetic AI with proven mental health tools to help you navigate life's challenges.
        </SectionSubtitle>

        <FeaturesGrid>
          {[
            { icon: <MessageCircle />, title: "Talk it out", desc: "Conversational AI trained for empathy. No pressure to say things 'right'." },
            { icon: <Mic />, title: "Voice Compassion", desc: "Speak naturally with our AI. A calm voice to guide you when typing feels like too much." },
            { icon: <Activity />, title: "Understand emotions", desc: "Reflective prompts and emotional pattern recognition to help you grow daily." },
            { icon: <Heart />, title: "Calm moments", desc: "Grounding exercises, breathing guidance, and crisis-aware responses." },
            { icon: <BookOpen />, title: "Private Journal", desc: "A secure space to log your thoughts and track your journey in privacy." },
            { icon: <Shield />, title: "Seek more help", desc: "Transparent safety boundaries encouraging human support when needed." }
          ].map((feature, index) => (
            <FeatureCard
              key={index}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: index * 0.1 }}
            >
              <IconWrapper style={{ width: 'fit-content', marginBottom: '1rem' }}>{feature.icon}</IconWrapper>
              <h3>{feature.title}</h3>
              <p>{feature.desc}</p>
            </FeatureCard>
          ))}
        </FeaturesGrid>
      </FeatureSection>

      <TestimonialSection>
        <SectionTitle
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
        >
          Stories from our Community
        </SectionTitle>
        <TestimonialGrid>
          {[
            { text: "I was having a panic attack at 3 AM. Sanctuary talked me down when I couldn't wake anyone up.", author: "Anonymous Student", initial: "A" },
            { text: "Usually I feel judged when I talk about my anxiety. Here, I just feel heard. It's my safe space.", author: "Sarah M.", initial: "S" },
            { text: "The breathing exercises are a lifesaver before exams. Simple, but they actually work.", author: "Davide", initial: "D" }
          ].map((t, i) => (
            <TestimonialCard
              key={i}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.1 }}
            >
              <p style={{ position: 'relative', zIndex: 1, fontSize: '1.1rem', fontStyle: 'italic', color: '#2D3E50' }}>
                {t.text}
              </p>
              <UserInfo>
                <UserAvatar>{t.initial}</UserAvatar>
                <div>
                  <p style={{ margin: 0, fontWeight: 600, color: '#2D3E50' }}>{t.author}</p>
                  <p style={{ margin: 0, fontSize: '0.8rem', color: '#7A9EAF' }}>Verified Member</p>
                </div>
              </UserInfo>
            </TestimonialCard>
          ))}
        </TestimonialGrid>
      </TestimonialSection>

      <VoiceSection>
        <VoiceContent>
          <motion.div
            initial={{ opacity: 0, x: -50 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
          >
            <h2 style={{ fontSize: '3rem', marginBottom: '1.5rem', color: '#2D3E50', lineHeight: 1.1 }}>
              Sometimes talking is <br />easier than typing.
            </h2>
            <p style={{ fontSize: '1.2rem', marginBottom: '2.5rem', color: 'var(--text-secondary)' }}>
              Use your voice when words feel heavy. Speak naturally and listen to calming responses.
            </p>
            <PrimaryButton style={{ padding: '1rem 2rem' }} onClick={() => navigate('/auth')}>
              Try Voice Support <ArrowRight size={18} style={{ marginLeft: '8px', verticalAlign: 'middle' }} />
            </PrimaryButton>
          </motion.div>

          <WaveformContainer
            initial={{ opacity: 0, scale: 0.9 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
          >
            <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
              {[1, 2, 3, 4, 5, 6, 7].map((i) => (
                <motion.div
                  key={i}
                  animate={{ height: [24, 64 + (Math.sin(i) * 20 + 20), 24] }} // Deterministic pseudo-randomness
                  transition={{ repeat: Infinity, duration: 1.2 + (i * 0.1), ease: "easeInOut", delay: i * 0.05 }}
                  style={{ width: '12px', background: 'var(--accent-sky)', borderRadius: '6px', opacity: 0.8 }}
                />
              ))}
            </div>
            <p style={{ position: 'absolute', bottom: '2rem', color: '#A0AEC0', fontSize: '0.9rem', fontWeight: 500 }}>
              AI Listening...
            </p>
          </WaveformContainer>
        </VoiceContent>
      </VoiceSection>

      {/* Footer */}
      <footer style={{ padding: '6rem 2rem 4rem', textAlign: 'center', background: 'white', borderTop: '1px solid #F1F5F9' }}>
        <Headline style={{ fontSize: '2.5rem', marginBottom: '1rem' }}>You don’t have to do this alone.</Headline>
        <p style={{ marginBottom: '2.5rem', fontSize: '1.1rem' }}>Start a private conversation. Take a breath. We’ll meet you there.</p>
        <div style={{ marginBottom: '5rem' }}>
          <PrimaryButton style={{ padding: '1rem 3rem', fontSize: '1.1rem' }} onClick={() => navigate('/auth')}>Join Sanctuary</PrimaryButton>
        </div>

        <div style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', maxWidth: '600px', margin: '0 auto', opacity: 0.8 }}>
          <p style={{ marginBottom: '0.5rem' }}>Sanctuary is an AI support tool and not a licensed medical professional.</p>
          <p>If you are in immediate danger, please contact your local emergency services.</p>
          <div style={{ display: 'flex', gap: '2rem', justifyContent: 'center', marginTop: '3rem', fontWeight: 500 }}>
            <a href="#">Privacy Policy</a>
            <a href="#">Terms of Service</a>
            <a href="#">Medical Disclaimer</a>
          </div>
          <p style={{ marginTop: '3rem', fontSize: '0.8rem', opacity: 0.5 }}>© 2026 Sanctuary. All rights reserved.</p>
        </div>
      </footer>
    </>
  );
}
