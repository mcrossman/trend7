import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import ThemeProvider from "./components/theme/ThemeProvider";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-sans",
});

export const metadata: Metadata = {
  title: 'TrendCloset Slackbot',
  description: 'Identify and resurface historical Atlantic stories',
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={inter.variable} suppressHydrationWarning>
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: `
              (function() {
                function getTheme() {
                  const stored = localStorage.getItem('theme');
                  if (stored) {
                    return stored;
                  }
                  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
                }
                
                const theme = getTheme();
                document.documentElement.classList.toggle('dark', theme === 'dark');
              })();
            `,
          }}
        />
      </head>
      <body
        className={`${inter.variable} font-sans antialiased min-h-screen`}
      >
        <ThemeProvider>
          {children}
        </ThemeProvider>
      </body>
    </html>
  );
}
