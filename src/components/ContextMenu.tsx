import { memo, useEffect, useRef, useState } from 'react';
import { ChevronRight } from 'lucide-react';

export interface MenuItem {
  label?: string;
  icon?: React.ReactNode;
  onClick?: () => void;
  submenu?: MenuItem[];
  divider?: boolean;
  danger?: boolean;
}

interface ContextMenuProps {
  position: { x: number; y: number };
  items: MenuItem[];
  onClose: () => void;
}

export const ContextMenu = memo(({ position, items, onClose }: ContextMenuProps) => {
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        onClose();
      }
    };

    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    // Add listeners after a small delay to prevent immediate close
    setTimeout(() => {
      document.addEventListener('mousedown', handleClickOutside);
      document.addEventListener('keydown', handleEscape);
    }, 0);

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleEscape);
    };
  }, [onClose]);

  // Adjust position to prevent overflow
  useEffect(() => {
    if (menuRef.current) {
      const menu = menuRef.current;
      const rect = menu.getBoundingClientRect();
      const viewportWidth = window.innerWidth;
      const viewportHeight = window.innerHeight;

      let adjustedX = position.x;
      let adjustedY = position.y;

      // Prevent horizontal overflow
      if (rect.right > viewportWidth) {
        adjustedX = viewportWidth - rect.width - 10;
      }

      // Prevent vertical overflow
      if (rect.bottom > viewportHeight) {
        adjustedY = viewportHeight - rect.height - 10;
      }

      menu.style.left = `${adjustedX}px`;
      menu.style.top = `${adjustedY}px`;
    }
  }, [position]);

  return (
    <div
      ref={menuRef}
      className="fixed z-50 min-w-[200px] bg-slate-800 border border-slate-700 rounded-lg shadow-2xl py-1"
      style={{
        left: position.x,
        top: position.y,
      }}
    >
      {items.map((item, index) => (
        <div key={index}>
          {item.divider ? (
            <div className="h-px bg-slate-700 my-1" />
          ) : (
            <ContextMenuItem item={item} onClose={onClose} />
          )}
        </div>
      ))}
    </div>
  );
});

ContextMenu.displayName = 'ContextMenu';

interface ContextMenuItemProps {
  item: MenuItem;
  onClose: () => void;
}

const ContextMenuItem = memo(({ item, onClose }: ContextMenuItemProps) => {
  const [showSubmenu, setShowSubmenu] = useState(false);
  const itemRef = useRef<HTMLDivElement>(null);

  const handleClick = () => {
    if (item.submenu) {
      setShowSubmenu(!showSubmenu);
    } else if (item.onClick) {
      item.onClick();
      onClose();
    }
  };

  return (
    <div className="relative" ref={itemRef}>
      <button
        onClick={handleClick}
        onMouseEnter={() => item.submenu && setShowSubmenu(true)}
        onMouseLeave={() => item.submenu && setShowSubmenu(false)}
        className={`w-full px-3 py-2 text-left text-sm flex items-center gap-2 transition-colors ${
          item.danger
            ? 'text-red-400 hover:bg-red-500/10'
            : 'text-slate-200 hover:bg-slate-700'
        }`}
      >
        {item.icon && <span className="w-4 h-4 flex-shrink-0">{item.icon}</span>}
        <span className="flex-1">{item.label}</span>
        {item.submenu && <ChevronRight className="w-4 h-4 flex-shrink-0" />}
      </button>

      {/* Submenu */}
      {item.submenu && showSubmenu && (
        <div
          className="absolute left-full top-0 ml-1 min-w-[180px] bg-slate-800 border border-slate-700 rounded-lg shadow-2xl py-1"
          onMouseEnter={() => setShowSubmenu(true)}
          onMouseLeave={() => setShowSubmenu(false)}
        >
          {item.submenu.map((subItem, subIndex) => (
            <button
              key={subIndex}
              onClick={() => {
                if (subItem.onClick) {
                  subItem.onClick();
                  onClose();
                }
              }}
              className="w-full px-3 py-2 text-left text-sm flex items-center gap-2 text-slate-200 hover:bg-slate-700 transition-colors"
            >
              {subItem.icon && <span className="w-4 h-4 flex-shrink-0">{subItem.icon}</span>}
              <span>{subItem.label}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
});

ContextMenuItem.displayName = 'ContextMenuItem';
