import { useState, useCallback } from 'react';
import { Message } from '../types';
import { postMessage } from '../api/triageApi';

const DEFAULT_MESSAGES: Message[] = [];

interface UseChatOptions {
  initialMessages?: Message[];
  onMessagesChange?: (messages: Message[]) => void;
}

interface UseChatReturn {
  messages: Message[];
  addMessage: (message: Omit<Message, 'id'>) => Message;
  updateMessage: (id: string, updates: Partial<Message>) => void;
  // Persists a fully-resolved message 
  saveMessage: (sessionId: string, message: Message) => Promise<void>;
  
  averageConfidence: number;
  lastNurseMessage: Message | undefined;
}

export function useChat({
  initialMessages,
  onMessagesChange,
}: UseChatOptions = {}): UseChatReturn {
  const [messages, setMessages] = useState<Message[]>(
    initialMessages && initialMessages.length > 0 ? initialMessages : DEFAULT_MESSAGES,
  );

  const addMessage = useCallback(
    (message: Omit<Message, 'id'>): Message => {
      const newMessage: Message = { ...message, id: Date.now().toString() };
      setMessages((prev) => {
        const next = [...prev, newMessage];
        onMessagesChange?.(next);
        return next;
      });
      return newMessage;
    },
    [onMessagesChange],
  );

  const updateMessage = useCallback(
    (id: string, updates: Partial<Message>) => {
      setMessages((prev) => {
        const next = prev.map((m) => (m.id === id ? { ...m, ...updates } : m));
        onMessagesChange?.(next);
        return next;
      });
    },
    [onMessagesChange],
  );

  const saveMessage = useCallback(async (sessionId: string, message: Message) => {
    try {
      await postMessage(sessionId, {
        sender: message.type === 'nurse' ? 'clinician' : 'patient',
        original_text: message.originalText,
        source_language: message.type === 'nurse' ? 'en' : 'ar',
        target_language: message.type === 'nurse' ? 'ar' : 'en',
        translated_text: message.translatedText,
        confidence: message.confidence,
      });
    } catch {
      // Non-fatal — message already visible in UI, backend sync is best-effort
    }
  }, []);

  const averageConfidence =
    messages.length > 0
      ? Math.round(messages.reduce((sum, m) => sum + m.confidence, 0) / messages.length)
      : 0;

  const lastNurseMessage = [...messages].reverse().find((m) => m.type === 'nurse');

  return { messages, addMessage, updateMessage, saveMessage, averageConfidence, lastNurseMessage };
}