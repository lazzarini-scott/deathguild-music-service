import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Home from './pages/Home';
import PlaylistPage from './pages/PlaylistPage';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/playlist/:date" element={<PlaylistPage />} />
      </Routes>
    </BrowserRouter>
  );
}
