import { Link, NavLink } from "react-router-dom";

interface AppHeaderProps {
  theme: "light" | "dark";
  onToggleTheme: () => void;
}

export function AppHeader({ theme, onToggleTheme }: AppHeaderProps) {
  return (
    <header className="app-header">
      <div className="app-header__content">
        <Link to="/cases" className="app-brand">
          Clinical Note Structuring Tool
        </Link>
        <div className="app-header__actions">
          <nav className="app-nav">
            <NavLink
              to="/cases"
              className={({ isActive }) =>
                isActive ? "app-nav__link app-nav__link--active" : "app-nav__link"
              }
            >
              Cases
            </NavLink>
            <NavLink
              to="/cases/new"
              className={({ isActive }) =>
                isActive ? "app-nav__link app-nav__link--active" : "app-nav__link"
              }
            >
              New Case
            </NavLink>
          </nav>
          <button type="button" className="theme-toggle" onClick={onToggleTheme}>
            {theme === "light" ? "Dark Mode" : "Light Mode"}
          </button>
        </div>
      </div>
    </header>
  );
}
