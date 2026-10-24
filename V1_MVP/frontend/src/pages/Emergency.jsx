import React from 'react';
import styled from 'styled-components';
import { motion } from 'framer-motion';
import { Phone, Shield, ExternalLink, Heart, AlertTriangle, ArrowLeft } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const PageContainer = styled.div`
  min-height: 100vh;
  background: #FEF2F2; /* Very soft red background to signal importance but stay calm */
  padding: 2rem;
  display: flex;
  flex-direction: column;
  align-items: center;
`;

const Header = styled.div`
  width: 100%;
  max-width: 800px;
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 3rem;
  
  button {
    background: white;
    border: 1px solid #FECACA;
    padding: 0.5rem;
    border-radius: 50%;
    cursor: pointer;
    color: #991B1B;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.2s;
    
    &:hover {
        transform: scale(1.05);
        background: #FEE2E2;
    }
  }
`;

const TitleSection = styled.div`
  text-align: center;
  margin-bottom: 3rem;
  
  h1 {
    font-size: 2.5rem;
    color: #991B1B;
    margin-bottom: 1rem;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 1rem;
  }
  
  p {
    font-size: 1.2rem;
    color: #7F1D1D;
    max-width: 600px;
    margin: 0 auto;
  }
`;

const ResourceGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1.5rem;
  width: 100%;
  max-width: 800px;
`;

const ResourceCard = styled(motion.a)`
  background: white;
  padding: 2rem;
  border-radius: 24px;
  border: 1px solid #FECACA;
  text-decoration: none;
  color: inherit;
  transition: all 0.3s ease;
  box-shadow: 0 4px 6px rgba(0,0,0,0.02);
  display: flex;
  flex-direction: column;
  gap: 1rem;
  position: relative;
  overflow: hidden;
  
  &:hover {
    transform: translateY(-5px);
    box-shadow: 0 10px 20px rgba(153, 27, 27, 0.1);
    border-color: #F87171;
  }
  
  &.primary {
    background: #DC2626;
    color: white;
    border: none;
    
    h3, p { color: white; }
    .icon-bg { background: rgba(255,255,255,0.2); }
  }
`;

const IconBox = styled.div`
  width: 48px;
  height: 48px;
  border-radius: 12px;
  background: #FEF2F2;
  color: #DC2626;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 0.5rem;
  
  &.white {
    background: rgba(255,255,255,0.2);
    color: white;
  }
`;

const CardTitle = styled.h3`
  font-size: 1.5rem;
  font-weight: 700;
  color: #1F2937;
  margin: 0;
`;

const CardDesc = styled.p`
  color: #4B5563;
  margin: 0;
  font-size: 0.95rem;
  line-height: 1.5;
`;

const ActionRow = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: auto; /* Push to bottom */
  font-weight: 600;
  font-size: 0.9rem;
`;

const Disclaimer = styled.p`
  margin-top: 4rem;
  font-size: 0.85rem;
  color: #9CA3AF;
  text-align: center;
  max-width: 500px;
`;

export default function Emergency() {
  const navigate = useNavigate();

  return (
    <PageContainer>
      <Header>
        <button onClick={() => navigate('/dashboard')}>
          <ArrowLeft size={24} />
        </button>
        <span style={{ fontWeight: 600, color: '#991B1B' }}>Exit to Dashboard</span>
      </Header>

      <TitleSection>
        <motion.h1
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <Shield size={42} /> Crisis Support
        </motion.h1>
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2 }}
        >
          You are important. If you are in pain, please reach out to one of these free, confidential resources.
        </motion.p>
      </TitleSection>

      <ResourceGrid>
        {/* Primary Action - Tele-Manas */}
        <ResourceCard
          href="tel:14416"
          className="primary"
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.3 }}
        >
          <IconBox className="white"><Phone size={24} /></IconBox>
          <CardTitle>Call 14416 (Tele-Manas)</CardTitle>
          <CardDesc>
            Govt of India's 24/7 Mental Health Support. Free, confidential support across languages.
          </CardDesc>
          <ActionRow style={{ color: 'white' }}>
            <span>Tap to Call</span>
            <ExternalLink size={18} />
          </ActionRow>
        </ResourceCard>

        {/* Kiran Helpline */}
        <ResourceCard
          href="tel:18005990019"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
        >
          <IconBox><Phone size={24} /></IconBox>
          <CardTitle>1800-599-0019 (Kiran)</CardTitle>
          <CardDesc>
            24/7 Mental Health Rehabilitation Helpline by Govt of India.
          </CardDesc>
          <ActionRow style={{ color: '#DC2626' }}>
            <span>Tap to Call</span>
            <ExternalLink size={18} />
          </ActionRow>
        </ResourceCard>

        {/* Vandrevala Foundation */}
        <ResourceCard
          href="tel:18602662345"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
        >
          <IconBox><Heart size={24} /></IconBox>
          <CardTitle>Vandrevala Foundation</CardTitle>
          <CardDesc>
            Free, 24/7 counseling and crisis mediation via phone or WhatsApp.
          </CardDesc>
          <ActionRow style={{ color: '#DC2626' }}>
            <span>Visit Website</span>
            <ExternalLink size={18} />
          </ActionRow>
        </ResourceCard>

        {/* International */}
        <ResourceCard
          href="https://findahelpline.com/"
          target="_blank"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
        >
          <IconBox><AlertTriangle size={24} /></IconBox>
          <CardTitle>Find A Helpline</CardTitle>
          <CardDesc>
            Directory of helplines for other countries and specialized needs.
          </CardDesc>
          <ActionRow style={{ color: '#DC2626' }}>
            <span>Search Directory</span>
            <ExternalLink size={18} />
          </ActionRow>
        </ResourceCard>

      </ResourceGrid>

      <Disclaimer>
        Sanctuary is an AI tool and cannot provide medical assistance. If you are in immediate danger, please call your local emergency services (112 in India) or go to the nearest emergency room.
      </Disclaimer>
    </PageContainer>
  );
}
