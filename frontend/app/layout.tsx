export const metadata = {
  title: 'Story Thread Surfacing',
  description: 'Identify and resurface historical Atlantic stories',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-background">
        {children}
      </body>
    </html>
  );
}
