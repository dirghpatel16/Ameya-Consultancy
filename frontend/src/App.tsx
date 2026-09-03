import { Routes, Route } from "react-router-dom";
import Home from "@/pages/Home";
import { PrivacyPage, TermsPage } from "@/pages/Legal";

// One <Route> per page in src/pages; BrowserRouter already wraps this in main.tsx.
export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/terms" element={<TermsPage />} />
      <Route path="/privacy" element={<PrivacyPage />} />
    </Routes>
  );
}
