import { Outlet } from 'react-router';
import { useState, useEffect } from 'react';
import { useLocation } from 'react-router';
import { NavigationBar } from './components/NavigationBar';
import { QuickTranslateDrawer } from './components/QuickTranslateDrawer';
import { AppProvider, useApp } from './context/AppContext';
import { Toaster } from 'sonner';
import { Patient } from './types';
import { useCurrentUser } from './hooks/useCurrentUser';

function RootContent() {
  const { mode, setMode, currentPatient, setCurrentPatient } = useApp();
  const [quickTranslateOpen, setQuickTranslateOpen] = useState(false);
  const location = useLocation();
  const { user } = useCurrentUser();

  useEffect(() => {
    if (location.pathname === '/history' && mode === 'idle') {
      setCurrentPatient(null);
    }
  }, [location.pathname, mode, setCurrentPatient]);

  const handleSelectPatient = (patient: Patient) => {
    setCurrentPatient(patient);
    setMode('active');
  };

  return (
    <div className="min-h-screen bg-[#F4F6F8]">
      <Toaster position="bottom-center" />
      <NavigationBar
        mode={mode}
        currentPatient={currentPatient}
        onQuickTranslate={() => setQuickTranslateOpen(true)}
        onSelectPatient={handleSelectPatient}
      />
      <Outlet />
      <QuickTranslateDrawer
        isOpen={quickTranslateOpen}
        onClose={() => setQuickTranslateOpen(false)}
      />
    </div>
  );
}

export default function Root() {
  return (
    <AppProvider>
      <RootContent />
    </AppProvider>
  );
}