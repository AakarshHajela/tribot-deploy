import { useState, useEffect } from 'react';

interface VitalInputProps {
  type: 'bp' | 'hr' | 'temp' | 'rr' | 'spo2';
  label: string;
  value: string | { systolic: string; diastolic: string };
  unit: string;
  normalRange: 
    | { min: number; max: number }
    | { systolic: { min: number; max: number }; diastolic: { min: number; max: number } };
  onChange: (value: string | { systolic: string; diastolic: string }) => void;
  readOnly?: boolean;
  placeholder?: boolean;
}

export function VitalInput({
  type,
  label,
  value,
  unit,
  normalRange,
  onChange,
  readOnly = false,
  placeholder = false
}: VitalInputProps) {
  const [localValue, setLocalValue] = useState(value);
  const [isEditing, setIsEditing] = useState(false);
  const [hasValue, setHasValue] = useState(!placeholder);

  useEffect(() => {
    setLocalValue(value);
  }, [value]);

  const handleChange = (newValue: string | { systolic: string; diastolic: string }) => {
    setLocalValue(newValue);
  };

  const handleBlur = () => {
    setIsEditing(false);
    
    // Check if there's a real value
    if (type === 'bp' && typeof localValue === 'object') {
      const hasRealValue = localValue.systolic.trim() !== '' || localValue.diastolic.trim() !== '';
      setHasValue(hasRealValue);
      if (hasRealValue) {
        onChange(localValue);
      }
    } else if (typeof localValue === 'string') {
      const hasRealValue = localValue.trim() !== '';
      setHasValue(hasRealValue);
      if (hasRealValue) {
        onChange(localValue);
      }
    }
  };

  const handleFocus = () => {
    if (!readOnly) {
      setIsEditing(true);
    }
  };

  const isAbnormal = () => {
    if (!hasValue) return false;
    
    if (type === 'bp' && typeof localValue === 'object') {
      const sys = parseInt(localValue.systolic) || 0;
      const dia = parseInt(localValue.diastolic) || 0;
      if (sys === 0 && dia === 0) return false;
      const range = normalRange as { systolic: { min: number; max: number }; diastolic: { min: number; max: number } };
      return sys < range.systolic.min || sys > range.systolic.max || 
             dia < range.diastolic.min || dia > range.diastolic.max;
    } else if (typeof localValue === 'string') {
      const val = type === 'temp' ? parseFloat(localValue) || 0 : parseInt(localValue) || 0;
      if (val === 0) return false;
      const range = normalRange as { min: number; max: number };
      return val < range.min || val > range.max;
    }
    return false;
  };

  const abnormal = isAbnormal();
  const borderStyle = hasValue ? 'border-solid' : 'border-dashed';

  const getNormalRangeText = () => {
    if (type === 'bp' && 'systolic' in normalRange) {
      return `Normal: ${normalRange.systolic.min}–${normalRange.systolic.max} / ${normalRange.diastolic.min}–${normalRange.diastolic.max} ${unit}`;
    } else if ('min' in normalRange) {
      return `Normal: ${normalRange.min}–${normalRange.max} ${unit}`;
    }
    return '';
  };

  // Get placeholder values
  const getPlaceholder = () => {
    if (type === 'bp') return { systolic: '120', diastolic: '80' };
    if (type === 'hr') return '75';
    if (type === 'temp') return '98.6';
    if (type === 'rr') return '16';
    if (type === 'spo2') return '98';
    return '';
  };

  const placeholderValue = getPlaceholder();

  return (
    <div className="mb-4 last:mb-0">
      <label className="block text-[11px] uppercase text-[#5F5E5A] mb-1.5">{label}</label>
      
      {type === 'bp' && typeof localValue === 'object' ? (
        <div className="flex gap-2 items-center">
          <input
            type="text"
            value={isEditing || hasValue ? localValue.systolic : ''}
            placeholder={typeof placeholderValue === 'object' ? placeholderValue.systolic : '120'}
            onChange={(e) => handleChange({ ...localValue, systolic: e.target.value })}
            onFocus={handleFocus}
            onBlur={handleBlur}
            readOnly={readOnly}
            className={`flex-1 max-w-[80px] h-[36px] px-3 rounded-md border ${borderStyle} ${
              abnormal
                ? 'border-[#A32D2D] bg-[#A32D2D]/5'
                : isEditing
                ? 'border-[#185FA5] ring-2 ring-[#185FA5] ring-offset-0'
                : 'border-[#E0DED6]'
            } text-[14px] focus:outline-none transition-all placeholder:text-[#5F5E5A]/50 ${
              readOnly ? 'cursor-not-allowed bg-[#F4F6F8]' : ''
            }`}
          />
          <span className="text-[14px] text-[#5F5E5A]">/</span>
          <input
            type="text"
            value={isEditing || hasValue ? localValue.diastolic : ''}
            placeholder={typeof placeholderValue === 'object' ? placeholderValue.diastolic : '80'}
            onChange={(e) => handleChange({ ...localValue, diastolic: e.target.value })}
            onFocus={handleFocus}
            onBlur={handleBlur}
            readOnly={readOnly}
            className={`flex-1 max-w-[80px] h-[36px] px-3 rounded-md border ${borderStyle} ${
              abnormal
                ? 'border-[#A32D2D] bg-[#A32D2D]/5'
                : isEditing
                ? 'border-[#185FA5] ring-2 ring-[#185FA5] ring-offset-0'
                : 'border-[#E0DED6]'
            } text-[14px] focus:outline-none transition-all placeholder:text-[#5F5E5A]/50 ${
              readOnly ? 'cursor-not-allowed bg-[#F4F6F8]' : ''
            }`}
          />
          <span className="text-[12px] text-[#5F5E5A] min-w-[45px]">{unit}</span>
        </div>
      ) : (
        <div className="flex gap-2 items-center">
          <input
            type="text"
            value={isEditing || hasValue ? (localValue as string) : ''}
            placeholder={placeholderValue as string}
            onChange={(e) => handleChange(e.target.value)}
            onFocus={handleFocus}
            onBlur={handleBlur}
            readOnly={readOnly}
            className={`flex-1 max-w-full h-[36px] px-3 rounded-md border ${borderStyle} ${
              abnormal
                ? 'border-[#A32D2D] bg-[#A32D2D]/5'
                : isEditing
                ? 'border-[#185FA5] ring-2 ring-[#185FA5] ring-offset-0'
                : 'border-[#E0DED6]'
            } text-[14px] focus:outline-none transition-all placeholder:text-[#5F5E5A]/50 ${
              readOnly ? 'cursor-not-allowed bg-[#F4F6F8]' : ''
            }`}
          />
          <span className="text-[12px] text-[#5F5E5A] min-w-[45px]">{unit}</span>
        </div>
      )}
      
      <p className="text-[10px] text-[#5F5E5A] mt-1 whitespace-normal">{getNormalRangeText()}</p>
    </div>
  );
}
