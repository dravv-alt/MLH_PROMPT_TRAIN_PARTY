import React, { useState } from 'react';
import styled from 'styled-components';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowLeft, BookOpen, Video, Headphones, ExternalLink, Search, Tag } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

// --- Configuration ---
const resources = [
  {
    id: 1,
    title: "Understanding Anxiety",
    type: "article",
    category: "Anxiety",
    desc: "A comprehensive guide to understanding the symptoms and triggers of anxiety.",
    link: "https://www.mind.org.uk/information-support/types-of-mental-health-problems/anxiety-and-panic-attacks/about-anxiety/",
    color: "#FCA5A5" // Red-ish
  },
  {
    id: 2,
    title: "5-Minute Meditation for Stress",
    type: "video",
    category: "Mindfulness",
    desc: "A quick guided meditation to help you reset and lower stress levels immediately.",
    link: "https://www.youtube.com/watch?v=ssss7V1_eyA",
    color: "#86EFAC" // Green-ish
  },
  {
    id: 3,
    title: "Sleep Hygiene 101",
    type: "article",
    category: "Sleep",
    desc: "Practical tips to improve your sleep quality and establish a healthy bedtime routine.",
    link: "https://www.sleepfoundation.org/sleep-hygiene",
    color: "#93C5FD" // Blue-ish
  },
  {
    id: 4,
    title: "Box Breathing Technique",
    type: "exercise",
    category: "Anxiety",
    desc: "A simple but powerful breathing technique to regain control during panic.",
    link: "#",
    internal: "/breathe",
    color: "#FDBA74" // Orange-ish
  },
  {
    id: 5,
    title: "Dealing with Burnout",
    type: "article",
    category: "Work",
    desc: "How to recognize the signs of burnout and steps to recover from it.",
    link: "https://hbr.org/2016/11/beating-burnout",
    color: "#C4B5FD" // Purple-ish
  },
  {
    id: 6,
    title: "The Science of Gratitude",
    type: "video",
    category: "Depression",
    desc: "How practicing gratitude can physically change your brain and improve happiness.",
    link: "https://www.youtube.com/watch?v=JMd1CcGZYwU",
    color: "#FCD34D" // Yellow-ish
  }
];

const categories = ["All", "Anxiety", "Depression", "Mindfulness", "Sleep", "Work"];

// --- Styled Components ---

const PageContainer = styled.div`
  min-height: 100vh;
  background: var(--bg-warm);
  padding: 2rem;
  display: flex;
  flex-direction: column;
  align-items: center;
`;

const Header = styled.div`
  width: 100%;
  max-width: 1000px;
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 2rem;
  
  button {
    background: white;
    border: 1px solid var(--ui-border);
    padding: 0.5rem;
    border-radius: 50%;
    cursor: pointer;
    color: #64748B;
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

const ContentArea = styled.div`
  width: 100%;
  max-width: 1000px;
`;

const TitleSection = styled.div`
  margin-bottom: 2rem;
  h1 {
    font-size: 2.5rem;
    color: var(--text-primary);
    display: flex;
    align-items: center;
    gap: 1rem;
    margin-bottom: 0.5rem;
  }
  p {
    color: #64748B;
    font-size: 1.1rem;
  }
`;

const SearchBar = styled.div`
  background: var(--bg-card);
  border-radius: 16px;
  padding: 1rem;
  display: flex;
  align-items: center;
  gap: 1rem;
  box-shadow: 0 4px 20px rgba(0,0,0,0.02);
  border: 1px solid var(--ui-border);
  margin-bottom: 2rem;

  input {
    border: none;
    outline: none;
    font-size: 1.1rem;
    width: 100%;
    background: transparent;
    color: var(--text-primary);
    
    &::placeholder { color: var(--text-secondary); }
  }
`;

const CategoryPills = styled.div`
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
  margin-bottom: 2rem;
`;

const CategoryBtn = styled.button`
  padding: 0.5rem 1.25rem;
  border-radius: 20px;
  border: 1px solid ${props => props.$active ? 'transparent' : '#E2E8F0'};
  background: ${props => props.$active ? 'var(--accent-sky)' : 'white'};
  color: ${props => props.$active ? '#1F3846' : '#64748B'};
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  
  &:hover {
    background: ${props => props.$active ? 'var(--accent-sky)' : '#F8FAFC'};
  }
