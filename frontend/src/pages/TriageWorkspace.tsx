import { useState, useCallback } from 'react';
import { useApp } from '../context/AppContext';
import { LiveChatPanel } from '../components/LiveChatPanel';
import { VitalsPanel } from '../components/VitalsPanel';
import { ATSPanel } from '../components/ATSPanel';
import { SessionSummary } from '../components/SessionSummary';
import { QuickTranslateDrawer } from '../components/QuickTranslateDrawer';
import { SessionSavedModal } from '../components/SessionSavedModal';
import { SelectPatientModal } from '../components/SelectPatientModal';
import { MobileNav } from '../components/MobileNav';
import { PatientBanner } from '../components/PatientBanner';
import { Message } from '../types';
import { toast } from 'sonner';
import { useTriageSession } from '../hooks/useTriageSession';
import { ATSCategory } from '../api/triageApi';
import { Patient } from '../api/patientsApi';

type MobileTab = 'chat' | 'vitals' | 'ats';
type TabletTab = 'vitals' | 'ats';

export default function TriageWorkspace() {
  const { mode, setMode, currentPatient, currentSession, setCurrentSession } = useApp();

  const isHistoryView = mode === 'history' && !!currentSession;
  const isIdleMode = mode === 'idle';
  const isActiveMode = mode === 'active';
  const isReadOnly = isHistoryView || isIdleMode;

  const { session, isSubmitting, error: sessionError, startSession, updateSession, finaliseSession, clearSession } =
    useTriageSession();

  const [quickTranslateOpen, setQuickTranslateOpen] = useState(false);
  const [sessionSavedOpen, setSessionSavedOpen] = useState(false);
  const [selectPatientModalOpen, setSelectPatientModalOpen] = useState(!isHistoryView);
  const [selectedCategory, setSelectedCategory] = useState<ATSCategory | null>(null);
  const [hasAbnormalVitals, setHasAbnormalVitals] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [mobileTab, setMobileTab] = useState<MobileTab>('chat');
  const [tabletTab, setTabletTab] = useState<TabletTab>('vitals');

  // Surface non-fatal session errors as toasts
  if (sessionError) toast.error(sessionError);

  // ---------------------------------------------------------------------------
  // Handlers
  // ---------------------------------------------------------------------------

  const handleCategoryChange = useCallback(async (category: ATSCategory | null) => {
    setSelectedCategory(category);
    if (category && session) {
      console.log('[ATS] patching session', session.id, 'with category', category);
      await updateSession({ ats_category: category, nurse_confirmed_ats: true });
    } else {
      console.warn('[ATS] skipped patch — session is null, category:', category);
    }
  }, [session, updateSession]);

  const handleSubmit = useCallback(async () => {
    if (!selectedCategory) {
      toast.error('Please assign an ATS category before submitting');
      return;
    }
    const ok = await finaliseSession(selectedCategory);
    if (ok) setSessionSavedOpen(true);
    else toast.error('Submission failed — please try again.');
  }, [selectedCategory, finaliseSession]);

  const handleStartNew = useCallback(() => {
    setSessionSavedOpen(false);
    setMode('idle');
    setSelectedCategory(null);
    setHasAbnormalVitals(false);
    setMessages([]);
    setCurrentSession(null);
    clearSession();
  }, [setMode, setCurrentSession, clearSession]);

  const handleSelectPatient = useCallback(async (patient: Patient) => {
    setMode('active');
    setSelectPatientModalOpen(false);
    await startSession({ patient_id: patient.id, patient_language: patient.patient_language });
  }, [setMode, startSession]);

  const handleWorkspaceClick = () => {
    if (isIdleMode) setSelectPatientModalOpen(true);
  };

  const handleBackToWorkspace = () => {
    setMode('idle');
    setCurrentSession(null);
  };

  // ---------------------------------------------------------------------------
  // Shared panel props — avoids repetition across breakpoint layouts
  // ---------------------------------------------------------------------------

  const chatPanelProps = {
    sessionId: session?.id ?? null,
    hasAbnormalVitals,
    readOnly: isHistoryView,
    readOnlyDate: currentSession ? currentSession.endTime.toLocaleDateString() : undefined,
    initialMessages: currentSession?.messages ?? [],
    onMessagesChange: setMessages,
  };

  const vitalsPanelProps = {
    onAbnormalChange: setHasAbnormalVitals,
    onVitalsChange: isHistoryView ? undefined : updateSession,
    readOnly: isHistoryView,
    initialValues: currentSession?.vitals,
  };

  const atsPanelProps = {
    onCategoryChange: handleCategoryChange,
    onSubmit: handleSubmit,
    readOnly: isHistoryView,
    selectedCategory,
    isSubmitting,
  };

  const idleClass = isIdleMode ? 'opacity-40 pointer-events-none' : '';

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------

  return (
    <>
      <div className="pt-[52px] pb-0 md:pb-0 h-screen">
        {(isActiveMode || isHistoryView) && (
          <PatientBanner patient={currentPatient} isLive={isActiveMode} />
        )}

        <div
          className={`max-w-[1440px] mx-auto h-[calc(100vh-52px)] p-0 md:p-4 flex gap-0 md:gap-4 ${
            isIdleMode ? 'cursor-not-allowed' : ''
          }`}
          onClick={handleWorkspaceClick}
        >
          {/* DESKTOP — three columns */}
          <div className="hidden lg:flex lg:flex-row lg:gap-4 w-full h-full">
            <div className={`flex-[5] min-w-0 ${idleClass}`}>
              <LiveChatPanel {...chatPanelProps} />
            </div>
            <div className={`flex-[2] min-w-0 ${idleClass}`}>
              <VitalsPanel {...vitalsPanelProps} />
            </div>
            <div className={`flex-[3] min-w-0 ${idleClass}`}>
              {isHistoryView && currentSession ? (
                <SessionSummary session={currentSession} onBack={handleBackToWorkspace} />
              ) : (
                <ATSPanel {...atsPanelProps} />
              )}
            </div>
          </div>

          {/* TABLET — chat left, tabbed vitals/ats right */}
          <div className="hidden md:flex lg:hidden flex-row gap-4 w-full h-full">
            <div className={`flex-[55] min-w-0 ${idleClass}`}>
              <LiveChatPanel {...chatPanelProps} />
            </div>
            <div className={`flex-[45] min-w-0 flex flex-col ${idleClass}`}>
              <div className="flex gap-1 mb-2">
                {(['vitals', 'ats'] as TabletTab[]).map((tab) => (
                  <button
                    key={tab}
                    onClick={() => setTabletTab(tab)}
                    className={`flex-1 px-3 py-2 rounded-t-lg text-[13px] font-medium transition-colors relative ${
                      tabletTab === tab
                        ? 'bg-white text-[#185FA5]'
                        : 'bg-[#F4F6F8] text-[#5F5E5A] hover:bg-[#E0DED6]'
                    }`}
                  >
                    {tab === 'vitals' ? 'Vitals' : 'ATS category'}
                    {tab === 'vitals' && hasAbnormalVitals && (
                      <span className="absolute top-1 right-1 w-2 h-2 bg-[#A32D2D] rounded-full" />
                    )}
                  </button>
                ))}
              </div>
              <div className="flex-1 min-h-0">
                {tabletTab === 'vitals' ? (
                  <VitalsPanel {...vitalsPanelProps} />
                ) : isHistoryView && currentSession ? (
                  <SessionSummary session={currentSession} onBack={handleBackToWorkspace} />
                ) : (
                  <ATSPanel {...atsPanelProps} />
                )}
              </div>
            </div>
          </div>

          {/* MOBILE — single panel, bottom nav */}
          <div className="md:hidden flex flex-col w-full h-[calc(100vh-112px)] p-4">
            <div className={`flex-1 min-h-0 ${idleClass}`}>
              {mobileTab === 'chat' && <LiveChatPanel {...chatPanelProps} />}
              {mobileTab === 'vitals' && <VitalsPanel {...vitalsPanelProps} />}
              {mobileTab === 'ats' && (
                isHistoryView && currentSession ? (
                  <SessionSummary session={currentSession} onBack={handleBackToWorkspace} />
                ) : (
                  <ATSPanel {...atsPanelProps} />
                )
              )}
            </div>
          </div>
        </div>

        {!isIdleMode && <MobileNav activeTab={mobileTab} onTabChange={setMobileTab} />}
      </div>

      {/* Modals */}
      <QuickTranslateDrawer isOpen={quickTranslateOpen} onClose={() => setQuickTranslateOpen(false)} />
      <SessionSavedModal
        isOpen={sessionSavedOpen}
        onClose={() => setSessionSavedOpen(false)}
        onStartNew={handleStartNew}
        selectedCategory={selectedCategory}
      />
      <SelectPatientModal
        isOpen={selectPatientModalOpen}
        onSelectPatient={handleSelectPatient}
      />
    </>
  );
}