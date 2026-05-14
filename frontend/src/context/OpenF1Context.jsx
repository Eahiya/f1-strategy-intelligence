import React, { createContext, useContext } from 'react';
import useOpenF1 from '../hooks/useOpenF1';

const OpenF1Context = createContext(null);

export const OpenF1Provider = ({ children }) => {
  const openF1State = useOpenF1();

  return (
    <OpenF1Context.Provider value={openF1State}>
      {children}
    </OpenF1Context.Provider>
  );
};

export const useOpenF1Context = () => {
  const context = useContext(OpenF1Context);
  if (!context) {
    throw new Error('useOpenF1Context must be used within an OpenF1Provider');
  }
  return context;
};