`;

const Grid = styled(motion.div)`
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1.5rem;
`;

const Card = styled(motion.a)`
  background: var(--bg-card);
  border-radius: 20px;
  padding: 1.5rem;
  border: 1px solid var(--ui-border);
  box-shadow: 0 4px 6px rgba(0,0,0,0.01);
  text-decoration: none;
  color: inherit;
  transition: all 0.2s;
  display: flex;
  flex-direction: column;
  height: 100%;
  cursor: pointer;
  
  &:hover {
    transform: translateY(-5px);
    box-shadow: 0 10px 20px rgba(0,0,0,0.05);
    border-color: #CBD5E1;
  }
`;

const Badge = styled.span`
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.25rem 0.75rem;
  border-radius: 8px;
  font-size: 0.8rem;
  font-weight: 600;
  margin-bottom: 1rem;
  width: fit-content;
`;

const CardTitle = styled.h3`
  font-size: 1.2rem;
  margin: 0 0 0.5rem 0;
  color: var(--text-primary);
`;

const CardDesc = styled.p`
  color: var(--text-secondary);
  font-size: 0.95rem;
  line-height: 1.5;
  margin-bottom: 1.5rem;
  flex: 1;
`;

const LinkText = styled.div`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 600;
  font-size: 0.9rem;
  color: #5D7B89;
`;

// --- Component ---

export default function Resources() {
  const navigate = useNavigate();
  const [search, setSearch] = useState('');
  const [activeCat, setActiveCat] = useState('All');

  const filtered = resources.filter(r => {
    const matchesSearch = r.title.toLowerCase().includes(search.toLowerCase()) || r.desc.toLowerCase().includes(search.toLowerCase());
    const matchesCat = activeCat === 'All' || r.category === activeCat;
    return matchesSearch && matchesCat;
  });

  const getTypeIcon = (type) => {
    if (type === 'video') return <Video size={14} />;
    if (type === 'exercise') return <Headphones size={14} />;
    return <BookOpen size={14} />;
  };

  return (
    <PageContainer>
      <Header>
        <button onClick={() => navigate('/dashboard')}>
          <ArrowLeft size={24} />
        </button>
        <span style={{ fontWeight: 600, color: '#2D3E50' }}>Dashboard</span>
      </Header>

      <ContentArea>
        <TitleSection>
          <h1><BookOpen size={32} /> Learning Hub</h1>
          <p>Curated resources to support your mental wellness journey.</p>
        </TitleSection>

        <SearchBar>
          <Search size={20} color="#94A3B8" />
          <input
            type="text"
            placeholder="Search for articles, topics, or videos..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </SearchBar>

        <CategoryPills>
          {categories.map(cat => (
            <CategoryBtn
              key={cat}
              $active={activeCat === cat}
              onClick={() => setActiveCat(cat)}
            >
              {cat}
            </CategoryBtn>
          ))}
        </CategoryPills>

        <Grid layout>
          <AnimatePresence>
            {filtered.map(r => (
              <Card
                key={r.id}
                href={r.internal ? undefined : r.link}
                onClick={(e) => {
                  if (r.internal) {
                    e.preventDefault();
                    navigate(r.internal);
                  }
                }}
                target={r.internal ? undefined : "_blank"}
                layout
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.9 }}
              >
                <Badge style={{ background: `${r.color}20`, color: r.color }}>
                  {getTypeIcon(r.type)} {r.type.charAt(0).toUpperCase() + r.type.slice(1)}
                </Badge>
                <CardTitle>{r.title}</CardTitle>
                <CardDesc>{r.desc}</CardDesc>
                <LinkText>
                  {r.internal ? 'Open Feature' : 'Read More'} <ExternalLink size={16} />
                </LinkText>
              </Card>
            ))}
          </AnimatePresence>
        </Grid>
      </ContentArea>
    </PageContainer>
  );
}
