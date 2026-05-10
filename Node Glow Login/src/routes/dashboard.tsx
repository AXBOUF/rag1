import { useState, useEffect } from "react";
import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { MessageSquare, User, Settings, Shield, Plus, Send, LogOut, Pin, FileText, X } from "lucide-react";
import { getUser, logout as apiLogout, getToken } from "@/lib/auth";
import { queryRag, getUsers, getStats, getLogs, uploadDocuments } from "@/lib/api";

export const Route = createFileRoute("/dashboard")({
  component: DashboardPage,
  head: () => ({
    meta: [
      { title: "Resource Center — Dashboard" },
      { name: "description", content: "Hungry Jacks internal resource center." },
    ],
  }),
});

type NavKey = "chat" | "profile" | "settings" | "admin";

type Source = { id: string; name: string; preview: string; filename: string };
type Message = { from: "user" | "bot"; text: string; sources?: Source[] };

const sampleSources: Source[] = [
  {
    id: "src-1",
    name: "evening_shift_roster_w42.pdf",
    filename: "evening_shift_roster_w42.pdf",
    preview:
      "EVENING SHIFT ROSTER — WEEK 42\n\nStore: Bondi Junction\nManager: R. Patel\n\nAvailability:\n• Jake Morrison — Mon/Tue/Thu — +61 4xx xxx xxx\n• Mia Tanaka — Wed/Thu/Fri — +61 4xx xxx xxx\n• Rupert Hale — Tue/Wed/Sat — +61 4xx xxx xxx\n\nNotes: All staff cleared for close-down duties. Refer to closing checklist v3 before sign-off.",
  },
  {
    id: "src-2",
    name: "staff_contact_directory.pdf",
    filename: "staff_contact_directory.pdf",
    preview:
      "STAFF CONTACT DIRECTORY (INTERNAL)\n\nFor rostering use only. Do not share externally.\n\n— Jake Morrison · Crew · jake.m@hj.local\n— Mia Tanaka · Crew · mia.t@hj.local\n— Rupert Hale · Shift Lead · rupert.h@hj.local",
  },
];

const initialMessages: Message[] = [
  {
    from: "user",
    text: "Ask me anything about your documents...",
  },
];

const chatHistory = [
  "Evening shift availability",
  "Closing checklist v3",
  "New hire onboarding",
  "Weekly waste report",
  "POS error 0x12",
  "Public holiday roster",
  "Stock reorder template",
];

