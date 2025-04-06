import { Inter } from 'next/font/google';
import { ApolloWrapper } from '@/lib/apollo/ApolloWrapper';
import { AuthProvider } from '@/lib/auth/AuthProvider';
import './globals.css';

const inter = Inter({ subsets: ['latin'] });

export const metadata = {
  title: 'AMoneyPlan',
  description: 'Plan your financial future with AMoneyPlan',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <AuthProvider>
          <ApolloWrapper>{children}</ApolloWrapper>
        </AuthProvider>
      </body>
    </html>
  );
} 