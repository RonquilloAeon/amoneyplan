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
        <meta name="theme-color" content="#4F46E5" />
        <link rel="apple-touch-icon" href="/icons/icon-192.png" />
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