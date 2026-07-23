"use client";

import Link from 'next/link';
import { useRouter, usePathname } from 'next/navigation';
import { useWorkspaceStore } from '../store';

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const { clientId, clearSession } = useWorkspaceStore();
  const router = useRouter();
  const pathname = usePathname();

  const handleLogout = () => {
    clearSession();
    router.push('/login');
  };

  const navItems = [
    { name: 'Dashboard Hub', href: '/dashboard' },
    { name: 'Memory Approval Feed', href: '/dashboard/memory' },
    { name: 'Workspace Canvas', href: `/dashboard/workspace/${clientId}` }
  ];

  return (
    <div style={{ display: 'flex', minHeight: '100vh', backgroundColor: 'var(--bg-obsidian)' }}>
      {/* Sidebar Navigation Panel */}
      <aside style={{
        width: '280px',
        borderRight: '1px solid var(--border-glass)',
        padding: '32px 24px',
        display: 'flex',
        flexDirection: 'column',
        gap: '40px',
        background: 'linear-gradient(to bottom, var(--bg-card), transparent)'
      }}>
        <div>
          <h2 style={{
            fontSize: '20px',
            fontWeight: 700,
            background: 'var(--color-gemini-gradient)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            marginBottom: '4px'
          }}>
            Agentic Workspace
          </h2>
          <span style={{ fontSize: '12px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.1em' }}>
            System of Action
          </span>
        </div>

        {/* Tenant status box */}
        <div className="glass-card" style={{ padding: '16px', borderRadius: '12px' }}>
          <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Active Tenant</div>
          <div style={{ fontSize: '14px', fontWeight: 600, color: 'var(--color-teal)', marginTop: '4px' }}>{clientId}</div>
        </div>

        {/* Nav Links */}
        <nav style={{ display: 'flex', flexDirection: 'column', gap: '8px', flexGrow: 1 }}>
          {navItems.map((item) => {
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                style={{
                  display: 'block',
                  padding: '12px 16px',
                  borderRadius: '8px',
                  textDecoration: 'none',
                  fontSize: '14px',
                  fontWeight: 500,
                  color: isActive ? 'var(--text-primary)' : 'var(--text-secondary)',
                  background: isActive ? 'hsla(262, 80%, 65%, 0.15)' : 'transparent',
                  border: isActive ? '1px solid hsla(262, 80%, 65%, 0.2)' : '1px solid transparent',
                  transition: 'var(--transition-smooth)'
                }}
              >
                {item.name}
              </Link>
            );
          })}
        </nav>

        {/* Logout Control Button */}
        <button
          onClick={handleLogout}
          className="btn-secondary"
          style={{ width: '100%', padding: '10px 16px', fontSize: '14px' }}
        >
          Sign Out
        </button>
      </aside>

      {/* Main Content Pane */}
      <main style={{ flexGrow: 1, padding: '40px', overflowY: 'auto', maxHeight: '100vh' }}>
        {children}
      </main>
    </div>
  );
}
