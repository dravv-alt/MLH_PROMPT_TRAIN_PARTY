import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowLeft, Save, Calendar as CalendarIcon, MoreVertical, Plus, ChevronLeft, ChevronRight, Check, Moon, Activity } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

// --- Styled Components ---

const PageContainer = styled.div`
  min-height: 100vh;
  background: var(--bg-warm); // Warm cream background
  display: flex;
  flex-direction: column;
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

const HeaderTitle = styled.h2`
  font-size: 1.1rem;
  color: #2D3E50;
  margin: 0;
  font-weight: 600;
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

const ContentLayout = styled.div`
  display: flex;
  flex: 1;
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
  padding: 2rem;
  gap: 3rem;

  @media (max-width: 900px) {
    flex-direction: column;
    padding: 1rem;
    gap: 1.5rem;
  }
`;

const Sidebar = styled.aside`
  width: 320px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 2rem;

  @media (max-width: 900px) {
    width: 100%;
  }
`;

const MainContent = styled.main`
  flex: 1;
  background: white;
  border-radius: 24px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.02);
  border: 1px solid var(--ui-border);
  padding: 2.5rem;
  min-height: 500px;
  position: relative;
  display: flex;
  flex-direction: column;
`;

// Calendar Styles
const CalendarCard = styled.div`
  background: white;
  border-radius: 20px;
  padding: 1.5rem;
  border: 1px solid var(--ui-border);
  box-shadow: 0 4px 15px rgba(0,0,0,0.02);
`;

const CalendarHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  
  h3 {
    margin: 0;
    font-size: 1.1rem;
    color: #2D3E50;
  }
`;

const WeekDays = styled.div`
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  text-align: center;
  font-size: 0.8rem;
  color: #94A3B8;
  margin-bottom: 0.5rem;
`;

const DaysGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 4px;
`;

const DayCell = styled.button`
  aspect-ratio: 1;
  border: none;
  background: ${props => props.$isSelected ? 'var(--accent-sky)' : props.$hasEntry ? '#F1F5F9' : 'transparent'};
  color: ${props => props.$isSelected ? '#1F3846' : '#475569'};
  border-radius: 50%;
  font-size: 0.9rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  transition: all 0.2s;

  &:hover {
    background: ${props => props.$isSelected ? 'var(--accent-sky)' : '#F8FAFC'};
  }

  ${props => props.$hasEntry && !props.$isSelected && `
    &::after {
      content: '';
      position: absolute;
      bottom: 4px;
      width: 4px;
      height: 4px;
      background: #8BAEB8;
      border-radius: 50%;
    }
  `}
`;

// Entry List Styles
const EntryList = styled.div`
  display: flex;
  flex-direction: column;
  gap: 1rem;
`;

const EntryCard = styled.div`
  background: white;
  padding: 1rem;
  border-radius: 16px;
  border: 1px solid transparent;
  cursor: pointer;
  transition: all 0.2s;
  
  &:hover {
    background: #F8FAFC;
    transform: translateY(-2px);
  }
`;

const EntryDate = styled.div`
  font-size: 0.8rem;
  color: #94A3B8;
  margin-bottom: 0.25rem;
`;

const EntryPreview = styled.div`
  font-size: 0.95rem;
  color: #334155;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
`;

// Editor Styles
const DateHeader = styled.div`
  margin-bottom: 2rem;
  
  h1 {
    font-size: 2rem;
    color: #2D3E50;
    margin: 0 0 0.5rem 0;
  }
  
  p {
    color: #64748B;
    margin: 0;
  }
`;

const EditorArea = styled.textarea`
  flex: 1;
  width: 100%;
  border: none;
  resize: none;
  font-size: 1.1rem;
  line-height: 1.8;
  color: #334155;
  outline: none;
  background: transparent;
  font-family: inherit;
  
  &::placeholder {
    color: #CBD5E1;
  }
`;

const MoodSelector = styled.div`
  display: flex;
  gap: 1rem;
  margin-bottom: 2rem;
  padding-bottom: 1.5rem;
  border-bottom: 1px solid #F1F5F9;
`;

const MetricsGrid = styled.div`
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
  margin-bottom: 2rem;
`;

const MetricCard = styled.div`
  background: #F8FAFC;
  padding: 1rem;
  border-radius: 16px;
  
  label {
    display: block;
    font-size: 0.85rem;
    color: #64748B;
    margin-bottom: 0.5rem;
    font-weight: 500;
  }
`;

const RangeInput = styled.input`
  width: 100%;
  accent-color: var(--accent-sky);
`;

const MoodBtn = styled.button`
  background: ${props => props.$selected ? 'var(--bg-sage)' : 'white'};
  border: 1px solid ${props => props.$selected ? '#CBD5E1' : '#E2E8F0'};
  padding: 0.5rem 1rem;
  border-radius: 20px;
  font-size: 1.2rem;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  gap: 0.5rem;
  align-items: center;

  span {
    font-size: 0.9rem;
    color: #475569;
  }

  &:hover {
    background: var(--bg-sage);
  }
`;

