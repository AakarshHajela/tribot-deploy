import { ConfidenceBadge } from './ConfidenceBadge';

interface ChatMessageProps {
  type: 'nurse' | 'patient';
  originalText: string;
  translatedText: string;
  confidence: number;
  senderName?: string;
  showQuickReplies?: boolean;
}

export function ChatMessage({
  type,
  originalText,
  translatedText,
  confidence,
  senderName,
}: ChatMessageProps) {
  const isNurse = type === 'nurse';

  const displayName = senderName ?? (isNurse ? 'Clinician' : 'Patient');
  const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

  const bubble = isNurse
    ? 'bg-[#185FA5] text-white'
    : 'bg-[#3B6D11] text-white';

  const translationBlock = isNurse
    ? 'bg-[#0e3d6e]/40 text-blue-100'
    : 'bg-[#2a4f0c]/40 text-green-100';

  const nameColor = isNurse ? 'text-[#185FA5]' : 'text-[#3B6D11]';

  const isPlaceholder = translatedText.startsWith('...') || translatedText.startsWith('Translation') || translatedText === '⚠ Translation failed';
  const isFailed = translatedText === '⚠ Translation failed';

  return (
    <div
      className={`flex ${isNurse ? 'justify-end' : 'justify-start'} mb-4 animate-[fadeSlideIn_0.18s_ease-out]`}
      style={{ animationFillMode: 'both' }}
    >
      <div className={`max-w-[78%] flex flex-col ${isNurse ? 'items-end' : 'items-start'}`}>

        <div className={`flex items-center gap-1.5 mb-1 px-1 ${isNurse ? 'flex-row-reverse' : 'flex-row'}`}>
          <span className={`text-[11px] font-semibold ${nameColor}`}>{displayName}</span>
          <span className="text-[10px] text-[#9E9C97]">{timestamp}</span>
        </div>

        <div className={`w-full rounded-2xl overflow-hidden shadow-sm ${bubble} ${isNurse ? 'rounded-tr-sm' : 'rounded-tl-sm'}`}>

          <div className="px-4 pt-3 pb-2">
            <p
              className="text-[14px] leading-relaxed font-medium"
              dir={isNurse ? 'ltr' : 'rtl'}
            >
              {originalText}
            </p>
          </div>

          {/* <div className={`mx-4 border-t ${isNurse ? 'border-white/20' : 'border-white/20'}`} /> */}

          <div className={`px-4 pt-2 pb-3 ${translationBlock}`}>
            {/* <p
              className={`text-[10px] uppercase font-bold tracking-widest mb-1 opacity-60`}
            >
              {isNurse ? 'AR' : 'EN'}
            </p> */}
            <p
              className={`text-[13px] leading-relaxed ${isFailed ? 'opacity-60' : ''}`}
              dir={isNurse ? 'rtl' : 'ltr'}
            >
              {isPlaceholder && !isFailed ? (
                <span className="flex items-center gap-1.5 opacity-70">
                  <span className="flex gap-0.5">
                    {[0, 1, 2].map((i) => (
                      <span
                        key={i}
                        className="w-1.5 h-1.5 rounded-full bg-current animate-bounce"
                        style={{ animationDelay: `${i * 0.15}s` }}
                      />
                    ))}
                  </span>
                  <span className="text-[12px]">Translating…</span>
                </span>
              ) : (
                translatedText
              )}
            </p>
          </div>

          {/* {!isPlaceholder && confidence > 0 && (
            <div className={`px-3 pb-2 flex ${isNurse ? 'justify-end' : 'justify-start'}`}>
              <ConfidenceBadge confidence={confidence} />
            </div>
          )} */}
        </div>
      </div>
    </div>
  );
}