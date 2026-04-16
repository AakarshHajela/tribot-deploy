interface ConfidenceBadgeProps {
  confidence: number;
  variant?: 'high' | 'medium' | 'low';
}

export function ConfidenceBadge({ confidence, variant }: ConfidenceBadgeProps) {
  const actualVariant = variant || (
    confidence >= 90 ? 'high' : confidence >= 75 ? 'medium' : 'low'
  );

  const styles = {
    high: 'bg-[#3B6D11]/10 text-[#3B6D11] border-[#3B6D11]/30',
    medium: 'bg-[#BA7517]/10 text-[#BA7517] border-[#BA7517]/30',
    low: 'bg-[#A32D2D]/10 text-[#A32D2D] border-[#A32D2D]/30'
  };

  const icon = {
    high: '✓',
    medium: '⚠',
    low: '⚠'
  };

  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-medium border ${styles[actualVariant]}`}>
      {icon[actualVariant]} {confidence}%
    </span>
  );
}
