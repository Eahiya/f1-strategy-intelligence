import React, { createContext, useContext, useEffect, useState } from 'react';

const SyntheticBannerContext = createContext({ visible: false, message: '' });

export const SyntheticBannerProvider = ({ children }) => {
  const [visible, setVisible] = useState(false);
  const [message, setMessage] = useState('Synthetic data loaded');

  const showBanner = (msg) => {
    setMessage(msg || 'Synthetic data loaded');
    setVisible(true);
  };

  const hideBanner = () => setVisible(false);

  useEffect(() => {
    const handler = (e) => {
      const msg = e?.detail?.message || 'Synthetic data loaded';
      showBanner(msg);
    };
    window.addEventListener('synthetic-data', handler);
    return () => window.removeEventListener('synthetic-data', handler);
  }, []);

  return (
    <SyntheticBannerContext.Provider value={{ visible, message, showBanner, hideBanner }}>
      {children}
    </SyntheticBannerContext.Provider>
  );
};

export const useSyntheticBanner = () => useContext(SyntheticBannerContext);
