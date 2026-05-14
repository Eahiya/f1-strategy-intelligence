/**
 * F1 Strategy Platform v4.0 - Mobile Bottom Navigation
 * Touch-optimized navigation for mobile devices
 */
import React from 'react';
import { NavLink } from 'react-router-dom';
import { 
  LayoutDashboard, 
  Play, 
  Trophy, 
  Settings,
  Zap
} from 'lucide-react';

const MobileNav = () => {
  const navItems = [
    { 
      to: '/', 
      icon: LayoutDashboard, 
      label: 'Dashboard'
    },
    { 
      to: '/simulate', 
      icon: Play, 
      label: 'Simulate'
    },
    { 
      to: '/elite', 
      icon: Zap, 
      label: 'Elite'
    },
    { 
      to: '/results', 
      icon: Trophy, 
      label: 'Results'
    },
    { 
      to: '/settings', 
      icon: Settings, 
      label: 'Settings'
    }
  ];

  return (
    <nav className="mobile-nav">
      {navItems.map((item) => (
        <NavLink
          key={item.to}
          to={item.to}
          className={({ isActive }) => 
            `mobile-nav-item ${isActive ? 'active' : ''}`
          }
          end={item.to === '/'}
        >
          <item.icon strokeWidth={2} />
          <span>{item.label}</span>
        </NavLink>
      ))}
    </nav>
  );
};

export default MobileNav;
