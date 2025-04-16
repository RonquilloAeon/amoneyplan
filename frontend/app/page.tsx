import { redirect } from 'next/navigation';

export default function HomePage() {
  // Redirect to the plans page
  redirect('/plans');
} 