import { useState, useEffect, useRef } from 'react';
import { VitalInput } from './VitalInput';
import { Lock } from 'lucide-react';
import { PatchSessionPayload } from '../api/triageApi';

interface VitalsPanelProps {
  onAbnormalChange?: (hasAbnormal: boolean) => void;
  onVitalsChange?: (patch: PatchSessionPayload) => void;
  readOnly?: boolean;
  initialValues?: {
    bp: { systolic: string; diastolic: string };
    hr: string;
    temp: string;
    rr: string;
    spo2: string;
  };
}

export function VitalsPanel({ onAbnormalChange, onVitalsChange, readOnly = false, initialValues }: VitalsPanelProps) {
  const [vitals, setVitals] = useState(
    initialValues || {
      bp: { systolic: '120', diastolic: '80' },
      hr: '75',
      temp: '98.6',
      rr: '16',
      spo2: '98'
    }
  );

  // Debounce timer ref so we don't spam PATCH on every keystroke
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const patchVitals = (updated: typeof vitals) => {
    if (!onVitalsChange || readOnly) return;
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      const patch: PatchSessionPayload = {};
      const sys = parseInt(updated.bp.systolic);
      const dia = parseInt(updated.bp.diastolic);
      const hr  = parseInt(updated.hr);
      const rr  = parseInt(updated.rr);
      const spo2 = parseInt(updated.spo2);
      const temp = parseFloat(updated.temp);
      if (!isNaN(sys))  patch.bp_systolic = sys;
      if (!isNaN(dia))  patch.bp_diastolic = dia;
      if (!isNaN(hr))   patch.heart_rate = hr;
      if (!isNaN(rr))   patch.respiratory_rate = rr;
      if (!isNaN(spo2)) patch.spo2 = spo2;
      if (!isNaN(temp)) patch.temperature = temp;
      if (Object.keys(patch).length > 0) onVitalsChange(patch);
    }, 800);
  };

  const checkAbnormal = (type: string, value: string | { systolic: string; diastolic: string }): boolean => {
    if (type === 'bp' && typeof value === 'object') {
      const sys = parseInt(value.systolic) || 0;
      const dia = parseInt(value.diastolic) || 0;
      return sys < 90 || sys > 180 || dia < 60 || dia > 110;
    } else if (type === 'hr') {
      const val = parseInt(value as string) || 0;
      return val < 40 || val > 150;
    } else if (type === 'temp') {
      const val = parseFloat(value as string) || 0;
      return val < 96.0 || val > 103.0;
    } else if (type === 'rr') {
      const val = parseInt(value as string) || 0;
      return val < 10 || val > 25;
    } else if (type === 'spo2') {
      const val = parseInt(value as string) || 0;
      return val < 90 || val > 100;
    }
    return false;
  };

  const abnormalCount = [
    checkAbnormal('bp', vitals.bp),
    checkAbnormal('hr', vitals.hr),
    checkAbnormal('temp', vitals.temp),
    checkAbnormal('rr', vitals.rr),
    checkAbnormal('spo2', vitals.spo2)
  ].filter(Boolean).length;

  useEffect(() => {
    onAbnormalChange?.(abnormalCount > 0);
  }, [abnormalCount, onAbnormalChange]);

  return (
    <div className="flex flex-col h-full bg-white rounded-xl overflow-hidden">
      {/* Header */}
      <div className="h-[32px] bg-[#F4F6F8] px-4 flex items-center justify-between border-b border-[#E0DED6] flex-shrink-0">
        <div className="flex items-center gap-2">
          <span className="text-[12px] font-medium text-[#1A1A1A]">Vitals</span>
          {abnormalCount > 0 && (
            <span className="px-2 py-0.5 bg-[#A32D2D] text-white text-[10px] font-medium rounded-full">
              {abnormalCount} abnormal
            </span>
          )}
          {readOnly && <Lock className="w-3 h-3 text-[#5F5E5A]" />}
        </div>
        {!readOnly && <span className="text-[11px] text-[#3B6D11]">auto-saved</span>}
      </div>

      {/* Vitals inputs */}
      <div className="flex-1 overflow-y-auto overflow-x-hidden p-4">
        <VitalInput
          type="bp"
          label="Blood pressure"
          value={vitals.bp}
          unit="mmHg"
          normalRange={{
            systolic: { min: 90, max: 180 },
            diastolic: { min: 60, max: 110 }
          }}
          onChange={(value) => {
            const updated = { ...vitals, bp: value as { systolic: string; diastolic: string } };
            setVitals(updated);
            patchVitals(updated);
          }}
          readOnly={readOnly}
          placeholder={!readOnly}
        />
        <VitalInput
          type="hr"
          label="Heart rate"
          value={vitals.hr}
          unit="bpm"
          normalRange={{ min: 40, max: 150 }}
          onChange={(value) => {
            const updated = { ...vitals, hr: value as string };
            setVitals(updated);
            patchVitals(updated);
          }}
          readOnly={readOnly}
          placeholder={!readOnly}
        />
        <VitalInput
          type="temp"
          label="Temperature"
          value={vitals.temp}
          unit="°F"
          normalRange={{ min: 96, max: 103 }}
          onChange={(value) => {
            const updated = { ...vitals, temp: value as string };
            setVitals(updated);
            patchVitals(updated);
          }}
          readOnly={readOnly}
          placeholder={!readOnly}
        />
        <VitalInput
          type="rr"
          label="Respiratory rate"
          value={vitals.rr}
          unit="br/min"
          normalRange={{ min: 10, max: 25 }}
          onChange={(value) => {
            const updated = { ...vitals, rr: value as string };
            setVitals(updated);
            patchVitals(updated);
          }}
          readOnly={readOnly}
          placeholder={!readOnly}
        />
        <VitalInput
          type="spo2"
          label="SpO2"
          value={vitals.spo2}
          unit="%"
          normalRange={{ min: 90, max: 100 }}
          onChange={(value) => {
            const updated = { ...vitals, spo2: value as string };
            setVitals(updated);
            patchVitals(updated);
          }}
          readOnly={readOnly}
          placeholder={!readOnly}
        />
      </div>

      {/* Footer note */}
      {/* {!readOnly && (
        <div className="px-4 pb-3 flex-shrink-0">
          <p className="text-[11px] text-[#5F5E5A] text-center">
            Edit anytime — changes save automatically
          </p>
        </div>
      )} */}
    </div>
  );
}