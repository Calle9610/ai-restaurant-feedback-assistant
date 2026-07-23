import Link from 'next/link';
import { Badge } from '@/components/ui/badge';

type AppHeaderProps = {
  activeHref: '/' | '/insights';
};

export default function AppHeader({ activeHref }: AppHeaderProps) {
  const navItem = (href: '/' | '/insights', label: string) => {
    const isActive = activeHref === href;
    return (
      <Link
        href={href}
        className={`px-3 py-1.5 text-sm rounded-md font-medium transition-colors cursor-pointer ${
          isActive
            ? 'bg-primary text-primary-foreground'
            : 'text-muted-foreground hover:text-foreground'
        }`}
      >
        {label}
      </Link>
    );
  };

  return (
    <header className="bg-card border-b border-border px-6 py-4">
      <div className="max-w-5xl mx-auto flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="text-xl font-mono font-bold tracking-tight text-foreground">
            Gästpuls
          </span>
          <Badge variant="secondary" className="text-xs">Demo</Badge>
        </div>
        <nav className="flex gap-1">
          {navItem('/', 'Översikt')}
          {navItem('/insights', 'Insikter')}
        </nav>
      </div>
    </header>
  );
}
