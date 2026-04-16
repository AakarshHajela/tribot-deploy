import { useState } from "react";
import { useNavigate } from "react-router"; // 
import { login, LoginCredentials } from "../api/authApi";
import LoginForm from "../components/LoginForm";

export default function LoginPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState<string>("");
  const [password, setPassword] = useState<string>("");
  const [error, setError] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(false);
  const [attemptsLeft, setAttemptsLeft] = useState<number>(5);

  const isLocked = attemptsLeft <= 0;

  async function handleLogin(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError("");

    if (!email || !password) {
      setError("Please fill in both fields.");
      return;
    }

    setLoading(true);

    try {
      const credentials: LoginCredentials = { email, password };
      const user = await login(credentials);

      // ===== ADMIN REDIRECT =====
      // CurrentUser is underspecified — the /auth/me response includes `role` at runtime.
      const role = (user as unknown as { role?: string }).role;
      if (role === 'admin') {
        navigate('/admin', { replace: true });
      } else {
        // Keep existing redirect behaviour for clinicians (and any unknown role)
        navigate('/', { replace: true });
      }
      // ===== END ADMIN REDIRECT =====
    } catch (err: any) {
      const remaining = attemptsLeft - 1;
      setAttemptsLeft(remaining);

      // Extract error from your specific API client structure
      const errorMsg = err?.response?.data?.detail || "Invalid email or password.";

      if (remaining <= 0) {
        setError("Your account has been locked. Please contact your system administrator.");
      } else {
        setError(`${errorMsg} ${remaining} attempt${remaining !== 1 ? "s" : ""} remaining.`);
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen flex flex-col items-center justify-center bg-white font-sans px-4">
      <header className="text-center mb-10">
        <h1 className="text-[42px] font-bold text-[#1e3a5f] mb-2.5 tracking-wide">TRIBOT</h1>
        <p className="text-base text-[#5a6a7a] tracking-tight">
          Multilingual Clinical Translation Platform
        </p>
      </header>

      <section className="w-full max-w-[540px] bg-white rounded-2xl border border-[#e5e9f0] shadow-[0_2px_16px_rgba(0,0,0,0.07)] p-10">
        <LoginForm
          email={email}
          setEmail={setEmail}
          password={password}
          setPassword={setPassword}
          onSubmit={handleLogin}
          error={error}
          loading={loading}
          isLocked={isLocked}
        />
      </section>
    </main>
  );
}