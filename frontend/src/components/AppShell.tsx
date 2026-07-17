import React, { useState, useEffect } from "react";
import { Link, useLocation } from "react-router-dom";
import { Terminal, Shield, Moon, Sun, Home } from "lucide-react";
import { useTheme } from "../core/providers";

interface AppShellProps {
  children: React.ReactNode;
  leftSidebarContent?: React.ReactNode;
  rightSidebarContent?: React.ReactNode;
  showLeftSidebar?: boolean;
  showRightSidebar?: boolean;
}

export function AppShell({
  children,
  leftSidebarContent,
  rightSidebarContent,
  showLeftSidebar = false,
  showRightSidebar = false,
}: AppShellProps) {
  const location = useLocation();
  const { theme, toggleTheme } = useTheme();

  // Column width states
  const [leftWidth, setLeftWidth] = useState(260);
  const [rightWidth, setRightWidth] = useState(320);

  // Resize state tracking
  const [isResizingLeft, setIsResizingLeft] = useState(false);
  const [isResizingRight, setIsResizingRight] = useState(false);

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (isResizingLeft) {
        const newWidth = Math.max(200, Math.min(400, e.clientX));
        setLeftWidth(newWidth);
      }
      if (isResizingRight) {
        const newWidth = Math.max(240, Math.min(480, window.innerWidth - e.clientX));
        setRightWidth(newWidth);
      }
    };

    const handleMouseUp = () => {
      setIsResizingLeft(false);
      setIsResizingRight(false);
      document.body.style.cursor = "default";
      document.body.style.userSelect = "auto";
    };

    if (isResizingLeft || isResizingRight) {
      document.body.style.cursor = "col-resize";
      document.body.style.userSelect = "none";
      window.addEventListener("mousemove", handleMouseMove);
      window.addEventListener("mouseup", handleMouseUp);
    }

    return () => {
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("mouseup", handleMouseUp);
    };
  }, [isResizingLeft, isResizingRight]);

  const activePath = location.pathname;

  return (
    <div className="min-h-screen flex flex-col bg-background text-slate-100 font-sans selection:bg-brand selection:text-white transition-colors duration-150">
      {/* Top Header Navigation */}
      <header className="h-14 border-b border-border px-6 flex items-center justify-between bg-slate-900/60 backdrop-blur-md sticky top-0 z-50">
        <div className="flex items-center space-x-6">
          <Link to="/" className="flex items-center space-x-3 group">
            <div className="w-8 h-8 rounded-lg bg-brand flex items-center justify-center text-white shadow-md shadow-brand/20 group-hover:scale-105 transition-transform duration-100">
              <Shield className="w-4 h-4" />
            </div>
            <span className="font-semibold tracking-wider text-sm font-mono text-slate-100 group-hover:text-white transition-colors">
              TRUTHENGINE
            </span>
          </Link>
          <nav className="hidden md:flex space-x-1">
            <Link
              to="/"
              className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                activePath === "/"
                  ? "bg-slate-800 text-white"
                  : "text-slate-400 hover:text-white hover:bg-slate-800/40"
              }`}
            >
              <span className="flex items-center space-x-1.5">
                <Home className="w-3.5 h-3.5" />
                <span>Dashboard</span>
              </span>
            </Link>
          </nav>
        </div>

        <div className="flex items-center space-x-4">
          <button
            onClick={toggleTheme}
            className="p-2 rounded-md hover:bg-slate-800/80 text-slate-400 hover:text-white transition-colors"
            title="Toggle Theme"
          >
            {theme === "dark" ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
          </button>
          <div className="hidden lg:flex items-center space-x-2 px-2.5 py-1 rounded bg-slate-800/60 border border-border text-[10px] font-mono text-slate-400">
            <Terminal className="w-3 h-3 text-brand" />
            <span>Agent Orchestrator Active</span>
          </div>
        </div>
      </header>

      {/* Main Workspace Column splits */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left panel */}
        {showLeftSidebar && leftSidebarContent && (
          <aside
            style={{ width: `${leftWidth}px` }}
            className="border-r border-border bg-slate-900/40 flex flex-col shrink-0 overflow-y-auto select-none"
          >
            {leftSidebarContent}
          </aside>
        )}

        {/* Left Resizer Drag Bar */}
        {showLeftSidebar && leftSidebarContent && (
          <div
            onMouseDown={() => setIsResizingLeft(true)}
            className="w-1 hover:w-1.5 bg-transparent hover:bg-brand/40 cursor-col-resize transition-all duration-100 shrink-0 z-40"
          />
        )}

        {/* Center Canvas */}
        <main className="flex-1 flex flex-col overflow-y-auto bg-slate-950/20">
          {children}
        </main>

        {/* Right Resizer Drag Bar */}
        {showRightSidebar && rightSidebarContent && (
          <div
            onMouseDown={() => setIsResizingRight(true)}
            className="w-1 hover:w-1.5 bg-transparent hover:bg-brand/40 cursor-col-resize transition-all duration-100 shrink-0 z-40"
          />
        )}

        {/* Right panel */}
        {showRightSidebar && rightSidebarContent && (
          <aside
            style={{ width: `${rightWidth}px` }}
            className="border-l border-border bg-slate-900/40 flex flex-col shrink-0 overflow-y-auto"
          >
            {rightSidebarContent}
          </aside>
        )}
      </div>
    </div>
  );
}
