import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { motion } from 'framer-motion';
import { ArrowLeft, User, Mail, Calendar, Edit2, Check, Save } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

// --- Styled Components ---

const PageContainer = styled.div`
  min-height: 100vh;
  background: var(--bg-warm);
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 2rem;
`;

const Header = styled.div`
  width: 100%;
  max-width: 600px;
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 3rem;
  
  button {
    background: var(--bg-card);
    border: 1px solid var(--ui-border);
    padding: 0.5rem;
    border-radius: 50%;
    cursor: pointer;
    color: var(--text-secondary);
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.2s;
    
    &:hover {
      transform: scale(1.05);
      background: var(--bg-sage);
      color: #2D3E50;
    }
  }
`;

const ProfileCard = styled(motion.div)`
  background: var(--bg-card);
  width: 100%;
  max-width: 600px;
  border-radius: 32px;
  padding: 3rem;
  box-shadow: 0 20px 40px rgba(0,0,0,0.04);
  display: flex;
  flex-direction: column;
  align-items: center;
  position: relative;
  overflow: hidden;
  
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 150px;
    background: linear-gradient(135deg, #B8D8E5 0%, #D1E8D5 100%);
    z-index: 0;
  }
`;

const Avatar = styled.div`
  width: 120px;
  height: 120px;
  border-radius: 50%;
  background: var(--bg-card);
  border: 4px solid white;
  box-shadow: 0 10px 20px rgba(0,0,0,0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #2D3E50;
  z-index: 1;
  margin-bottom: 2rem;
  margin-top: 1rem;
`;

const InfoGroup = styled.div`
  width: 100%;
  margin-bottom: 1.5rem;
`;

const Label = styled.label`
  display: block;
  font-size: 0.9rem;
  color: var(--text-secondary);
  margin-bottom: 0.5rem;
  font-weight: 500;
`;

const InputWrapper = styled.div`
  display: flex;
  align-items: center;
  background: var(--bg-input);
  border: 1px solid ${props => props.$isEditing ? '#94A3B8' : 'transparent'};
  border-radius: 12px;
  padding: 0.75rem 1rem;
  transition: all 0.2s;
`;

const Input = styled.input`
  flex: 1;
  border: none;
  background: transparent;
  font-size: 1.1rem;
  color: var(--text-primary);
  font-weight: 500;
  outline: none;
  pointer-events: ${props => props.$isEditing ? 'all' : 'none'};
`;

const EditButton = styled.button`
  background: none;
  border: none;
  color: #64748B;
  cursor: pointer;
  padding: 0.25rem;
  
  &:hover {
    color: var(--primary);
  }
`;

const StatRow = styled.div`
  display: flex;
  gap: 1rem;
  width: 100%;
  margin-top: 2rem;
`;

const StatBox = styled.div`
  flex: 1;
  background: var(--bg-input);
  border-radius: 16px;
  padding: 1.5rem;
  text-align: center;
  
  h4 {
    font-size: 2rem;
    color: var(--text-primary);
    margin-bottom: 0.25rem;
  }
  
  span {
    font-size: 0.9rem;
    color: var(--text-secondary);
  }
`;

export default function Profile() {
  const navigate = useNavigate();
  const { user, login } = useAuth(); // Assuming login updates user context
  const [name, setName] = useState(user?.name || 'User');
  const [isEditing, setIsEditing] = useState(false);
  const [stats, setStats] = useState({ entries: 0, sessions: 0 });

  useEffect(() => {
    // Load stats
    const journal = JSON.parse(localStorage.getItem('mlh_journal') || '{}');
    const breathe = JSON.parse(localStorage.getItem('mlh_breathe_stats') || '[]');
    setStats({
      entries: Object.keys(journal).length,
      sessions: breathe.length
    });
  }, []);

  const handleSave = () => {
    setIsEditing(false);
    // Update user in local storage
    if (user) {
      const updatedUser = { ...user, name: name };
      localStorage.setItem('mlh_user', JSON.stringify(updatedUser));
      // Force reload or update context (Context might not auto-update if not designed to listen to storage)
      // Ideally call a context method. Since we don't have updateProfile in context, we might need to manually refresh or just accept visual persistence.
      // A simple hack is updating the state, which we did. But context needs to know.
      // If we don't update context, header greeting won't change until refresh.
      // Let's assume simpler approach: just update storage.
      window.location.reload(); // Simple way to propagate name change everywhere
    }
  };

  return (
    <PageContainer>
      <Header>
        <button onClick={() => navigate('/dashboard')}>
          <ArrowLeft size={24} />
        </button>
        <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>Back to Dashboard</span>
      </Header>

      <ProfileCard
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <Avatar>
          <User size={64} color="#94A3B8" />
        </Avatar>

        <InfoGroup>
          <Label>Display Name</Label>
          <InputWrapper $isEditing={isEditing}>
            <User size={20} color="#94A3B8" style={{ marginRight: '0.75rem' }} />
            <Input
              value={name}
              onChange={(e) => setName(e.target.value)}
              $isEditing={isEditing}
            />
            {isEditing ? (
              <EditButton onClick={handleSave}>
                <Check size={20} color="#10B981" />
              </EditButton>
            ) : (
              <EditButton onClick={() => setIsEditing(true)}>
                <Edit2 size={18} />
              </EditButton>
            )}
          </InputWrapper>
        </InfoGroup>

        <InfoGroup>
          <Label>Member Since</Label>
          <InputWrapper>
            <Calendar size={20} color="#94A3B8" style={{ marginRight: '0.75rem' }} />
            <Input value="October 2024" readOnly />
          </InputWrapper>
        </InfoGroup>

        <StatRow>
          <StatBox>
            <h4>{stats.entries}</h4>
            <span>Journal Entries</span>
          </StatBox>
          <StatBox>
            <h4>{stats.sessions}</h4>
            <span>Breathing Sessions</span>
          </StatBox>
        </StatRow>

      </ProfileCard>
    </PageContainer>
  );
}
