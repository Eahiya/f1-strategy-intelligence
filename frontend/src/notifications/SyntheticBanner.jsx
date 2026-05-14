import React from 'react';
import { X } from 'lucide-react';
import { useSyntheticBanner } from '../contexts/SyntheticBannerContext';

const SyntheticBanner = () => {
  const { visible, message, hideBanner } = useSyntheticBanner();
  if (!visible) return null;
  return (
    <div className="fixed top-0 left-0 right-0 z-50 bg-[#e10600] text-white shadow-md flex items-center justify-between px-4 py-2">
      <span className="text-sm">{message}</span>
      <button aria-label="Close" onClick={hideBanner} className="p-1 rounded-full hover:bg-white/20">
        <X className="w-4 h-4" />
      </button>
    </div>
  );
};

export default SyntheticBanner;
