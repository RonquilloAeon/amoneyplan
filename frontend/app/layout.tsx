import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { Providers } from './providers';
import { Navbar } from '@/components/Navbar';
import { ServiceWorkerEffect } from '@/components/ServiceWorkerEffect';

const inter = Inter({ subsets: ['latin'] });

const appName = 'Fortana Money Planner';

export const metadata: Metadata = {
  title: {
    default: appName,
    template: `%s | ${appName}`,
  },
  description: 'Plan your money, not your budget.',
  manifest: '/manifest.json',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <meta name="theme-color" content="#1D33DD" />
        <meta name="apple-mobile-web-app-capable" content="yes" />
        <link rel="icon" type="image/png" href="/icons/favicon-96x96.png" sizes="96x96" />
        <link rel="icon" type="image/svg+xml" href="/icons/favicon.svg" />
        <link rel="shortcut icon" href="/icons/favicon.ico" />
        <link rel="apple-touch-icon" sizes="180x180" href="/icons/apple-touch-icon.png" />
        <meta name="apple-mobile-web-app-title" content="Fortana" />
      </head>
      <body className={inter.className}>
        <Providers>
          <ServiceWorkerEffect />
          <Navbar />
          <div className="container max-w-6xl mx-auto px-4 py-8">
            {children}
          </div>
        </Providers>
      </body>
    </html>
  );
} 