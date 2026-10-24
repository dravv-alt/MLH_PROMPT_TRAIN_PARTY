import {useEffect,useState} from 'react';
import {Routes,Route,Navigate,useLocation,Link,NavLink} from 'react-router-dom';
import {Show,UserButton} from '@clerk/react';
import ProtectedRoute from './components/ProtectedRoute';
import StoneCurtain from './components/StoneCurtain';
import LandingPage from './pages/LandingPage';
import AuthPage from './pages/AuthPage';
import ChatPage from './pages/ChatPage';
import AnalysisPage from './pages/AnalysisPage';
import MemoryPage from './pages/MemoryPage';
import SettingsPage from './pages/SettingsPage';
import JournalPage from './pages/JournalPage';
import SavedMomentsPage from './pages/SavedMomentsPage';
import InsightsPage from './pages/InsightsPage';
import CalmPage from './pages/CalmPage';
import SsoCallbackPage from './pages/SsoCallbackPage';

function Alias({to}){const {search}=useLocation();return <Navigate to={to+search} replace/>;}
function Account(){return <><Show when="signed-out"><Link to="/auth" className="ghost-btn">Sign in</Link></Show><Show when="signed-in"><UserButton/></Show></>;}
export default function IntegratedApp(){
  const [curtain,setCurtain]=useState(false);
  useEffect(()=>{function escape(e){if(e.key==='Escape')setCurtain(value=>!value);}window.addEventListener('keydown',escape);return()=>window.removeEventListener('keydown',escape);},[]);
  const guard = element => <ProtectedRoute>{element}</ProtectedRoute>;
  const links=[['Talk','/talk'],['How this was read','/how-this-was-read'],['Moments','/moments'],['Journal','/journal'],['Remembered','/remembered'],['Calm','/calm'],['Privacy','/privacy']];
  return <div className="app-shell"><StoneCurtain isOpen={curtain} onClose={()=>setCurtain(false)}/><header className="live-navigation"><div className="live-navigation-top"><Link to="/" className="live-brand">Sanctuary</Link><div className="button-row"><button className="ghost-btn" onClick={()=>setCurtain(value=>!value)}>Hide screen <kbd>Esc</kbd></button>{import.meta.env.VITE_CLERK_PUBLISHABLE_KEY?<Account/>:<Link to="/auth">Sign-in setup</Link>}</div></div><nav aria-label="Main navigation">{links.map(([name,path])=><NavLink key={path} to={path} className={({isActive})=>isActive?'active':''}>{name}</NavLink>)}</nav></header>
  <main className="integrated-content"><Routes>
    <Route path="/" element={<LandingPage/>}/><Route path="/auth/*" element={<AuthPage/>}/>
    <Route path="/sso-callback" element={import.meta.env.VITE_CLERK_PUBLISHABLE_KEY?<SsoCallbackPage/>:<Alias to="/auth"/>}/>
    <Route path="/talk" element={guard(<ChatPage/>)}/><Route path="/moments" element={guard(<SavedMomentsPage/>)}/>
    <Route path="/journal" element={guard(<JournalPage/>)}/><Route path="/remembered" element={guard(<MemoryPage/>)}/>
    <Route path="/how-this-was-read" element={guard(<AnalysisPage/>)}/><Route path="/privacy" element={guard(<SettingsPage/>)}/>
    <Route path="/insights" element={guard(<InsightsPage/>)}/><Route path="/calm" element={<CalmPage/>}/>
    <Route path="/chat" element={<Alias to="/talk"/>}/><Route path="/analysis" element={<Alias to="/how-this-was-read"/>}/>
    <Route path="/read" element={<Alias to="/how-this-was-read"/>}/><Route path="/memory" element={<Alias to="/remembered"/>}/>
    <Route path="/settings" element={<Alias to="/privacy"/>}/><Route path="/dashboard" element={<Alias to="/talk"/>}/>
    <Route path="*" element={<Navigate to="/" replace/>}/>
  </Routes></main></div>;
}
