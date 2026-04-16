import { MessageCircle, Heart, ClipboardList } from 'lucide-react';

type Tab = 'chat' | 'vitals' | 'ats';

interface MobileNavProps {
  activeTab: Tab;
  onTabChange: (tab: Tab) => void;
}

export function MobileNav({ activeTab, onTabChange }: MobileNavProps) {
  return (
    <div className="md:hidden fixed bottom-0 left-0 right-0 h-[60px] bg-white border-t border-[#E0DED6] z-40 flex items-center justify-around px-4">
      <button
        onClick={() => onTabChange('chat')}
        className={`flex flex-col items-center gap-1 px-6 py-2 rounded-md transition-colors ${
          activeTab === 'chat' ? 'text-[#185FA5]' : 'text-[#5F5E5A]'
        }`}
      >
        <MessageCircle className="w-5 h-5" />
        <span className="text-[10px] font-medium">Chat</span>
      </button>
      <button
        onClick={() => onTabChange('vitals')}
        className={`flex flex-col items-center gap-1 px-6 py-2 rounded-md transition-colors ${
          activeTab === 'vitals' ? 'text-[#185FA5]' : 'text-[#5F5E5A]'
        }`}
      >
        <Heart className="w-5 h-5" />
        <span className="text-[10px] font-medium">Vitals</span>
      </button>
      <button
        onClick={() => onTabChange('ats')}
        className={`flex flex-col items-center gap-1 px-6 py-2 rounded-md transition-colors ${
          activeTab === 'ats' ? 'text-[#185FA5]' : 'text-[#5F5E5A]'
        }`}
      >
        <ClipboardList className="w-5 h-5" />
        <span className="text-[10px] font-medium">ATS</span>
      </button>
    </div>
  );
}
