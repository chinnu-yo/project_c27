import './layout.css';

export const metadata = {
  title: 'Agentic Workspace',
  description: 'B2B Agentic System of Action Platform',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
