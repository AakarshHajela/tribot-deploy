import { X, ArrowLeftRight, Languages, Loader2 } from 'lucide-react';
import { useState } from 'react';
import { ConfidenceBadge } from './ConfidenceBadge';
import { useTranslation } from '../hooks/useTranslation';

interface QuickTranslateDrawerProps {
  isOpen: boolean;
  onClose: () => void;
}

export function QuickTranslateDrawer({ isOpen, onClose }: QuickTranslateDrawerProps) {
  const { translate, isTranslating, error } = useTranslation();

  const [sourceLanguage, setSourceLanguage] = useState('English');
  const [targetLanguage, setTargetLanguage] = useState('Arabic');
  const [inputText, setInputText] = useState('');
  const [outputText, setOutputText] = useState('');
  const [confidence, setConfidence] = useState(0);

  const handleSwapLanguages = () => {
    setSourceLanguage(targetLanguage);
    setTargetLanguage(sourceLanguage);
    const tempInput = inputText;
    setInputText(outputText);
    setOutputText(tempInput);
  };

  const handleTranslate = async () => {
    if (!inputText.trim()) return;

    try {
      const result = await translate({
        source_language: sourceLanguage,
        target_language: targetLanguage,
        source_text: inputText,
        patient_id: "000",
      });

      if (result) {
        setOutputText(result.translated_text);
        setConfidence(result.confidence || 0.95);
      }
    } catch (err) {
      setOutputText('⚠ Translation failed');
    }
  };

  const handleDiscard = () => {
    setInputText('');
    setOutputText('');
    setConfidence(0);
    onClose();
  };

  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-black/40 z-[60] transition-opacity"
        onClick={handleDiscard}
      ></div>

      {/* Slide-over drawer */}
      <div className={`fixed top-0 right-0 h-full w-[380px] bg-white shadow-2xl z-[61] transform transition-transform duration-300 ${
        isOpen ? 'translate-x-0' : 'translate-x-full'
      }`}>
        <div className="h-full flex flex-col p-5">
          {/* Header */}
          <div className="flex items-start justify-between mb-6">
            <div>
              <h2 className="text-[18px] font-bold text-[#1A1A1A]">Quick Translate</h2>
              <p className="text-[12px] text-[#5F5E5A] mt-1">
                One-off translation for immediate clinical use
              </p>
            </div>
            <button onClick={handleDiscard} className="p-1 hover:bg-gray-100 rounded-full transition-colors">
              <X className="w-5 h-5 text-[#5F5E5A]" />
            </button>
          </div>

          {/* Language Swap Control */}
          <div className="flex items-center justify-between mb-6 p-3 bg-[#F8F9FA] rounded-xl border border-[#E0DED6]">
            <div className="flex flex-col items-center flex-1">
              <span className="text-[10px] uppercase text-[#5F5E5A] mb-1">From</span>
              <span className="font-bold text-[#185FA5]">{sourceLanguage}</span>
            </div>

            <button
              onClick={handleSwapLanguages}
              className="w-10 h-10 rounded-full bg-white border border-[#E0DED6] flex items-center justify-center text-[#185FA5] hover:shadow-md active:scale-95 transition-all"
            >
              <ArrowLeftRight className="w-5 h-5" />
            </button>

            <div className="flex flex-col items-center flex-1">
              <span className="text-[10px] uppercase text-[#5F5E5A] mb-1">To</span>
              <span className="font-bold text-[#185FA5]">{targetLanguage}</span>
            </div>
          </div>

          {/* Input Area */}
          <div className="flex-1 flex flex-col gap-4 min-h-0">
            <div className="flex-[4] flex flex-col">
              <textarea
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                className="flex-1 w-full p-4 border border-[#E0DED6] rounded-xl text-[15px] resize-none focus:ring-2 focus:ring-[#185FA5] focus:border-transparent outline-none bg-white shadow-sm"
                placeholder={`Enter ${sourceLanguage} text here...`}
              />
            </div>

            {/* ACTION BUTTON */}
            <button
              onClick={handleTranslate}
              disabled={isTranslating || !inputText.trim()}
              className="w-full py-3.5 bg-[#185FA5] text-white rounded-xl font-bold flex items-center justify-center gap-2 hover:bg-[#144f8a] disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-blue-900/10 transition-all active:scale-[0.98]"
            >
              {isTranslating ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <Languages className="w-5 h-5" />
              )}
              {isTranslating ? 'Translating...' : 'Translate Now'}
            </button>

            {/* Output Area */}
            <div className="flex-[4] flex flex-col">
              <div className={`flex-1 w-full p-4 border-2 rounded-xl text-[15px] overflow-y-auto transition-colors ${
                error ? 'border-red-200 bg-red-50' : 'border-[#3B6D11] bg-[#3B6D11]/5'
              }`}>
                {error ? (
                  <div className="text-red-600 flex flex-col gap-1">
                    <span className="font-bold">Error</span>
                    <span className="text-sm">{error}</span>
                  </div>
                ) : outputText ? (
                  <div className="flex flex-col h-full justify-between">
                    <div className="text-[#1A1A1A] leading-relaxed">{outputText}</div>
                    {confidence > 0 && (
                      <div className="mt-4 pt-3 border-t border-[#3B6D11]/20">
                        <ConfidenceBadge confidence={confidence} />
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="h-full flex items-center justify-center text-[#5F5E5A] italic text-sm text-center px-4">
                    Translated text will appear here after clicking the button above.
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Bottom Actions */}
          <div className="mt-6">
            <button
              onClick={handleDiscard}
              className="w-full py-3 border border-[#E0DED6] text-[#5F5E5A] rounded-xl text-[14px] font-medium hover:bg-gray-50 transition-colors"
            >
              Close Drawer
            </button>
          </div>
        </div>
      </div>
    </>
  );
}