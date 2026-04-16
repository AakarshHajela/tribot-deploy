interface SessionSavedModalProps {
  isOpen: boolean;
  onClose: () => void;
  onStartNew: () => void;
  selectedCategory?: 1 | 2 | 3 | 4 | 5 | null;
}

export function SessionSavedModal({ isOpen, onClose, onStartNew, selectedCategory }: SessionSavedModalProps) {
  if (!isOpen) return null;

  const categoryText = selectedCategory ? `ATS Cat ${selectedCategory}` : 'No category';

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center pb-8">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-black/40"
        onClick={onClose}
      ></div>

      {/* Bottom sheet */}
      <div className="relative bg-white rounded-xl shadow-2xl w-[480px] p-6">
        <div className="text-center">
          <div className="w-12 h-12 bg-[#3B6D11]/10 rounded-full flex items-center justify-center mx-auto mb-3">
            <svg className="w-6 h-6 text-[#3B6D11]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <h3 className="text-[16px] font-medium text-[#1A1A1A] mb-1">Session saved</h3>
          <p className="text-[14px] text-[#5F5E5A] mb-4">
            {categoryText} assigned to Maria Garcia. Transcript logged.
          </p>
          <button
            onClick={onStartNew}
            className="w-full px-4 py-2.5 bg-[#185FA5] text-white rounded-md text-[14px] font-medium hover:bg-[#185FA5]/90 transition-colors"
          >
            Start new session
          </button>
        </div>
      </div>
    </div>
  );
}