const SaveButton = styled(motion.button)`
  position: absolute;
  top: 2.5rem;
  right: 2.5rem;
  background: var(--accent-sky);
  color: #1F3846;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 12px;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  
  &:disabled {
    opacity: 0.5;
    cursor: default;
  }
`;

// Helper for Calendar Generation
const daysInMonth = (month, year) => new Date(year, month + 1, 0).getDate();
const firstDayOfMonth = (month, year) => new Date(year, month, 1).getDay();

export default function Journal() {
  const navigate = useNavigate();
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [currentMonth, setCurrentMonth] = useState(new Date().getMonth());
  const [currentYear, setCurrentYear] = useState(new Date().getFullYear());
  const [entryText, setEntryText] = useState('');
  const [selectedMood, setSelectedMood] = useState(null);
  const [sleep, setSleep] = useState(7); // Default 7 hours
  const [stress, setStress] = useState(3); // Default moderate stress
  const [entries, setEntries] = useState({}); // { "YYYY-MM-DD": { text: "...", mood: "...", sleep: 7, stress: 3 } }
  const [isSaved, setIsSaved] = useState(false);

  // Check LocalStorage for existing data
  useEffect(() => {
    const saved = localStorage.getItem('mlh_journal');
    if (saved) {
      setEntries(JSON.parse(saved));
    }
  }, []);

  // Update editor when date Selection Changes
  useEffect(() => {
    const key = selectedDate.toISOString().split('T')[0];
    const existing = entries[key];
    if (existing) {
      setEntryText(existing.text);
      setSelectedMood(existing.mood);
      setSleep(existing.sleep || 7);
      setStress(existing.stress || 3);
      setIsSaved(true);
    } else {
      setEntryText('');
      setSelectedMood(null);
      setSleep(7);
      setStress(3); // Reset to default
      setIsSaved(false);
    }
  }, [selectedDate, entries]);

  const handleTextChange = (e) => {
    setEntryText(e.target.value);
    setIsSaved(false);
  };

  const handleMoodChange = (m) => {
    setSelectedMood(m);
    setIsSaved(false);
  };

  const handleMetricChange = (type, value) => {
    if (type === 'sleep') setSleep(Number(value));
    if (type === 'stress') setStress(Number(value));
    setIsSaved(false);
  };

  const handleSave = () => {
    const key = selectedDate.toISOString().split('T')[0];
    const newEntries = {
      ...entries,
      [key]: { text: entryText, mood: selectedMood, sleep, stress, date: key }
    };
    setEntries(newEntries);
    localStorage.setItem('mlh_journal', JSON.stringify(newEntries));
    setIsSaved(true);
  };

  const handlePrevMonth = () => {
    if (currentMonth === 0) {
      setCurrentMonth(11);
      setCurrentYear(currentYear - 1);
    } else {
      setCurrentMonth(currentMonth - 1);
    }
  };

  const handleNextMonth = () => {
    if (currentMonth === 11) {
      setCurrentMonth(0);
      setCurrentYear(currentYear + 1);
    } else {
      setCurrentMonth(currentMonth + 1);
    }
  };

  // Check if selected date is in the future relative to *today* (discarding time)
  const isFutureDate = (date) => {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    return date > today;
  };

  const isSelectedDateFuture = isFutureDate(selectedDate);

  const renderCalendarDays = () => {
    const totalDays = daysInMonth(currentMonth, currentYear);
    const startDay = firstDayOfMonth(currentMonth, currentYear);
    const days = [];

    // Empty cells for padding
    for (let i = 0; i < startDay; i++) {
      days.push(<div key={`empty-${i}`} />);
    }

    // Days
    for (let d = 1; d <= totalDays; d++) {
      const date = new Date(currentYear, currentMonth, d);
      const key = date.toISOString().split('T')[0];
      const isSelected = selectedDate.toISOString().split('T')[0] === key;
      const hasEntry = !!entries[key];
      const isFuture = isFutureDate(date);

      days.push(
        <DayCell
          key={d}
          $isSelected={isSelected}
          $hasEntry={hasEntry}
          onClick={() => !isFuture && setSelectedDate(date)}
          style={{ opacity: isFuture ? 0.3 : 1, cursor: isFuture ? 'not-allowed' : 'pointer' }}
        >
          {d}
        </DayCell>
      );
    }
    return days;
  };

  const monthNames = ["January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
  ];

  const moods = [
    { emoji: '😊', label: 'Great' },
    { emoji: '😐', label: 'Okay' },
    { emoji: '😔', label: 'Low' },
    { emoji: '😰', label: 'Anxious' },
    { emoji: '☁️', label: 'Dreamy' },
  ];

  return (
    <PageContainer>
      <Header>
        <IconButton onClick={() => navigate('/dashboard')}>
          <ArrowLeft size={24} />
        </IconButton>
        <HeaderTitle>Daily Journal</HeaderTitle>
        <IconButton>
          <MoreVertical size={24} />
        </IconButton>
      </Header>

      <ContentLayout>
        <Sidebar>
          <CalendarCard>
            <CalendarHeader>
              <IconButton onClick={handlePrevMonth}><ChevronLeft size={18} /></IconButton>
              <h3>{monthNames[currentMonth]} {currentYear}</h3>
              <IconButton onClick={handleNextMonth}><ChevronRight size={18} /></IconButton>
            </CalendarHeader>
            <WeekDays>
              <span>S</span><span>M</span><span>T</span><span>W</span><span>T</span><span>F</span><span>S</span>
            </WeekDays>
            <DaysGrid>
              {renderCalendarDays()}
            </DaysGrid>
          </CalendarCard>

          <div style={{ padding: '0 0.5rem' }}>
            <h4 style={{ color: '#64748B', marginBottom: '1rem', fontSize: '0.9rem', textTransform: 'uppercase', letterSpacing: '1px' }}>Recent Entries</h4>
            <EntryList>
              {Object.values(entries)
                .sort((a, b) => new Date(b.date) - new Date(a.date))
                .slice(0, 3)
                .map((entry, i) => (
                  <EntryCard key={i} onClick={() => setSelectedDate(new Date(entry.date))}>
                    <EntryDate>{new Date(entry.date).toLocaleDateString(undefined, { weekday: 'long', month: 'short', day: 'numeric' })}</EntryDate>
                    <EntryPreview>{entry.mood?.emoji} {entry.text || "No text..."}</EntryPreview>
                  </EntryCard>
                ))}
              {Object.keys(entries).length === 0 && <p style={{ color: '#94A3B8', fontStyle: 'italic', fontSize: '0.9rem' }}>No entries safely stored yet.</p>}
            </EntryList>
          </div>
        </Sidebar>

        <MainContent>
          <DateHeader>
            <motion.div
              key={selectedDate.toISOString()}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
            >
              <h1>{selectedDate.toLocaleDateString(undefined, { weekday: 'long', month: 'long', day: 'numeric' })}</h1>
              <p>{isSelectedDateFuture ? "You cannot journal for the future." : "Take a deep breath. Write it out."}</p>
            </motion.div>
          </DateHeader>

          {isSelectedDateFuture ? (
            <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#94A3B8', fontStyle: 'italic' }}>
              Come back on this day to write your entry.
            </div>
          ) : (
            <>
              <MoodSelector>
                {moods.map((m, i) => (
                  <MoodBtn
                    key={i}
                    $selected={selectedMood?.label === m.label}
                    onClick={() => handleMoodChange(m)}
                  >
                    {m.emoji} <span>{m.label}</span>
                  </MoodBtn>
                ))}
              </MoodSelector>

              <MetricsGrid>
                <MetricCard>
                  <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <Moon size={16} /> Sleep Duration
                  </label>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '0.5rem' }}>
                    <IconButton onClick={() => handleMetricChange('sleep', Math.max(0, sleep - 0.5))} style={{ background: '#E2E8F0' }}>-</IconButton>
                    <span style={{ fontSize: '1.2rem', fontWeight: '600', color: '#2D3E50' }}>{sleep} <span style={{ fontSize: '0.8rem', fontWeight: '400', color: '#64748B' }}>hrs</span></span>
                    <IconButton onClick={() => handleMetricChange('sleep', Math.min(14, sleep + 0.5))} style={{ background: '#E2E8F0' }}>+</IconButton>
                  </div>
                </MetricCard>

                <MetricCard>
                  <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <Activity size={16} /> Stress Level
                  </label>
                  <div style={{ display: 'flex', gap: '0.25rem', marginTop: '0.5rem' }}>
                    {[1, 2, 3, 4, 5].map(lvl => (
                      <button
                        key={lvl}
                        onClick={() => handleMetricChange('stress', lvl)}
                        style={{
                          flex: 1,
                          height: '36px',
                          border: 'none',
                          borderRadius: '8px',
                          cursor: 'pointer',
                          background: stress === lvl ?
                            (lvl <= 2 ? '#86EFAC' : lvl === 3 ? '#FDE047' : '#FCA5A5')
                            : '#F1F5F9',
                          fontWeight: stress === lvl ? 'bold' : 'normal',
                          color: stress === lvl ? '#1F2937' : '#94A3B8',
                          transition: 'all 0.2s'
                        }}
                      >
                        {lvl}
                      </button>
                    ))}
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', color: '#94A3B8', marginTop: '0.25rem' }}>
                    <span>Calm</span>
                    <span>Stressed</span>
                  </div>
                </MetricCard>
              </MetricsGrid>

              <EditorArea
                placeholder="What's on your mind today?..."
                value={entryText}
                onChange={handleTextChange}
              />

              <SaveButton
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={handleSave}
                disabled={!entryText.trim() || isSaved}
                style={{ background: isSaved ? '#D1FAE5' : 'var(--accent-sky)', color: isSaved ? '#065F46' : '#1F3846' }}
              >
                {isSaved ? <Check size={18} /> : <Save size={18} />}
                {isSaved ? 'Saved' : 'Save Entry'}
              </SaveButton>
            </>
          )}
        </MainContent>
      </ContentLayout>
    </PageContainer >
  );
}
