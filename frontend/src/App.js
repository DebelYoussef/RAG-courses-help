import { useState, useRef, useEffect } from "react";

const API = "http://127.0.0.1:8000";

export default function App() {
  const [messages, setMessages]   = useState([]);
  const [question, setQuestion]   = useState("");
  const [loading, setLoading]     = useState(false);
  const [status, setStatus]       = useState({ ready: false, loaded_files: [] });
  const [uploading, setUploading] = useState(false);
  const bottomRef = useRef(null);

  // Check backend status on mount
  useEffect(() => {
    fetch(`${API}/status`)
      .then((r) => r.json())
      .then(setStatus)
      .catch(() => {});
  }, []);

  // Auto-scroll to bottom
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // ── Upload PDFs ──────────────────────────────────────────────────────────
  async function handleUpload(e) {
    const files = Array.from(e.target.files);
    if (!files.length) return;

    const formData = new FormData();
    files.forEach((f) => formData.append("files", f));

    setUploading(true);
    try {
      const res  = await fetch(`${API}/upload`, { method: "POST", body: formData });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail);
      setStatus({ ready: true, loaded_files: data.files });
      addMessage("system", `✅ ${data.message} (${data.chunks} chunks créés)`);
    } catch (err) {
      addMessage("system", `❌ Upload échoué: ${err.message}`);
    } finally {
      setUploading(false);
      e.target.value = "";
    }
  }

  // ── Send question ────────────────────────────────────────────────────────
  async function handleSend() {
    const q = question.trim();
    if (!q || loading) return;

    addMessage("user", q);
    setQuestion("");
    setLoading(true);

    try {
      const res  = await fetch(`${API}/chat`, {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify({ question: q }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail);
      addMessage("assistant", data.answer, data.sources);
    } catch (err) {
      addMessage("assistant", `❌ Erreur: ${err.message}`);
    } finally {
      setLoading(false);
    }
  }

  function addMessage(role, text, sources = []) {
    setMessages((prev) => [...prev, { role, text, sources, id: Date.now() }]);
  }

  function handleKey(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  // ── Render ───────────────────────────────────────────────────────────────
  return (
    <div style={styles.app}>

      {/* Header */}
      <div style={styles.header}>
        <h2 style={{ margin: 0, fontSize: 18 }}>📄 RAG PDF Assistant</h2>
        <span style={styles.badge(status.ready)}>
          {status.ready
            ? `✅ ${status.loaded_files.length} PDF(s) chargé(s)`
            : "⚠️ Aucun PDF indexé"}
        </span>
      </div>

      {/* Upload bar */}
      <div style={styles.uploadBar}>
        <label style={styles.uploadBtn}>
          {uploading ? "⏳ Indexation en cours..." : "📂 Charger des PDFs"}
          <input
            type="file"
            accept=".pdf"
            multiple
            hidden
            onChange={handleUpload}
            disabled={uploading}
          />
        </label>
        {status.loaded_files.length > 0 && (
          <span style={styles.fileList}>
            📎 {status.loaded_files.join(" · ")}
          </span>
        )}
      </div>

      {/* Chat messages */}
      <div style={styles.chat}>
        {messages.length === 0 && (
          <div style={styles.empty}>
            <p>👆 Chargez un PDF puis posez votre question</p>
            <p style={{ fontSize: 13, marginTop: 8, color: "#94a3b8" }}>
              Backend: {API}
            </p>
          </div>
        )}

        {messages.map((msg) => (
          <div key={msg.id} style={styles.bubbleWrapper(msg.role)}>
            <div style={styles.bubble(msg.role)}>
              <div style={styles.roleLabel(msg.role)}>
                {msg.role === "user" && "🧑 Vous"}
                {msg.role === "assistant" && "🤖 Assistant"}
                {msg.role === "system" && "⚙️ Système"}
              </div>
              <p style={{ margin: "6px 0 0", whiteSpace: "pre-wrap", lineHeight: 1.6 }}>
                {msg.text}
              </p>
              {msg.sources?.length > 0 && (
                <div style={styles.sources}>
                  📄 {msg.sources.join(" · ")}
                </div>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div style={styles.bubbleWrapper("assistant")}>
            <div style={styles.bubble("assistant")}>
              <div style={styles.roleLabel("assistant")}>🤖 Assistant</div>
              <p style={{ margin: "6px 0 0", color: "#94a3b8" }}>
                ⏳ Génération en cours...
              </p>
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div style={styles.inputRow}>
        <textarea
          style={styles.textarea}
          rows={2}
          placeholder="Posez votre question... (Entrée pour envoyer)"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={handleKey}
          disabled={loading}
        />
        <button
          style={styles.sendBtn(loading || !question.trim())}
          onClick={handleSend}
          disabled={loading || !question.trim()}
        >
          Envoyer
        </button>
      </div>
    </div>
  );
}

// ── Styles ────────────────────────────────────────────────────────────────────
const styles = {
  app: {
    display: "flex",
    flexDirection: "column",
    height: "100vh",
    maxWidth: 800,
    margin: "0 auto",
    fontFamily: "'Segoe UI', system-ui, sans-serif",
    background: "#f8fafc",
  },
  header: {
    background: "#1e293b",
    color: "#fff",
    padding: "14px 20px",
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    flexShrink: 0,
  },
  badge: (ready) => ({
    background: ready ? "#166534" : "#92400e",
    color: "#fff",
    padding: "4px 14px",
    borderRadius: 20,
    fontSize: 13,
    fontWeight: 500,
  }),
  uploadBar: {
    background: "#fff",
    borderBottom: "1px solid #e2e8f0",
    padding: "10px 20px",
    display: "flex",
    alignItems: "center",
    gap: 12,
    flexShrink: 0,
  },
  uploadBtn: {
    background: "#3b82f6",
    color: "#fff",
    padding: "7px 16px",
    borderRadius: 8,
    cursor: "pointer",
    fontSize: 14,
    fontWeight: 500,
    whiteSpace: "nowrap",
    userSelect: "none",
  },
  fileList: {
    color: "#64748b",
    fontSize: 13,
    overflow: "hidden",
    textOverflow: "ellipsis",
    whiteSpace: "nowrap",
  },
  chat: {
    flex: 1,
    overflowY: "auto",
    padding: "20px",
    display: "flex",
    flexDirection: "column",
    gap: 12,
  },
  empty: {
    textAlign: "center",
    color: "#64748b",
    marginTop: 80,
    fontSize: 16,
  },
  bubbleWrapper: (role) => ({
    display: "flex",
    justifyContent: role === "user" ? "flex-end" : "flex-start",
  }),
  bubble: (role) => ({
    background:
      role === "user"
        ? "#dbeafe"
        : role === "system"
        ? "#fef9c3"
        : "#ffffff",
    maxWidth: "80%",
    padding: "12px 16px",
    borderRadius: role === "user" ? "18px 18px 4px 18px" : "18px 18px 18px 4px",
    boxShadow: "0 1px 4px rgba(0,0,0,0.08)",
    border: "1px solid",
    borderColor:
      role === "user" ? "#bfdbfe" : role === "system" ? "#fde68a" : "#e2e8f0",
  }),
  roleLabel: (role) => ({
    fontSize: 12,
    fontWeight: 600,
    color:
      role === "user"
        ? "#1d4ed8"
        : role === "system"
        ? "#92400e"
        : "#059669",
  }),
  sources: {
    marginTop: 10,
    fontSize: 12,
    color: "#64748b",
    borderTop: "1px solid #e2e8f0",
    paddingTop: 8,
    lineHeight: 1.5,
  },
  inputRow: {
    display: "flex",
    gap: 10,
    padding: "12px 20px",
    background: "#fff",
    borderTop: "1px solid #e2e8f0",
    flexShrink: 0,
  },
  textarea: {
    flex: 1,
    padding: "10px 14px",
    borderRadius: 10,
    border: "1px solid #cbd5e1",
    fontSize: 14,
    resize: "none",
    fontFamily: "inherit",
    outline: "none",
    lineHeight: 1.5,
  },
  sendBtn: (disabled) => ({
    background: disabled ? "#e2e8f0" : "#1e293b",
    color: disabled ? "#94a3b8" : "#fff",
    border: "none",
    borderRadius: 10,
    padding: "0 22px",
    cursor: disabled ? "not-allowed" : "pointer",
    fontWeight: 600,
    fontSize: 14,
    transition: "all 0.2s",
  }),
};