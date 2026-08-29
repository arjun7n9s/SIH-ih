import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { Chat } from "./pages/Chat";
import { Contradictions } from "./pages/Contradictions";
import { Landing } from "./pages/Landing";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/app" element={<Chat />} />
        <Route path="/contradictions" element={<Contradictions />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
