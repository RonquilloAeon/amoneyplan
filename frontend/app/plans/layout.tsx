export default function PlansLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <main className="container py-10">
      {children}
    </main>
  );
} 