import { BrowserRouter, Routes, Route, Navigate, NavLink } from "react-router-dom";
import { Mic, AudioWaveform, Library } from "lucide-react";
import ClonePage from "./pages/ClonePage";
import MyVoicesPage from "./pages/MyVoicesPage";
import RecordPage from "./pages/RecordPage";

const navItems = [
  { to: "/clone", label: "Voice Clone", icon: AudioWaveform },
  { to: "/my-voices", label: "My Voices", icon: Library },
  { to: "/record", label: "Record", icon: Mic },
];

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen flex flex-col">
        {/* Header */}
        <header className="border-b bg-card">
          <div className="max-w-7xl mx-auto px-4 h-14 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <AudioWaveform className="h-6 w-6 text-primary" />
              <span className="font-bold text-lg">VoiceClone</span>
            </div>

            <nav className="flex items-center gap-1">
              {navItems.map(({ to, label, icon: Icon }) => (
                <NavLink
                  key={to}
                  to={to}
                  className={({ isActive }) =>
                    `flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                      isActive
                        ? "bg-primary text-primary-foreground"
                        : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                    }`
                  }
                >
                  <Icon className="h-4 w-4" />
                  {label}
                </NavLink>
              ))}
            </nav>
          </div>
        </header>

        {/* Content */}
        <main className="flex-1">
          <Routes>
            <Route path="/" element={<Navigate to="/clone" replace />} />
            <Route path="/clone" element={<ClonePage />} />
            <Route path="/my-voices" element={<MyVoicesPage />} />
            <Route path="/record" element={<RecordPage />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;
