import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { motion } from 'framer-motion';
import { ArrowLeft, TrendingUp, Moon, Activity, Calendar as CalendarIcon, Wind, Heart } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import {
    LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
    AreaChart, Area
} from 'recharts';

// --- Styled Components ---

const PageContainer = styled.div`
  min-height: 100vh;
  background: var(--bg-warm);
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
  gap: 1rem;
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
  
  &:hover {
    background: var(--bg-sage);
    color: #2D3E50;
  }
`;

const ContentLayout = styled.div`
  max-width: 1000px;
  margin: 0 auto;
  width: 100%;
  padding: 2rem;
  display: grid;
  grid-template-columns: 1fr;
  gap: 2rem;
  padding-bottom: 4rem;
`;

const SectionTitle = styled.h3`
  font-size: 1.2rem;
  color: #2D3E50;
  margin-bottom: 1rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
`;

const Card = styled(motion.div)`
  background: white;
  border-radius: 24px;
  padding: 1.5rem;
  box-shadow: 0 4px 20px rgba(0,0,0,0.02);
  border: 1px solid var(--ui-border);
`;

const ChartContainer = styled.div`
  height: 300px;
  width: 100%;
  margin-top: 1rem;
`;

const StatGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 1rem;
`;

const StatCard = styled.div`
  background: ${props => props.$bg || '#F8FAFC'};
  padding: 1.2rem;
  border-radius: 16px;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;

  h4 {
    margin: 0;
    font-size: 0.9rem;
    color: #64748B;
    font-weight: 500;
  }
  
  p {
    margin: 0;
    font-size: 1.5rem;
    font-weight: 700;
    color: #2D3E50;
  }
