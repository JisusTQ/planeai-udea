import { useState } from "react";

import Chat from "./components/Chat.jsx";
import VistaCupos from "./components/VistaCupos.jsx";

// Componente raíz: cabecera + navegación por pestañas entre el Chat y la Vista de cupos.
export default function App() {
  const [vista, setVista] = useState("chat");

  return (
    <div className="app">
      <header className="header">
        <h1>
          🎓 PlaneAI <span>UdeA</span>
        </h1>
        <p>Asistente de planeación académica · Facultad de Ingeniería</p>
      </header>

      <nav className="tabs">
        <button
          className={vista === "chat" ? "tab activa" : "tab"}
          onClick={() => setVista("chat")}
        >
          💬 Chat
        </button>
        <button
          className={vista === "cupos" ? "tab activa" : "tab"}
          onClick={() => setVista("cupos")}
        >
          📋 Cupos
        </button>
      </nav>

      <main className="contenido">
        {vista === "chat" ? <Chat /> : <VistaCupos />}
      </main>

      <footer className="footer">PlaneAI UdeA · Proyecto académico</footer>
    </div>
  );
}
