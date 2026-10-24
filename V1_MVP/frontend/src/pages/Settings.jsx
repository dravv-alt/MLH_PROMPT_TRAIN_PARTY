import React, { useState } from 'react';
import styled from 'styled-components';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowLeft, Bell, Moon, Shield, Volume2, Trash2, LogOut, ChevronRight, Check } from 'lucide-react';
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
  margin-bottom: 2rem;
  
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

const SettingsCard = styled(motion.div)`
  background: var(--bg-card);
  width: 100%;
  max-width: 600px;
  border-radius: 24px;
  padding: 1rem;
  box-shadow: 0 4px 20px rgba(0,0,0,0.02);
  border: 1px solid var(--ui-border);
  overflow: hidden;
`;

const SectionTitle = styled.h3`
  font-size: 0.9rem;
  text-transform: uppercase;
  color: #94A3B8;
  margin: 1.5rem 1rem 0.75rem;
  letter-spacing: 0.05em;
  font-weight: 600;
  
  &:first-child { margin-top: 0.5rem; }
`;

const SettingItem = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
  
  &:hover {
    background: #F8FAFC;
  }
  
  &.danger:hover {
    background: #FEF2F2;
    color: #DC2626;
  }
`;

const IconLabel = styled.div`
  display: flex;
  align-items: center;
  gap: 1rem;
  color: var(--text-primary);
  font-weight: 500;
  
  .icon-box {
    width: 36px;
    height: 36px;
    border-radius: 8px;
    background: #F1F5F9;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #64748B;
  }
  
  &.danger {
    color: #DC2626;
    .icon-box { background: #FEE2E2; color: #DC2626; }
  }
`;

const Toggle = styled.div`
  width: 44px;
  height: 24px;
  background: ${props => props.$active ? '#10B981' : '#E2E8F0'};
  border-radius: 12px;
  position: relative;
  transition: all 0.2s;
  
  &::after {
    content: '';
    position: absolute;
    top: 2px;
    left: ${props => props.$active ? '22px' : '2px'};
    width: 20px;
    height: 20px;
    background: white;
    border-radius: 50%;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    transition: all 0.2s;
  }
`;

const ModalOverlay = styled(motion.div)`
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 50;
  padding: 2rem;
`;

const Modal = styled(motion.div)`
  background: var(--bg-card);
  padding: 2rem;
  border-radius: 24px;
  width: 100%;
  max-width: 400px;
  text-align: center;
  
  h3 { color: var(--text-primary); margin-bottom: 0.5rem; }
  p { color: var(--text-secondary); margin-bottom: 1.5rem; font-size: 0.95rem; line-height: 1.5; }
`;

const ButtonRow = styled.div`
  display: flex;
  gap: 1rem;
  
  button {
    flex: 1;
    padding: 0.75rem;
    border-radius: 12px;
    font-weight: 600;
    cursor: pointer;
    border: none;
    
    &.cancel { background: #F1F5F9; color: #475569; }
    &.confirm { background: #DC2626; color: white; }
  }
`;

export default function Settings() {
  const navigate = useNavigate();
  const { logout } = useAuth();

  // UI State
  const [notifications, setNotifications] = useState(true);
  const [voiceAuto, setVoiceAuto] = useState(true);
  const [showDeleteModal, setShowDeleteModal] = useState(false); const handleLogout = () => {
    logout();
    navigate('/auth');
  };

  const handleClearData = () => {
    localStorage.clear();
    navigate('/'); // Reset to landing or auth
    window.location.reload(); // Force full reset
  };

  return (
    <PageContainer>
      <Header>
        <button onClick={() => navigate('/dashboard')}>
          <ArrowLeft size={24} />
        </button>
        <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>Back to Dashboard</span>
      </Header>

      <h1 style={{ marginBottom: '2rem', color: 'var(--text-primary)' }}>Settings</h1>

      <SettingsCard
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <SectionTitle>Preferences</SectionTitle>



        <SettingItem onClick={() => setNotifications(!notifications)}>
          <IconLabel>
            <div className="icon-box"><Bell size={20} /></div>
            Daily Reminders
          </IconLabel>
          <Toggle $active={notifications} />
        </SettingItem>

        <SettingItem onClick={() => setVoiceAuto(!voiceAuto)}>
          <IconLabel>
            <div className="icon-box"><Volume2 size={20} /></div>
            Auto-Play Voice Responses
          </IconLabel>
          <Toggle $active={voiceAuto} />
        </SettingItem>

        <SectionTitle>Account</SectionTitle>

        {/* <SettingItem onClick={() => alert('Change PIN feature coming soon!')}>
                    <IconLabel>
                        <div className="icon-box"><Shield size={20} /></div>
                        Change PIN
                    </IconLabel>
                    <ChevronRight size={20} color="#CBD5E1" />
                </SettingItem> */}

        <SettingItem onClick={handleLogout}>
          <IconLabel>
            <div className="icon-box"><LogOut size={20} /></div>
            Log Out
          </IconLabel>
          <ChevronRight size={20} color="#CBD5E1" />
        </SettingItem>

        <SectionTitle style={{ color: '#EF4444' }}>Danger Zone</SectionTitle>

        <SettingItem className="danger" onClick={() => setShowDeleteModal(true)}>
          <IconLabel className="danger">
            <div className="icon-box"><Trash2 size={20} /></div>
            Clear All Data
          </IconLabel>
        </SettingItem>

      </SettingsCard>

      <AnimatePresence>
        {showDeleteModal && (
          <ModalOverlay
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <Modal
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
            >
              <Trash2 size={48} color="#DC2626" style={{ marginBottom: '1rem' }} />
              <h3>Are you sure?</h3>
              <p>This will delete your account, journal entries, and all statistics. This action cannot be undone.</p>
              <ButtonRow>
                <button className="cancel" onClick={() => setShowDeleteModal(false)}>Cancel</button>
                <button className="confirm" onClick={handleClearData}>Delete Everything</button>
              </ButtonRow>
            </Modal>
          </ModalOverlay>
        )}
      </AnimatePresence>

    </PageContainer>
  );
}
