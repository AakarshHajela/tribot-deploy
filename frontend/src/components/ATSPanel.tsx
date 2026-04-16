import { useState } from 'react';
import { ATSCategoryRow } from './ATSCategoryRow';

interface ATSPanelProps {
  onCategoryChange?: (category: 1 | 2 | 3 | 4 | 5 | null) => void;
  onSubmit?: () => void;
  readOnly?: boolean;
  selectedCategory?: 1 | 2 | 3 | 4 | 5 | null;
}

export function ATSPanel({ 
  onCategoryChange,
  onSubmit,
  readOnly = false,
  selectedCategory: externalCategory
}: ATSPanelProps) {
  const [selectedCategory, setSelectedCategory] = useState<1 | 2 | 3 | 4 | 5 | null>(externalCategory || null);

  const handleCategoryClick = (category: 1 | 2 | 3 | 4 | 5) => {
    if (readOnly) return;
    setSelectedCategory(category);
    onCategoryChange?.(category);
  };

  const categories = [
    { category: 1 as const, label: 'Resuscitation', subLabel: 'Immediate · life threat' },
    { category: 2 as const, label: 'Emergency', subLabel: 'Within 10 min · emergency' },
    { category: 3 as const, label: 'Urgent', subLabel: 'Within 30 min · urgent' },
    { category: 4 as const, label: 'Semi-urgent', subLabel: 'Within 60 min · semi-urgent' },
    { category: 5 as const, label: 'Non-urgent', subLabel: 'Within 120 min · non-urgent' }
  ];

  return (
    <div className="flex flex-col h-full bg-white rounded-xl overflow-hidden">
      {/* Header */}
      <div className="h-[32px] bg-[#F4F6F8] px-4 flex items-center justify-between border-b border-[#E0DED6] flex-shrink-0">
        <span className="text-[12px] font-medium text-[#1A1A1A]">ATS category</span>
        <span className="text-[11px] text-[#5F5E5A]">nurse confirms</span>
      </div>

      {/* Categories */}
      <div className="p-4 space-y-2 flex-1">
        {categories.map(({ category, label, subLabel }) => (
          <ATSCategoryRow
            key={category}
            category={category}
            label={label}
            subLabel={subLabel}
            selected={selectedCategory === category}
            onClick={() => handleCategoryClick(category)}
            disabled={readOnly}
          />
        ))}
      </div>

      {/* Submit button */}
      {!readOnly && (
        <div className="p-4 border-t border-[#E0DED6] flex-shrink-0">
          <button 
            onClick={onSubmit}
            disabled={!selectedCategory}
            className={`w-full px-4 py-2.5 rounded-md text-[14px] font-medium transition-colors ${
              selectedCategory
                ? 'bg-[#185FA5] text-white hover:bg-[#185FA5]/90'
                : 'bg-[#E0DED6] text-[#5F5E5A] cursor-not-allowed'
            }`}
          >
            Submit session
          </button>
        </div>
      )}
    </div>
  );
}