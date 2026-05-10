import { useEffect, useState, lazy, Suspense } from "react";
import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { login as apiLogin, register as apiRegister } from "@/lib/auth";

const DocumentTorus3D = lazy(() => import("@/components/DocumentTorus3D"));

export const Route = createFileRoute("/login")({
  component: LoginPage,
  head: () => ({
    meta: [
      { title: "Sign in" },
      { name: "description", content: "Sign in to your account." },
    ],
  }),
});

function LoginPage() {
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);
  const [role, setRole] = useState<"employee" | "manager" | "admin">("employee");
  const [mode, setMode] = useState<"signin" | "create">("signin");
  const navigate = useNavigate();
  const [signinRole, setSigninRole] = useState<"employee" | "manager" | "admin">("admin");
  const [error, setError] = useState<string>("");
  const [loading, setLoading] = useState(false);

  return (
    <main
      className="min-h-screen w-full grid lg:grid-cols-[30%_70%]"
      style={{ background: "var(--gradient-hero)" }}
    >
      {/* Left: Form */}
      <section className="relative flex flex-col items-center justify-center px-6 py-10 lg:px-10 lg:py-12">
        <div className="w-full max-w-sm flex flex-col">
        {/* Title */}
        <div className="mb-8">
          <div className="flex items-center gap-2 mb-6">
            <div className="h-7 w-7 rounded-sm" style={{ background: "var(--hj-orange)" }} />
            <span className="text-[10px] font-bold tracking-[0.3em] uppercase" style={{ color: "var(--hj-brown)" }}>
              HJ — Internal
            </span>
          </div>
          <h1 className="font-display uppercase text-3xl xl:text-4xl leading-[0.95]">
            <span style={{ color: "var(--hj-orange)" }}>Hungry</span>{" "}
            <span style={{ color: "var(--hj-green)" }}>Jacks</span>
            <br />
            <span style={{ color: "var(--hj-red)" }}>Resource</span>{" "}
            <span style={{ color: "var(--hj-brown)" }}>Center</span>
          </h1>
        </div>

        {/* Cards */}
        <div className="flex flex-col gap-4 w-full animate-fade-in">
          {/* Toggle bar */}
          <div
            className="relative grid grid-cols-2 p-1 rounded-full border-2"
            style={{ borderColor: "var(--hj-brown)", background: "var(--card)" }}
          >
            <div
              className="absolute top-1 bottom-1 w-[calc(50%-4px)] rounded-full transition-transform duration-300"
              style={{
                background: mode === "signin" ? "var(--hj-orange)" : "var(--hj-green)",
                transform: mode === "signin" ? "translateX(0)" : "translateX(calc(100% + 8px))",
              }}
            />
            {(["signin", "create"] as const).map((m) => (
              <button
                key={m}
                type="button"
                onClick={() => setMode(m)}
                className="relative z-10 h-10 font-display uppercase text-[11px] tracking-widest transition-colors"
                style={{ color: mode === m ? "white" : "var(--hj-brown)" }}
              >
                {m === "signin" ? "Sign in" : "Create account"}
              </button>
            ))}
          </div>

          {/* Card */}
          <div
            key={mode}
            className="bg-card border-2 rounded-2xl p-6 animate-fade-in"
            style={{ borderColor: mode === "signin" ? "var(--hj-brown)" : "var(--hj-green)" }}
          >
            {error && (
              <div
                className="mb-4 p-3 rounded-lg text-sm text-white"
                style={{ background: "var(--hj-red)" }}
              >
                {error}
              </div>
            )}
            <form
              onSubmit={async (e) => {
                e.preventDefault();
                setError("");
                setLoading(true);

                try {
                  const emailInput = document.querySelector('input[type="email"]') as HTMLInputElement;
                  const passwordInput = document.querySelector('input[type="password"]') as HTMLInputElement;
                  const fullNameInput = document.querySelector('input[placeholder="Full name"]') as HTMLInputElement;

                  const email = emailInput?.value;
                  const password = passwordInput?.value;

                  if (!email || !password) {
                    setError("Email and password required");
                    setLoading(false);
                    return;
                  }

                  if (mode === "create") {
                    const fullName = fullNameInput?.value;
                    if (!fullName) {
                      setError("Full name required");
                      setLoading(false);
                      return;
                    }
                    await apiRegister(email, password, role);
                    setMode("signin");
                  } else {
                    await apiLogin(email, password);
                    navigate({ to: "/dashboard" });
                  }
                } catch (err) {
                  setError(err instanceof Error ? err.message : "An error occurred");
                } finally {
                  setLoading(false);
                }
              }}
              className="space-y-3"
            >
              {mode === "create" && (
                <Input
                  type="text"
                  placeholder="Full name"
                  autoComplete="name"
                  required
                  className="h-11 bg-input border-2"
                />
              )}
              <Input
                type="email"
                placeholder="Email"
                autoComplete="email"
                required
                className="h-11 bg-input border-2"
              />
              <Input
                type="password"
                placeholder="Password"
                autoComplete={mode === "signin" ? "current-password" : "new-password"}
                required
                className="h-11 bg-input border-2"
              />

              {mode === "signin" && (
                <div className="pt-1">
                  <div className="grid grid-cols-3 gap-2">
                    {(["employee", "manager", "admin"] as const).map((r) => {
                      const active = signinRole === r;
                      const color =
                        r === "employee" ? "var(--hj-orange)" : r === "manager" ? "var(--hj-green)" : "var(--hj-red)";
                      return (
                        <button
                          key={r}
                          type="button"
                          onClick={() => setSigninRole(r)}
                          className="h-9 rounded-full font-display uppercase text-[10px] tracking-widest border-2 transition-all"
                          style={{
                            borderColor: color,
                            background: active ? color : "transparent",
                            color: active ? "white" : "var(--hj-brown)",
                          }}
                        >
                          {r}
                        </button>
                      );
                    })}
                  </div>
                </div>
              )}

              {mode === "create" && (
                <div className="pt-2">
                  <Label className="text-[10px] font-bold tracking-widest uppercase block mb-2" style={{ color: "var(--hj-brown)" }}>
                    I am a
                  </Label>
                  <div className="grid grid-cols-3 gap-2">
                    {(["employee", "manager", "admin"] as const).map((r) => {
                      const active = role === r;
                      const color =
                        r === "employee" ? "var(--hj-orange)" : r === "manager" ? "var(--hj-green)" : "var(--hj-red)";
                      return (
                        <button
                          key={r}
                          type="button"
                          onClick={() => setRole(r)}
                          className="h-10 rounded-full font-display uppercase text-[10px] tracking-widest border-2 transition-all"
                          style={{
                            borderColor: color,
                            background: active ? color : "transparent",
                            color: active ? "white" : "var(--hj-brown)",
                          }}
                        >
                          {r}
                        </button>
                      );
                    })}
                  </div>
                </div>
              )}

              <Button
                type="submit"
                disabled={loading}
                className="w-full h-11 font-display uppercase tracking-wider text-sm rounded-full mt-2 disabled:opacity-50"
                style={{
                  background: mode === "signin" ? "var(--hj-orange)" : "var(--hj-green)",
                  color: "white",
                  boxShadow: "var(--glow-primary)",
                }}
              >
                {loading ? "Loading..." : mode === "signin" ? "Login" : "Create account"}
              </Button>

              {mode === "signin" && (
                <a
                  href="#"
                  className="block text-center text-[11px] font-bold uppercase tracking-widest pt-1 hover:opacity-70"
                  style={{ color: "var(--hj-red)" }}
                >
                  Forgot password?
                </a>
              )}
            </form>
          </div>
        </div>
        </div>
      </section>

      {/* Right: 3D Graph */}
      <section
        className="relative hidden lg:block overflow-hidden border-l-4"
        style={{
          borderColor: "var(--hj-brown)",
          background:
            "radial-gradient(ellipse at center, oklch(0.32 0.05 50) 0%, oklch(0.18 0.04 50) 70%, oklch(0.12 0.03 50) 100%)",
        }}
      >
        {/* Vignette */}
        <div
          className="absolute inset-0 pointer-events-none"
          style={{
            background:
              "radial-gradient(ellipse at center, transparent 40%, rgba(0,0,0,0.55) 100%)",
          }}
        />
        <div className="absolute inset-0">
          {mounted && (
            <Suspense fallback={null}>
              <DocumentTorus3D />
            </Suspense>
          )}
        </div>
        <div className="absolute bottom-10 left-10 right-10 z-10 pointer-events-none">
          <h2 className="font-display text-3xl uppercase" style={{ color: "var(--hj-brown)" }}>
            Every document, <span style={{ color: "var(--hj-orange)" }}>in orbit.</span>
          </h2>
          <p className="mt-3 text-sm max-w-md" style={{ color: "var(--hj-brown)" }}>
            PDFs, images, and notes — spinning together in one connected workspace.
          </p>
        </div>
        {/* Bottom orange accent bar like HJ */}
        <div className="absolute bottom-0 left-0 right-0 h-2" style={{ background: "var(--hj-orange)" }} />
      </section>
      {/* Mobile bottom bar */}
      <div className="lg:hidden h-2 w-full" style={{ background: "var(--hj-orange)" }} />
    </main>
  );
}