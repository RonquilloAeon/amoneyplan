'use client';

import Link from 'next/link';
import Image from 'next/image';
import { usePathname } from 'next/navigation';
import { useAuth } from '@/lib/auth/AuthContext';
import { Button } from '@/components/ui/button';

export function Navbar() {
  const pathname = usePathname();
  const { logout, isAuthenticated } = useAuth();

  if (!isAuthenticated) return null;

  return (
    <nav className="border-b">
      <div className="container max-w-6xl mx-auto flex justify-between items-center p-4">
        <div className="flex items-center">
          <Link href="/" className="flex items-center font-bold text-xl mr-6 font-manrope" style={{ color: '#1D33DD' }}>
            <Image src="/icons/fortana-logo.svg" alt="Fortana Logo" width={24} height={24} className="mr-2" />
            fortana
          </Link>
          <div className="flex gap-4">
            <Link 
              href="/plans" 
              className={`${pathname.startsWith('/plans') ? 'font-semibold border-b-2 border-blue-500' : ''}`}
            >
              Plans
            </Link>
            <Link 
              href="/accounts" 
              className={`${pathname.startsWith('/accounts') ? 'font-semibold border-b-2 border-blue-500' : ''}`}
            >
              Accounts
            </Link>
          </div>
        </div>
        <Button variant="ghost" onClick={logout}>
          Logout
        </Button>
      </div>
    </nav>
  );
} 