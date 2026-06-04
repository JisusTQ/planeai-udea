import { useState } from "react";

import Chat from "./components/Chat.jsx";
import VistaCupos from "./components/VistaCupos.jsx";
import { IconChat, IconGrid } from "./components/icons.jsx";

export default function App() {
  const [vista, setVista] = useState("chat");

  return (
    <div className="shell">
      <aside className="side">
        <div className="brand">
          <div className="brand-mark">P</div>
          <div>
            <div className="brand-name">PlaneAI</div>
            <div className="brand-sub">Ingeniería · UdeA</div>
          </div>
        </div>

        <nav className="side-nav">
          <button
            className={`nav-btn ${vista === "chat" ? "on" : ""}`}
            onClick={() => setVista("chat")}
          >
            <IconChat width={19} height={19} />
            <span>Asistente</span>
          </button>
          <button
            className={`nav-btn ${vista === "cupos" ? "on" : ""}`}
            onClick={() => setVista("cupos")}
          >
            <IconGrid width={19} height={19} />
            <span>Cupos y horarios</span>
          </button>
        </nav>

        <div className="side-foot">
          <span className="live">
            <span className="live-dot" /> Datos en vivo
          </span>
          <span>Pensum y oferta tomados de los portales oficiales de la UdeA.</span>
        </div>
      </aside>

      <main className="main">
        {vista === "chat" ? <Chat /> : <VistaCupos />}
      </main>
    </div>
  );
}