`;

// Helper: Mood Maps
const moodValueMap = { 'Great': 5, 'Okay': 3, 'Dreamy': 3, 'Low': 2, 'Anxious': 1 };
const reverseMoodMap = { 5: 'Great', 4: 'Good', 3: 'Okay', 2: 'Low', 1: 'Anxious' };

export default function Insights() {
    const navigate = useNavigate();
    const [moodData, setMoodData] = useState([]);
    const [stats, setStats] = useState({ totalEntries: 0, avgMood: 'N/A', currentStreak: 0 });
    const [breathStats, setBreathStats] = useState({ totalSessions: 0, totalCycles: 0, topMood: 'N/A' });
    const [timeRange, setTimeRange] = useState('month'); // 'week', 'month', 'year'

    useEffect(() => {
        // Load Data
        const journalData = JSON.parse(localStorage.getItem('mlh_journal') || '{}');
        const breatheData = JSON.parse(localStorage.getItem('mlh_breathe_stats') || '[]');
        const entries = Object.values(journalData);

        let processedData = [];

        if (timeRange === 'week' || timeRange === 'month') {
            const days = timeRange === 'week' ? 7 : 30;
            // Generate dates
            const dateKeys = Array.from({ length: days }, (_, i) => {
                const d = new Date();
                d.setDate(d.getDate() - ((days - 1) - i));
                return d.toISOString().split('T')[0];
            });

            processedData = dateKeys.map(dateKey => {
                const entry = journalData[dateKey];
                return {
                    date: new Date(dateKey).toLocaleDateString(undefined, { month: 'short', day: 'numeric' }),
                    fullDate: dateKey,
                    value: entry?.mood ? (moodValueMap[entry.mood.label] || null) : null,
                    sleep: entry?.sleep ? Number(entry.sleep) : null,
                    stress: entry?.stress ? Number(entry.stress) : null,
                    label: entry?.mood?.label
                };
            });
        } else if (timeRange === 'year') {
            // Aggregate by month for the last 12 months
            const months = Array.from({ length: 12 }, (_, i) => {
                const d = new Date();
                d.setMonth(d.getMonth() - ((11) - i));
                return {
                    month: d.getMonth(),
                    year: d.getFullYear(),
                    label: d.toLocaleDateString(undefined, { month: 'short' })
                };
            });

            processedData = months.map(({ month, year, label }) => {
                // Find entries for this month
                const monthEntries = entries.filter(e => {
                    const d = new Date(e.date);
                    return d.getMonth() === month && d.getFullYear() === year;
                });

                // Calculate avgs
                const avgVal = (arr, keyFn) => {
                    const valid = arr.map(keyFn).filter(v => v !== null && v !== undefined);
                    if (!valid.length) return null;
                    return valid.reduce((a, b) => a + b, 0) / valid.length;
                };

                const avgMood = avgVal(monthEntries, e => e.mood ? moodValueMap[e.mood.label] : null);
                const avgSleep = avgVal(monthEntries, e => e.sleep ? Number(e.sleep) : null);
                const avgStress = avgVal(monthEntries, e => e.stress ? Number(e.stress) : null);

                return {
                    date: label,
                    fullDate: `${year}-${month + 1}`,
                    value: avgMood ? Number(avgMood.toFixed(1)) : null,
                    sleep: avgSleep ? Number(avgSleep.toFixed(1)) : null,
                    stress: avgStress ? Number(avgStress.toFixed(1)) : null,
                    label: reverseMoodMap[Math.round(avgMood)] // approx label
                };
            });
        }

        setMoodData(processedData);

        // Calculate Journal Stats (Overall, not just range dependent? Or range dependent? Usually overall stats like 'Total Entries' define the whole journey, but let's keep it consistent)
        // Let's keep stats based on ALL TIME entries for "Total Logged" to show progress, but "Avg Mood" could be for the view.
        // User asked to "understand progress", so filtered stats might be better. 
        // Actually, let's keep "Total Entries" as All Time, but maybe Avg Mood for the view.

        const filledOverall = entries.filter(e => e.mood || e.sleep || e.stress);
        if (filledOverall.length > 0) {
            const validMoods = filledOverall.filter(e => e.mood);
            const totalMood = validMoods.reduce((acc, curr) => acc + (moodValueMap[curr.mood.label] || 0), 0);
            const avg = validMoods.length ? Math.round(totalMood / validMoods.length) : 0;

            // Streak Calculation
            const sortedDates = filledOverall.map(e => e.date).sort();
            let streak = 0;
            if (sortedDates.length > 0) {
                const today = new Date();
                const todayStr = today.toISOString().split('T')[0];
                const yesterday = new Date(today);
                yesterday.setDate(today.getDate() - 1);
                const yesterdayStr = yesterday.toISOString().split('T')[0];

                // Check if last entry is today or yesterday
                const lastEntry = sortedDates[sortedDates.length - 1];
                if (lastEntry === todayStr || lastEntry === yesterdayStr) {
                    streak = 1;
                    for (let i = sortedDates.length - 2; i >= 0; i--) {
                        const curr = new Date(sortedDates[i]);
                        const next = new Date(sortedDates[i + 1]);
                        const diff = (next - curr) / (1000 * 60 * 60 * 24);
                        if (diff === 1) streak++;
                        else if (diff > 1) break;
                    }
                }
            }

            setStats(prev => ({ ...prev, totalEntries: filledOverall.length, avgMood: reverseMoodMap[avg] || 'Okay', currentStreak: streak }));
        }

        // Breathing stats (All time)
        if (breatheData.length > 0 && breathStats.totalSessions === 0) {
            const totalCyc = breatheData.reduce((acc, curr) => acc + curr.cycles, 0);
            const moodCounts = {};
            breatheData.forEach(s => { if (s.moodAfter) moodCounts[s.moodAfter] = (moodCounts[s.moodAfter] || 0) + 1; });
            const topMood = Object.entries(moodCounts).sort((a, b) => b[1] - a[1])[0]?.[0] || 'N/A';
            setBreathStats({ totalSessions: breatheData.length, totalCycles: totalCyc, topMood });
        }

    }, [timeRange]); // Dependency on timeRange

    return (
        <PageContainer>
            <Header>
                <IconButton onClick={() => navigate('/dashboard')}>
                    <ArrowLeft size={24} />
                </IconButton>
                <HeaderTitle>My Journey</HeaderTitle>
            </Header>

            <ContentLayout>

                {/* 1. At a Glance Stats */}
                <section>
                    <StatGrid>
                        <StatCard $bg="#EEF2FF">
                            <h4>Entries Logged</h4>
                            <p>{stats.totalEntries}</p>
                        </StatCard>
                        <StatCard $bg="#F0FDF4">
                            <h4>Average Mood</h4>
                            <p>{stats.avgMood}</p>
                        </StatCard>
                        <StatCard $bg="#FFF7ED">
                            <h4>Consistency</h4>
                            <p>{stats.currentStreak} Day Streak</p>
                        </StatCard>
                    </StatGrid>
                </section>

                {/* Consistency Heatmap */}
                <section style={{ marginBottom: '2rem' }}>
                    <SectionTitle><CalendarIcon size={20} /> Consistency Map (Last Year)</SectionTitle>
                    <Card>
                        <div style={{ overflowX: 'auto' }}>
                            <div style={{ display: 'flex', flexDirection: 'column', minWidth: 'max-content' }}>
                                {/* Month Labels */}
                                <div style={{ display: 'flex', marginLeft: '30px', marginBottom: '8px', fontSize: '0.75rem', color: '#64748B', height: '1.2rem' }}>
                                    {Array.from({ length: 52 }).map((_, weekIndex) => {
                                        const today = new Date();
                                        const startOfWeek = new Date(today);
                                        const daysFromToday = (51 - weekIndex) * 7 + today.getDay();
                                        startOfWeek.setDate(today.getDate() - daysFromToday);

                                        // Determine if we should show a label
                                        // Show if it's the first week of the month OR the very first column
                                        // But typically Github style is: check if this week's month != previous week's month
                                        // Since we are iterating, we can check date of Sunday (start) vs. Saturday (end) or just if it's ~1st

                                        const month = startOfWeek.toLocaleString('default', { month: 'short' });

                                        // Check previous week
                                        let showLabel = false;
                                        if (weekIndex === 0) {
                                            showLabel = true;
                                        } else {
                                            const prevWeek = new Date(startOfWeek);
                                            prevWeek.setDate(prevWeek.getDate() - 7);
                                            const prevMonth = prevWeek.toLocaleString('default', { month: 'short' });
                                            if (month !== prevMonth) showLabel = true;
                                        }

                                        // Adjust spacing - if we show label, it takes space, if not, empty
                                        // Actually, just render text in a cell of width 16px (12px box + 4px gap)
                                        return (
                                            <div key={weekIndex} style={{ width: '16px', overflow: 'visible' }}>
                                                {showLabel && <span>{month}</span>}
                                            </div>
                                        );
                                    })}
                                </div>

                                <div style={{ display: 'flex', gap: '4px' }}>
                                    {/* Week Day Labels (Left) */}
                                    <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', marginRight: '8px', fontSize: '0.7rem', color: '#94A3B8', paddingTop: '0' }}>
                                        {/* Matches grid row heights */}
                                        <div style={{ height: '12px' }}></div>
                                        <div style={{ height: '12px', lineHeight: '12px' }}>Mon</div>
                                        <div style={{ height: '12px' }}></div>
                                        <div style={{ height: '12px', lineHeight: '12px' }}>Wed</div>
                                        <div style={{ height: '12px' }}></div>
                                        <div style={{ height: '12px', lineHeight: '12px' }}>Fri</div>
                                        <div style={{ height: '12px' }}></div>
                                    </div>

                                    {Array.from({ length: 52 }).map((_, weekIndex) => {
                                        // Generate last 52 weeks
                                        const today = new Date();
                                        const startOfWeek = new Date(today);
                                        const daysFromToday = (51 - weekIndex) * 7 + today.getDay();
                                        startOfWeek.setDate(today.getDate() - daysFromToday);

                                        return (
                                            <div key={weekIndex} style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                                                {Array.from({ length: 7 }).map((_, dayIndex) => {
                                                    const d = new Date(startOfWeek);
                                                    d.setDate(d.getDate() + dayIndex);
                                                    const dateKey = d.toISOString().split('T')[0];
                                                    const entry = JSON.parse(localStorage.getItem('mlh_journal') || '{}')[dateKey];
                                                    const hasEntry = !!entry;

                                                    const isFuture = d > new Date();

                                                    return (
                                                        <div
                                                            key={dayIndex}
                                                            title={`${d.toLocaleDateString(undefined, { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}${hasEntry ? ' • Journaled' : ''}`}
                                                            style={{
                                                                width: '12px',
                                                                height: '12px',
                                                                borderRadius: '3px',
                                                                background: isFuture ? 'transparent' : (hasEntry ? '#10B981' : '#F1F5F9'),
                                                                border: isFuture ? '1px dashed #E2E8F0' : 'none',
                                                                cursor: isFuture ? 'default' : 'help'
                                                            }}
                                                        />
                                                    );
                                                })}
                                            </div>
                                        );
                                    })}
                                </div>
                            </div>
                        </div>
                        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center', marginTop: '1rem', fontSize: '0.85rem', color: '#64748B' }}>
                            <span>Less</span>
                            <div style={{ display: 'flex', gap: '4px' }}>
                                <div style={{ width: 12, height: 12, borderRadius: 3, background: '#F1F5F9' }} />
                                <div style={{ width: 12, height: 12, borderRadius: 3, background: '#10B981' }} />
                            </div>
                            <span>More</span>
                        </div>
                    </Card>
                </section>

                {/* 2. Mood Trends Chart */}
                <section>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
                        <SectionTitle style={{ marginBottom: 0 }}><TrendingUp size={20} /> Mood Trends</SectionTitle>
                        <div style={{ background: '#F1F5F9', padding: '4px', borderRadius: '12px', display: 'flex', gap: '4px' }}>
                            {['Week', 'Month', 'Year'].map(range => (
                                <button
                                    key={range}
                                    onClick={() => setTimeRange(range.toLowerCase())}
                                    style={{
                                        border: 'none',
                                        background: timeRange === range.toLowerCase() ? 'white' : 'transparent',
                                        color: timeRange === range.toLowerCase() ? '#1F3846' : '#64748B',
                                        padding: '0.4rem 1rem',
                                        borderRadius: '8px',
                                        fontSize: '0.85rem',
                                        fontWeight: 600,
                                        cursor: 'pointer',
                                        boxShadow: timeRange === range.toLowerCase() ? '0 1px 3px rgba(0,0,0,0.1)' : 'none',
                                        transition: 'all 0.2s'
                                    }}
                                >
                                    {range}
                                </button>
                            ))}
                        </div>
                    </div>
                    <Card
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                    >
                        <p style={{ fontSize: '0.9rem', color: '#64748B', marginBottom: '1rem' }}>
                            Your emotional heartbeat. See how your feelings ebb and flow over time.
                        </p>
                        <ChartContainer>
                            {/* ResponsiveContainer causing hook issues, using fixed dimensions temporarily or checking different import */}
                            <div style={{ width: '100%', height: '100%' }}>
                                <AreaChart width={800} height={300} data={moodData}>
                                    <defs>
                                        <linearGradient id="colorMood" x1="0" y1="0" x2="0" y2="1">
                                            <stop offset="5%" stopColor="#8BAEB8" stopOpacity={0.3} />
                                            <stop offset="95%" stopColor="#8BAEB8" stopOpacity={0} />
                                        </linearGradient>
                                    </defs>
                                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E2E8F0" />
                                    <XAxis
                                        dataKey="date"
                                        axisLine={false}
                                        tickLine={false}
                                        tick={{ fill: '#94A3B8', fontSize: 12 }}
                                        minTickGap={30}
                                    />
                                    <YAxis
                                        hide
                                        domain={[0, 6]}
                                    />
                                    <Tooltip
                                        contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}
                                        cursor={{ stroke: '#94A3B8', strokeWidth: 1, strokeDasharray: '3 3' }}
                                        formatter={(value) => [reverseMoodMap[value] || value, 'Mood']}
                                    />
                                    <Area
                                        type="monotone"
                                        dataKey="value"
                                        stroke="#5D7B89"
                                        strokeWidth={3}
                                        fillOpacity={1}
                                        fill="url(#colorMood)"
                                        connectNulls
                                    />
                                </AreaChart>
                            </div>
                        </ChartContainer>
                    </Card>
                </section>

                {/* 3. Sleep & Stress Integration */}
                <section>
                    <SectionTitle><Moon size={20} /> Sleep & Stress</SectionTitle>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem' }}>
                        <Card whileHover={{ y: -5 }}>
                            <h4 style={{ margin: '0 0 1rem 0', color: '#64748B' }}>Sleep Quality</h4>
                            <div style={{ height: '200px' }}>
                                <ResponsiveContainer width="100%" height="100%">
                                    <LineChart data={moodData}>
                                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E2E8F0" />
                                        <XAxis dataKey="date" hide />
                                        <Tooltip
                                            labelFormatter={(l) => ''}
                                            formatter={(value) => [`${value} hrs`, 'Sleep']}
                                            contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}
                                        />
                                        <Line type="monotone" dataKey="sleep" stroke="#6366F1" strokeWidth={3} dot={{ r: 4 }} connectNulls />
                                    </LineChart>
                                </ResponsiveContainer>
                            </div>
                        </Card>
                        <Card whileHover={{ y: -5 }}>
                            <h4 style={{ margin: '0 0 1rem 0', color: '#64748B' }}>Stress Levels</h4>
                            <div style={{ height: '200px' }}>
                                <ResponsiveContainer width="100%" height="100%">
                                    <LineChart data={moodData}>
                                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E2E8F0" />
                                        <XAxis dataKey="date" hide />
                                        <Tooltip
                                            labelFormatter={(l) => ''}
                                            formatter={(value) => [`${value}/5`, 'Stress']}
                                            contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}
                                        />
                                        <Line type="monotone" dataKey="stress" stroke="#F43F5E" strokeWidth={3} dot={{ r: 4 }} connectNulls />
                                    </LineChart>
                                </ResponsiveContainer>
                            </div>
                        </Card>
                    </div>
                </section>

                {/* 4. The Effect (Breathing Impact) */}
                <section>
                    <SectionTitle><Wind size={20} /> The Effect (Breathing)</SectionTitle>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem' }}>
                        <StatCard $bg="#F0F9FF">
                            <h4>Total Sessions</h4>
                            <p>{breathStats.totalSessions}</p>
                        </StatCard>
                        <StatCard $bg="#F0FDF4">
                            <h4>Cycles Breathed</h4>
                            <p>{breathStats.totalCycles}</p>
                        </StatCard>
                        <StatCard $bg="#FEF3C7">
                            <h4>After Breathing, I feel...</h4>
                            <p style={{ fontSize: '1.2rem' }}>{breathStats.topMood === 'N/A' ? '---' : breathStats.topMood}</p>
                        </StatCard>
                    </div>
                </section>

            </ContentLayout>
        </PageContainer>
    );
}
