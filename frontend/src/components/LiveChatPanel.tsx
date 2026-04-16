import { useState, useRef, useEffect } from 'react';
import { AlertTriangle } from 'lucide-react';

import { ChatMessage } from './ChatMessage';
import { Message } from '../types';
import { useChat } from '../hooks/useChat';
import { useTranslation } from '../hooks/useTranslation';

const PLACEHOLDER_TRANSLATING = {
  EN: '...الترجمة',
  AR: 'Translation...',
} as const;

type Language = 'EN' | 'AR';

interface LiveChatPanelProps {
  sessionId?: string | null;
  hasAbnormalVitals?: boolean;
  readOnly?: boolean;
  readOnlyDate?: string;
  initialMessages?: Message[];
  onMessagesChange?: (messages: Message[]) => void;
}

export function LiveChatPanel({
  sessionId = null,
  hasAbnormalVitals = false,
  readOnly = false,
  readOnlyDate,
  initialMessages = [],
  onMessagesChange,
}: LiveChatPanelProps) {
  const [activeLanguage, setActiveLanguage] = useState<Language>('EN');
  const [inputText, setInputText] = useState('');

  const { messages, addMessage, updateMessage, saveMessage, averageConfidence, lastNurseMessage } =
    useChat({ initialMessages, onMessagesChange });

  const { translate, isTranslating, error } = useTranslation();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSendMessage = async () => {
    if (!inputText.trim() || readOnly || isTranslating) return;

    const text = inputText;
    setInputText('');
    const senderType = activeLanguage === 'EN' ? 'nurse' : 'patient';

    const optimisticMessage = addMessage({
      type: senderType,
      originalText: text,
      translatedText: PLACEHOLDER_TRANSLATING[activeLanguage],
      confidence: 0,
    });

    const result = await translate({
      source_language: activeLanguage === 'EN' ? 'en' : 'ar',
      target_language: activeLanguage === 'EN' ? 'ar' : 'en',
      source_text: text,
      session_id: text,
    });

    if (result) {
      const resolvedMessage: Partial<Message> = {
        translatedText: result.translated_text,
        confidence: result.confidence ?? 92,
      };
      updateMessage(optimisticMessage.id, resolvedMessage);

      // Persist to backend once we have both original + translation
      if (sessionId) {
        await saveMessage(sessionId, {
          ...optimisticMessage,
          ...resolvedMessage,
        } as Message);
      }
    } else {
      updateMessage(optimisticMessage.id, {
        translatedText: '⚠ Translation failed',
        confidence: 0,
      });
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const showLowConfidenceWarning =
    !readOnly && lastNurseMessage && lastNurseMessage.confidence < 80 && lastNurseMessage.confidence > 0;

  return (
    <>
      <style>{`
        @keyframes fadeSlideIn {
          from { opacity: 0; transform: translateY(6px); }
          to   { opacity: 1; transform: translateY(0); }
        }
      `}</style>

      <div className="flex flex-col h-full bg-white rounded-xl overflow-hidden">
        <ChatPanelHeader readOnly={readOnly} averageConfidence={averageConfidence} isTranslating={isTranslating} />

        {hasAbnormalVitals && !readOnly && (
          <WarningBanner message="Abnormal vital recorded — review before closing session." />
        )}
        {error && <WarningBanner message={`Translation error: ${error}`} />}

        <div className="flex-1 overflow-y-auto bg-[#F4F6F8] p-4">
          {messages.map((message) => (
            <ChatMessage
              key={message.id}
              type={message.type}
              originalText={message.originalText}
              translatedText={message.translatedText}
              confidence={message.confidence}
            />
          ))}
          <div ref={messagesEndRef} />
        </div>

        {showLowConfidenceWarning && (
          <WarningBanner message="Low confidence detected — consider rephrasing or calling an interpreter." />
        )}

        {readOnly ? (
          <ReadOnlyFooter date={readOnlyDate} />
        ) : (
          <InputBar
            activeLanguage={activeLanguage}
            inputText={inputText}
            isTranslating={isTranslating}
            onInputChange={setInputText}
            onKeyDown={handleKeyDown}
            onSend={handleSendMessage}
            onToggle={() => setActiveLanguage((l) => (l === 'EN' ? 'AR' : 'EN'))}
          />
        )}
      </div>
    </>
  );
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function ChatPanelHeader({
  readOnly,
  averageConfidence,
  isTranslating,
}: {
  readOnly: boolean;
  averageConfidence: number;
  isTranslating: boolean;
}) {
  return (
    <div className="h-[32px] bg-[#F4F6F8] px-4 flex items-center justify-between border-b border-[#E0DED6] flex-shrink-0">
      <div className="flex items-center gap-2">
        {!readOnly && (
          <>
            <span className="w-2 h-2 bg-[#A32D2D] rounded-full animate-pulse" />
            <span className="text-[12px] font-medium text-[#A32D2D]">LIVE</span>
            <span className="text-[#5F5E5A]">|</span>
          </>
        )}
        <span className="text-[12px] text-[#1A1A1A]">EN ↔ AR</span>
        {isTranslating && <span className="text-[11px] text-[#5F5E5A] italic ml-1">translating…</span>}
      </div>
      <div className="text-[11px] text-[#5F5E5A]">avg conf {averageConfidence}%</div>
    </div>
  );
}

function WarningBanner({ message }: { message: string }) {
  return (
    <div className="min-h-[28px] bg-[#BA7517]/10 border-b border-[#BA7517]/30 px-4 flex items-center gap-2 flex-shrink-0 py-1">
      <AlertTriangle className="w-3.5 h-3.5 text-[#BA7517] shrink-0" />
      <span className="text-[11px] text-[#BA7517]">{message}</span>
    </div>
  );
}

function ReadOnlyFooter({ date }: { date?: string }) {
  return (
    <div className="h-[52px] bg-[#F4F6F8] border-t border-[#E0DED6] px-4 flex items-center justify-center flex-shrink-0">
      <span className="text-[12px] text-[#5F5E5A]">Read-only — session submitted {date ?? ''}</span>
    </div>
  );
}

interface InputBarProps {
  activeLanguage: Language;
  inputText: string;
  isTranslating: boolean;
  onInputChange: (value: string) => void;
  onKeyDown: (e: React.KeyboardEvent) => void;
  onSend: () => void;
  onToggle: () => void;
}

function InputBar({ activeLanguage, inputText, isTranslating, onInputChange, onKeyDown, onSend, onToggle }: InputBarProps) {
  const isNurse = activeLanguage === 'EN';
  const accent = isNurse ? '#185FA5' : '#3B6D11';

  return (
    <div className="bg-white border-t border-[#E0DED6] px-4 py-2.5 flex items-center gap-3 flex-shrink-0">
      <button
        onClick={onToggle}
        title="Switch speaker"
        className="flex-shrink-0 flex flex-col items-center justify-center w-[56px] h-[44px] rounded-xl border-2 transition-all duration-200 active:scale-95 select-none"
        style={{ borderColor: accent, backgroundColor: `${accent}10` }}
      >
        <span className="text-[10px] font-black uppercase leading-none" style={{ color: accent }}>
          {isNurse ? 'EN' : 'AR'}
        </span>
        <span className="text-[10px] leading-none opacity-40" style={{ color: accent }}>⇅</span>
        <span className="text-[10px] font-medium uppercase leading-none text-[#9E9C97]">
          {isNurse ? 'AR' : 'EN'}
        </span>
      </button>

      <div className="flex-1 relative">
        <span
          className="absolute -top-[9px] left-3 px-2 py-0.5 text-[9px] font-black uppercase rounded-full text-white leading-none z-10"
          style={{ backgroundColor: accent }}
        >
          {isNurse ? 'Clinician' : 'Patient'}
        </span>
        <input
          type="text"
          value={inputText}
          onChange={(e) => onInputChange(e.target.value)}
          onKeyDown={onKeyDown}
          disabled={isTranslating}
          dir={isNurse ? 'ltr' : 'rtl'}
          placeholder={isNurse ? 'Type clinician message…' : 'اكتب رسالة المريض هنا…'}
          className="w-full h-[40px] px-4 rounded-xl border-2 text-[14px] transition-all duration-200 outline-none bg-white disabled:opacity-60"
          style={{ borderColor: accent }}
          onFocus={(e) => (e.currentTarget.style.boxShadow = `0 0 0 3px ${accent}30`)}
          onBlur={(e) => (e.currentTarget.style.boxShadow = 'none')}
        />
      </div>

      <button
        onClick={onSend}
        disabled={isTranslating || !inputText.trim()}
        className="h-[40px] px-5 rounded-xl text-white text-[13px] font-bold shadow-sm transition-all active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed flex-shrink-0"
        style={{ backgroundColor: accent }}
      >
        {isTranslating ? (
          <span className="w-3 h-3 border-2 border-white/30 border-t-white rounded-full animate-spin block" />
        ) : (
          'Send →'
        )}
      </button>
    </div>
  );
}