function DashboardPage() {
  const navigate = useNavigate();
  const user = getUser();
  const role = user?.role || "employee";
  const username = user?.username || "User";

  useEffect(() => {
    if (!user) {
      navigate({ to: "/login" });
    }
  }, [user, navigate]);

  const [active, setActive] = useState<NavKey>("chat");
  const [messages, setMessages] = useState<Message[]>(initialMessages);
  const [draft, setDraft] = useState("");
  const [title, setTitle] = useState("Evening shift — availability");
  const [openSource, setOpenSource] = useState<Source | null>(null);
  const [queryLoading, setQueryLoading] = useState(false);

  const navItems: { key: NavKey; label: string; icon: typeof MessageSquare }[] = [
    { key: "chat", label: "Chat", icon: MessageSquare },
    { key: "profile", label: "Profile", icon: User },
    { key: "settings", label: "Settings", icon: Settings },
    ...(role === "admin"
      ? [{ key: "admin" as NavKey, label: "Admin", icon: Shield }]
      : []),
  ];

  const send = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!draft.trim() || queryLoading) return;

    const userQuery = draft;
    setMessages((m) => [...m, { from: "user", text: userQuery }]);
    setDraft("");
    setQueryLoading(true);

    try {
      const result = await queryRag(userQuery, 3);

      // Map metadatas to Source format
      const sources: Source[] = result.metadatas.map((meta, idx) => {
        // Use the relative path from metadata, or fallback to filename
        const filePath = (meta.path || meta.filename)
          .replace(/^.*test_data\//, "")  // Strip test_data prefix if present
          .replace(/^.*uploads\//, "");   // Strip uploads prefix if present

        return {
          id: `${meta.filename}__page_${meta.page}`,
          name: meta.filename,
          filename: filePath,
          preview: result.documents[idx] || "",
        };
      });

      setMessages((m) => [
        ...m,
        {
          from: "bot",
          text: result.response,
          sources: sources.length > 0 ? sources : undefined,
        },
      ]);
    } catch (err) {
      setMessages((m) => [
        ...m,
        {
          from: "bot",
          text: `Error: ${err instanceof Error ? err.message : "Failed to query"}`,
        },
      ]);
    } finally {
      setQueryLoading(false);
    }
  };

  const roleColor =
    role === "admin"
      ? "var(--hj-red)"
      : role === "manager"
        ? "var(--hj-green)"
        : "var(--hj-orange)";

  return (
    <main className="min-h-screen w-full" style={{ background: "var(--gradient-hero)" }}>
      {/* Top bar */}
      <header
        className="flex items-center justify-between px-6 lg:px-10 h-16 border-b-2"
        style={{ borderColor: "var(--hj-brown)" }}
      >
        <Link to="/dashboard" className="flex items-center gap-3">
          <div className="h-8 w-8 rounded-sm" style={{ background: "var(--hj-orange)" }} />
          <div className="font-display uppercase text-sm leading-none">
            <span style={{ color: "var(--hj-orange)" }}>Hungry</span>{" "}
            <span style={{ color: "var(--hj-green)" }}>Jacks</span>
            <span className="block text-[10px] tracking-[0.3em] mt-1" style={{ color: "var(--hj-brown)" }}>
              Resource Center
            </span>
          </div>
        </Link>
        <div className="flex items-center gap-3">
          <span
            className="font-display uppercase text-[10px] tracking-widest px-3 py-1.5 rounded-full text-white"
            style={{ background: roleColor }}
          >
            {role}
          </span>
          <button
            onClick={() => {
              apiLogout();
              navigate({ to: "/login" });
            }}
            className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-widest hover:opacity-70"
            style={{ color: "var(--hj-brown)" }}
          >
            <LogOut className="h-3.5 w-3.5" /> Logout
          </button>
        </div>
      </header>

      <div className="grid grid-cols-[260px_1fr] gap-4 p-4 lg:p-6">
        {/* Sidebar */}
        <aside className="flex flex-col gap-4">
          {/* Nav card */}
          <div
            className="bg-card border-2 rounded-2xl p-3 flex flex-col gap-1.5"
            style={{ borderColor: "var(--hj-brown)" }}
          >
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = active === item.key;
              return (
                <button
                  key={item.key}
                  onClick={() => setActive(item.key)}
                  className="flex items-center gap-3 h-11 px-4 rounded-full text-left font-display uppercase text-[11px] tracking-widest border-2 transition-all"
                  style={{
                    borderColor: isActive ? roleColor : "transparent",
                    background: isActive ? roleColor : "transparent",
                    color: isActive ? "white" : "var(--hj-brown)",
                  }}
                >
                  <Icon className="h-4 w-4" />
                  {item.label}
                </button>
              );
            })}
          </div>

          {/* Chat history */}
          <div
            className="bg-card border-2 rounded-2xl p-3 flex-1 flex flex-col"
            style={{ borderColor: "var(--hj-brown)" }}
          >
            <div className="flex items-center justify-between mb-3 px-2">
              <span
                className="font-display uppercase text-[10px] tracking-widest"
                style={{ color: "var(--hj-brown)" }}
              >
                Chat history
              </span>
              <button
                className="h-6 w-6 rounded-full flex items-center justify-center text-white"
                style={{ background: "var(--hj-orange)" }}
                aria-label="New chat"
              >
                <Plus className="h-3.5 w-3.5" />
              </button>
            </div>
            <div className="flex flex-col gap-1 overflow-y-auto pr-1">
              {chatHistory.map((c, i) => (
                <button
                  key={i}
                  className="text-left text-xs px-3 py-2 rounded-lg hover:bg-muted transition-colors truncate"
                  style={{ color: "var(--hj-brown)" }}
                >
                  {c}
                </button>
              ))}
            </div>
          </div>
        </aside>

        {/* Main panel + optional source viewer */}
        <div
          className="grid gap-4 transition-all"
          style={{
            gridTemplateColumns: openSource ? "1fr 420px" : "1fr",
            height: "calc(100vh - 64px - 3rem)",
          }}
        >
        <section
          className="bg-card border-2 rounded-2xl flex flex-col overflow-hidden"
          style={{ borderColor: "var(--hj-brown)" }}
        >
          {active === "chat" && (
            <>
              {/* Chat header */}
              <div
                className="flex items-center justify-between px-6 h-14 border-b-2"
                style={{ borderColor: "var(--hj-brown)" }}
              >
                <input
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="font-display uppercase text-sm tracking-wider bg-transparent outline-none flex-1"
                  style={{ color: "var(--hj-brown)" }}
                />
                <button
                  className="h-8 w-8 rounded-full flex items-center justify-center"
                  style={{ background: "var(--hj-red)", color: "white" }}
                  aria-label="Pin chat"
                >
                  <Pin className="h-3.5 w-3.5" />
                </button>
              </div>

              {/* Messages */}
              <div className="flex-1 overflow-y-auto px-6 py-6 space-y-4">
                {messages.map((m, i) => (
                  <div
                    key={i}
                    className={`flex flex-col ${m.from === "user" ? "items-end" : "items-start"}`}
                  >
                    <div
                      className="max-w-[75%] px-4 py-3 rounded-2xl text-sm whitespace-pre-line border-2"
                      style={{
                        background: m.from === "user" ? "var(--hj-orange)" : "var(--background)",
                        borderColor:
                          m.from === "user" ? "var(--hj-orange)" : "var(--hj-brown)",
                        color: m.from === "user" ? "white" : "var(--hj-brown)",
                      }}
                    >
                      {m.text}
                    </div>
                    {m.sources && m.sources.length > 0 && (
                      <div className="mt-2 flex flex-wrap gap-2 max-w-[75%]">
                        <span
                          className="text-[10px] font-bold uppercase tracking-widest self-center"
                          style={{ color: "var(--hj-brown)" }}
                        >
                          Sauce —
                        </span>
                        {m.sources.map((s) => (
                          <button
                            key={s.id}
                            onClick={() => setOpenSource(s)}
                            className="flex items-center gap-1.5 text-[11px] px-3 py-1.5 rounded-full border-2 hover:bg-muted transition-colors"
                            style={{ borderColor: "var(--hj-brown)", color: "var(--hj-brown)" }}
                          >
                            <FileText className="h-3 w-3" />
                            {s.name}
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>

              {/* Input */}
              <form
                onSubmit={send}
                className="px-6 py-4 border-t-2 flex gap-3"
                style={{ borderColor: "var(--hj-brown)" }}
              >
                <Input
                  value={draft}
                  onChange={(e) => setDraft(e.target.value)}
                  placeholder="Enter your query here…"
                  className="h-12 bg-input border-2 rounded-full px-5"
                />
                <Button
                  type="submit"
                  className="h-12 px-6 rounded-full font-display uppercase tracking-wider text-xs"
                  style={{
                    background: "var(--hj-orange)",
                    color: "white",
                    boxShadow: "var(--glow-primary)",
                  }}
                >
                  <Send className="h-4 w-4 mr-1" /> Send
                </Button>
              </form>
            </>
          )}

          {active === "profile" && (
            <Placeholder title="Profile" color="var(--hj-orange)" desc="Your details, role and shift preferences." />
          )}
          {active === "settings" && (
            <Placeholder title="Settings" color="var(--hj-green)" desc="Notifications, theme, and account options." />
          )}
          {active === "admin" && role === "admin" && <AdminPanel />}
        </section>

        {openSource && (
          <aside
            className="bg-card border-2 rounded-2xl flex flex-col overflow-hidden animate-fade-in"
            style={{ borderColor: "var(--hj-brown)" }}
          >
            <div
              className="flex items-center justify-between px-4 h-14 border-b-2 gap-2"
              style={{ borderColor: "var(--hj-brown)" }}
            >
              <div className="flex items-center gap-2 min-w-0">
                <FileText className="h-4 w-4 shrink-0" style={{ color: "var(--hj-orange)" }} />
                <span
                  className="font-display uppercase text-[11px] tracking-widest truncate"
                  style={{ color: "var(--hj-brown)" }}
                  title={openSource.name}
                >
                  {openSource.name}
                </span>
              </div>
              <button
                onClick={() => setOpenSource(null)}
                className="h-7 w-7 rounded-full flex items-center justify-center hover:bg-muted"
                style={{ color: "var(--hj-brown)" }}
                aria-label="Close source"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            {/* Text preview */}
            <div className="flex-1 overflow-auto p-4" style={{ background: "var(--background)" }}>
              <div
                className="h-full w-full rounded-lg border-2 p-4 overflow-y-auto text-xs whitespace-pre-wrap"
                style={{
                  borderColor: "var(--hj-brown)",
                  color: "var(--hj-brown)",
                  background: "var(--card)",
                }}
              >
                {openSource.preview || "No content available"}
              </div>
            </div>

            <div
              className="px-4 py-2 border-t-2 text-[10px] uppercase tracking-widest text-center"
              style={{ borderColor: "var(--hj-brown)", color: "var(--hj-brown)" }}
            >
              Preview · Read Only
            </div>
          </aside>
        )}
        </div>
      </div>
    </main>
  );
}

function AdminPanel() {
  const [adminTab, setAdminTab] = useState<"documents" | "users" | "logs">(
    "documents"
  );
  const [stats, setStats] = useState<{ total_documents: number } | null>(null);
  const [usersList, setUsersList] = useState<any[]>([]);
  const [logsList, setLogsList] = useState<any[]>([]);
  const [uploading, setUploading] = useState(false);
  const [statsLoading, setStatsLoading] = useState(false);
  const [usersLoading, setUsersLoading] = useState(false);
  const [logsLoading, setLogsLoading] = useState(false);

  useEffect(() => {
    if (adminTab === "documents") {
      setStatsLoading(true);
      getStats()
        .then(setStats)
        .finally(() => setStatsLoading(false));
    } else if (adminTab === "users") {
      setUsersLoading(true);
      getUsers()
        .then(setUsersList)
        .finally(() => setUsersLoading(false));
    } else if (adminTab === "logs") {
      setLogsLoading(true);
      getLogs(20)
        .then((res) => setLogsList(res.logs))
        .finally(() => setLogsLoading(false));
    }
  }, [adminTab]);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    if (files.length === 0) return;

    setUploading(true);
    try {
      await uploadDocuments(files);
      setStats(null);
      setAdminTab("documents");
    } catch (err) {
      console.error("Upload failed:", err);
    } finally {
      setUploading(false);
      e.target.value = "";
    }
  };

  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      {/* Tabs */}
      <div
        className="flex items-center gap-2 px-6 py-4 border-b-2"
        style={{ borderColor: "var(--hj-brown)" }}
      >
        {(["documents", "users", "logs"] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setAdminTab(tab)}
            className="font-display uppercase text-[11px] tracking-widest px-4 py-2 rounded-full border-2 transition-all"
            style={{
              borderColor: adminTab === tab ? "var(--hj-red)" : "transparent",
              background: adminTab === tab ? "var(--hj-red)" : "transparent",
              color: adminTab === tab ? "white" : "var(--hj-brown)",
            }}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto px-6 py-6">
        {adminTab === "documents" && (
          <div>
            <h3 className="font-display uppercase text-xl mb-4" style={{ color: "var(--hj-red)" }}>
              Upload Documents
            </h3>
            <div className="mb-6">
              <label className="block mb-3">
                <input
                  type="file"
                  multiple
                  accept=".pdf"
                  onChange={handleFileUpload}
                  disabled={uploading}
                  className="block w-full text-sm"
                />
              </label>
            </div>
            {uploading && <p style={{ color: "var(--hj-brown)" }}>Uploading...</p>}
            {stats && (
              <div
                className="p-4 rounded-lg border-2"
                style={{ borderColor: "var(--hj-brown)" }}
              >
                <p style={{ color: "var(--hj-brown)" }}>
                  Total Documents: <strong>{stats.total_documents}</strong>
                </p>
              </div>
            )}
            {statsLoading && <p style={{ color: "var(--hj-brown)" }}>Loading...</p>}
          </div>
        )}

        {adminTab === "users" && (
          <div>
            <h3 className="font-display uppercase text-xl mb-4" style={{ color: "var(--hj-red)" }}>
              Registered Users
            </h3>
            {usersLoading ? (
              <p style={{ color: "var(--hj-brown)" }}>Loading...</p>
            ) : usersList.length > 0 ? (
              <div className="space-y-2">
                {usersList.map((u) => (
                  <div
                    key={u.id}
                    className="flex items-center justify-between p-3 rounded-lg border-2"
                    style={{ borderColor: "var(--hj-brown)" }}
                  >
                    <span style={{ color: "var(--hj-brown)" }}>{u.username}</span>
                    <span
                      className="text-xs font-bold uppercase tracking-widest px-3 py-1 rounded-full"
                      style={{
                        background: u.role === "admin" ? "var(--hj-red)" :
                                   u.role === "manager" ? "var(--hj-green)" :
                                   "var(--hj-orange)",
                        color: "white",
                      }}
                    >
                      {u.role}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <p style={{ color: "var(--hj-brown)" }}>No users found</p>
            )}
          </div>
        )}

        {adminTab === "logs" && (
          <div>
            <h3 className="font-display uppercase text-xl mb-4" style={{ color: "var(--hj-red)" }}>
              Audit Logs
            </h3>
            {logsLoading ? (
              <p style={{ color: "var(--hj-brown)" }}>Loading...</p>
            ) : logsList.length > 0 ? (
              <div className="space-y-3">
                {logsList.map((log, idx) => (
                  <div
                    key={idx}
                    className="p-4 rounded-lg border-2"
                    style={{ borderColor: "var(--hj-brown)" }}
                  >
                    <p className="text-xs font-bold uppercase" style={{ color: "var(--hj-red)" }}>
                      {log.user_id} — {log.user_role.toUpperCase()}
                    </p>
                    <p className="text-sm mt-1" style={{ color: "var(--hj-brown)" }}>
                      {log.query}
                    </p>
                    <div className="flex gap-4 mt-2 text-xs" style={{ color: "var(--hj-brown)" }}>
                      <span>Retrieved: {log.retrieved_count}</span>
                      <span>Filtered: {log.filtered_count}</span>
                      <span>{log.status}</span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p style={{ color: "var(--hj-brown)" }}>No logs available</p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function Placeholder({ title, color, desc }: { title: string; color: string; desc: string }) {
  return (
    <div className="flex-1 flex flex-col items-center justify-center text-center px-6">
      <h2 className="font-display uppercase text-5xl mb-3" style={{ color }}>
        {title}
      </h2>
      <p className="text-sm max-w-md" style={{ color: "var(--hj-brown)" }}>
        {desc}
      </p>
    </div>
  );
}