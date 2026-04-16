import React, { useState } from "react";

type LoginFormProps = {
  onSubmit: (e: React.FormEvent<HTMLFormElement>) => void;
  email: string;
  setEmail: (val: string) => void;
  password:  string;
  setPassword: (val: string) => void;
  error: string;
  loading: boolean;
  isLocked: boolean;
};

export default function LoginForm({
  onSubmit,
  email,
  setEmail,
  password,
  setPassword,
  error,
  loading,
  isLocked,
}: LoginFormProps) {
  const [showPassword, setShowPassword] = useState(false);

  return (
    <div className="flex flex-col gap-5">
      <form onSubmit={onSubmit} className="flex flex-col gap-5">
        {/* Email Field */}
        <div className="flex flex-col gap-2">
          <label className="text-[15px] font-bold text-[#1e3a5f]">Email</label>
          <input
            type="text"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="Enter email"
            autoFocus
            autoComplete="email"
            disabled={isLocked}
            className="w-full px-4 py-[14px] text-[15px] text-[#333] bg-[#f0f2f5] rounded-[10px] outline-none transition-colors focus:bg-[#e8edf3] disabled:opacity-50 disabled:cursor-not-allowed placeholder:text-[#aab0ba]"
          />
        </div>

        {/* Password Field */}
        <div className="flex flex-col gap-2">
          <label className="text-[15px] font-bold text-[#1e3a5f]">Password</label>
          <div className="relative">
            <input
              type={showPassword ? "text" : "password"}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter password"
              autoComplete="current-password"
              disabled={isLocked}
              className="w-full pl-4 pr-12.5 py-3.5 text-[15px] text-[#333] bg-[#f0f2f5] rounded-[10px] outline-none transition-colors focus:bg-[#e8edf3] disabled:opacity-50 disabled:cursor-not-allowed placeholder:text-[#aab0ba]"
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-3.5 top-1/2 -translate-y-1/2 text-[#7a8a9a] hover:text-[#1e3a5f] flex items-center justify-center"
              aria-label={showPassword ? "Hide password" : "Show password"}
            >
              {showPassword ? (
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M17.94 17.94A10.07 10.07 0 0112 20c-7 0-11-8-11-8a18.45 18.45 0 015.06-5.94" />
                  <path d="M9.9 4.24A9.12 9.12 0 0112 4c7 0 11 8 11 8a18.5 18.5 0 01-2.16 3.19" />
                  <line x1="1" y1="1" x2="23" y2="23" />
                </svg>
              ) : (
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                  <circle cx="12" cy="12" r="3" />
                </svg>
              )}
            </button>
          </div>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="flex items-start gap-2 bg-[#fff5f5] border border-[#fca5a5] rounded-lg p-2.5 px-3.5">
            <span className="font-bold text-[#dc2626] text-[13px] leading-6 shrink-0">!</span>
            <span className="text-[#dc2626] text-[13px] leading-6">{error}</span>
          </div>
        )}

        {/* Submit Button */}
        <button
          type="submit"
          disabled={loading || isLocked}
          className={`w-full p-[15px] bg-[#2a9d8f] text-white rounded-[10px] text-base font-bold tracking-tight transition-colors mt-1.5 
            ${(loading || isLocked) ? "opacity-60 cursor-not-allowed" : "hover:bg-[#238a7d]"}`}
        >
          {loading ? "Signing in..." : "Sign In"}
        </button>
      </form>

      {/* Footer */}
      <div className="text-center text-[12px] text-[#aaa] mt-2">
        <a href="/forgot-password" className="text-[#2a9d8f] no-underline hover:underline">Forgot password?</a>
        <span className="mx-2">·</span>
        <span>Contact your system administrator for access</span>
      </div>
    </div>
  );
}