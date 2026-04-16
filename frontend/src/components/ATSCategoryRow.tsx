interface ATSCategoryRowProps {
  category: 1 | 2 | 3 | 4 | 5;
  label: string;
  subLabel: string;
  selected: boolean;
  onClick: () => void;
  disabled?: boolean;
}

export function ATSCategoryRow({ category, label, subLabel, selected, onClick, disabled = false }: ATSCategoryRowProps) {
  const selectedStyles = {
    1: 'bg-[#A32D2D]/10 border-2 border-[#A32D2D]',
    2: 'bg-[#D94F04]/10 border-2 border-[#D94F04]',
    3: 'bg-[#BA7517]/10 border-2 border-[#BA7517]',
    4: 'bg-[#5F5E5A]/30 border-2 border-[#5F5E5A]',
    5: 'bg-[#5F5E5A]/30 border-2 border-[#5F5E5A]'
  };

  const colors = {
    1: 'bg-[#A32D2D] text-white',
    2: 'bg-[#D94F04] text-white',
    3: 'bg-[#BA7517] text-white',
    4: 'bg-[#5F5E5A] text-white',
    5: 'bg-[#5F5E5A] text-white'
  };

  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`w-full px-3 py-2 rounded-lg border transition-all text-left flex items-center gap-3 ${
        selected
          ? selectedStyles[category]
          : 'border-[#E0DED6] bg-white hover:border-[#185FA5] hover:bg-[#185FA5]/5'
      } ${disabled ? 'cursor-not-allowed opacity-50' : ''}`}
    >
      <div className={`w-8 h-8 rounded-full flex items-center justify-center text-[14px] font-bold flex-shrink-0 ${colors[category]}`}>
        {category}
      </div>
      <div className="flex-1 min-w-0">
        <div className="text-[14px] font-medium text-[#1A1A1A]">{label}</div>
        <div className="text-[11px] text-[#5F5E5A]">{subLabel}</div>
      </div>
    </button>
  );
}
