import { BrowserRouter, Routes, Route } from 'react-router-dom';
import './App.css';
import Clinical from './pages/Clinical';
import Finance from './pages/Finance';
import AIDev from './pages/AIDev';
import Fashion from './pages/Fashion';
import Dashboard from './pages/Dashboard';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/clinical" element={<Clinical />} />
        <Route path="/finance" element={<Finance />} />
        <Route path="/ai-dev" element={<AIDev />} />
        <Route path="/fashion" element={<Fashion />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
