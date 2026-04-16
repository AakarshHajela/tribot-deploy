import { Link, useLocation } from 'react-router';
import { Zap, Menu, Search as SearchIcon, X, LogOut } from 'lucide-react';
import { logout } from '../api/authApi';
import { PatientSearch } from './PatientSearch';
import { Patient, AppMode } from '../types';
import { useState } from 'react';

interface NavigationBarProps {
  mode: AppMode;
  currentPatient: Patient | null;
  onQuickTranslate: () => void;
  onSelectPatient: (patient: Patient) => void;
}

export function NavigationBar({ 
  mode, 
  currentPatient, 
  onQuickTranslate,
  onSelectPatient 
}: NavigationBarProps) {
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [mobileSearchOpen, setMobileSearchOpen] = useState(false);
  
  const isWorkspace = location.pathname === '/';
  const isHistory = location.pathname === '/history';

  const canNavigate = mode !== 'login';
  const canQuickTranslate = mode !== 'login';

  return (
    <nav className="fixed top-0 left-0 right-0 h-[52px] bg-white border-b border-[#E0DED6] z-60">
      <div className="max-w-[1440px] mx-auto h-full px-4 flex items-center justify-between">
        {/* Left: Hamburger (tablet) + Logo + Nav (desktop) */}
        <div className="flex items-center gap-3 md:gap-6">
          {/* Hamburger menu - tablet only */}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="md:lg:hidden text-[#5F5E5A] hover:text-[#1A1A1A]"
          >
            {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>

          {/* Logo */}
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 bg-[#185FA5] rounded-md flex items-center justify-center">
              <span className="text-white text-[14px] font-bold">T</span>
            </div>
            <span className="text-[15px] font-semibold text-[#1A1A1A] hidden sm:inline">TRIBOT</span>
          </div>

          {/* Desktop nav links */}
          <div className="hidden lg:flex items-center gap-1">
            <Link
              to="/"
              className={`px-3 py-1.5 rounded-md text-[13px] font-medium transition-colors ${
                isWorkspace
                  ? 'bg-[#185FA5]/10 text-[#185FA5]'
                  : canNavigate
                  ? 'text-[#5F5E5A] hover:bg-[#F4F6F8]'
                  : 'text-[#5F5E5A] opacity-40 cursor-not-allowed pointer-events-none'
              }`}
            >
              Triage workspace
            </Link>
            <Link
              to="/history"
              className={`px-3 py-1.5 rounded-md text-[13px] font-medium transition-colors ${
                isHistory
                  ? 'bg-[#185FA5]/10 text-[#185FA5]'
                  : canNavigate
                  ? 'text-[#5F5E5A] hover:bg-[#F4F6F8]'
                  : 'text-[#5F5E5A] opacity-40 cursor-not-allowed pointer-events-none'
              }`}
            >
              History
            </Link>
          </div>
        </div>

        {/* Center: Patient search - desktop/tablet */}
        <div className="hidden md:block">
          <PatientSearch 
            onSelectPatient={onSelectPatient} 
            disabled={mode === 'login'}
          />
        </div>

        {/* Right: Patient pill + Quick translate + Search icon (mobile) + Avatar */}
        <div className="flex items-center gap-2 md:gap-3">
          {currentPatient && (
            <div className="hidden sm:block px-3 py-1.5 bg-[#F4F6F8] rounded-full text-[12px] font-medium text-[#1A1A1A]">
              {currentPatient.name} · {currentPatient.language.substring(0, 2).toUpperCase()}
            </div>
          )}

          {/* Quick translate - desktop/tablet */}
          <button
            onClick={onQuickTranslate}
            disabled={!canQuickTranslate}
            className={`hidden lg:flex items-center gap-1.5 px-3 py-1.5 rounded-md text-[13px] font-medium transition-colors ${
              canQuickTranslate
                ? 'text-[#185FA5] hover:bg-[#185FA5]/10'
                : 'text-[#5F5E5A] opacity-40 cursor-not-allowed'
            }`}
          >
            <Zap className="w-4 h-4" />
            Quick translate
          </button>

          {/* Search icon - mobile only */}
          <button
            onClick={() => setMobileSearchOpen(!mobileSearchOpen)}
            className="md:hidden text-[#5F5E5A] hover:text-[#1A1A1A]"
          >
            <SearchIcon className="w-5 h-5" />
          </button>

          <div className="w-8 h-8 bg-[#185FA5] rounded-full flex items-center justify-center">
            <span className="text-white text-[12px] font-medium">SC</span>
          </div>

          {/* ===== LOGOUT BUTTON - Racha ===== */}
          <button
            onClick={logout}
            className="hidden lg:flex items-center gap-1.5 px-3 py-1.5 rounded-md text-[13px] font-medium transition-colors text-[#5F5E5A] hover:bg-[#F4F6F8]"
          >
            <LogOut className="w-4 h-4" />
            Log out
          </button>
          {/* ===== END LOGOUT BUTTON ===== */}
        </div>
      </div>

      {/* Mobile/Tablet dropdown menu */}
      {mobileMenuOpen && (
        <div className="lg:hidden absolute top-full left-0 right-0 bg-white border-b border-[#E0DED6] shadow-lg">
          <div className="p-4 space-y-2">
            <Link
              to="/"
              onClick={() => setMobileMenuOpen(false)}
              className={`block px-3 py-2 rounded-md text-[14px] font-medium transition-colors ${
                isWorkspace ? 'bg-[#185FA5]/10 text-[#185FA5]' : 'text-[#5F5E5A]'
              }`}
            >
              Triage workspace
            </Link>
            <Link
              to="/history"
              onClick={() => setMobileMenuOpen(false)}
              className={`block px-3 py-2 rounded-md text-[14px] font-medium transition-colors ${
                isHistory ? 'bg-[#185FA5]/10 text-[#185FA5]' : 'text-[#5F5E5A]'
              }`}
            >
              History
            </Link>
            <button
              onClick={() => {
                onQuickTranslate();
                setMobileMenuOpen(false);
              }}
              disabled={!canQuickTranslate}
              className={`w-full text-left flex items-center gap-2 px-3 py-2 rounded-md text-[14px] font-medium transition-colors ${
                canQuickTranslate ? 'text-[#185FA5]' : 'text-[#5F5E5A] opacity-40'
              }`}
            >
              <Zap className="w-4 h-4" />
              Quick translate
            </button>

            {/* ===== LOGOUT BUTTON - Racha ===== */}
            <button
              onClick={() => {
                logout();
                setMobileMenuOpen(false);
              }}
              className="w-full text-left flex items-center gap-2 px-3 py-2 rounded-md text-[14px] font-medium transition-colors text-[#5F5E5A] hover:bg-[#F4F6F8]"
            >
              <LogOut className="w-4 h-4" />
              Log out
            </button>
            {/* ===== END LOGOUT BUTTON ===== */}
          </div>
        </div>
      )}

      {/* Mobile search panel */}
      {mobileSearchOpen && (
        <div className="md:hidden absolute top-full left-0 right-0 bg-white border-b border-[#E0DED6] shadow-lg p-4">
          <PatientSearch 
            onSelectPatient={(patient) => {
              onSelectPatient(patient);
              setMobileSearchOpen(false);
            }} 
            disabled={mode === 'login'}
          />
        </div>
      )}
    </nav>
  );
}
