'use client';

import { useEffect } from 'react';

export default function ThemeProvider({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    // Set initial theme
    const setTheme = () => {
      const stored = localStorage.getItem('theme');
      if (stored) {
        document.documentElement.classList.toggle('dark', stored === 'dark');
      } else {
        const isDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        document.documentElement.classList.toggle('dark', isDark);
      }
    };

    setTheme();

    // Listen for system theme changes
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    const handleChange = (e: MediaQueryListEvent) => {
      const stored = localStorage.getItem('theme');
      if (!stored) {
        document.documentElement.classList.toggle('dark', e.matches);
      }
    };

    mediaQuery.addEventListener('change', handleChange);

    return () => {
      mediaQuery.removeEventListener('change', handleChange);
    };
  }, []);

  return <>{children}</>;
}
