import type { Metadata } from "next";
import localFont from "next/font/local";
import "./globals.css";

const geistSans = localFont({
  src: "./fonts/GeistVF.woff",
  variable: "--font-geist-sans",
  weight: "100 900",
});

export const metadata: Metadata = {
  title: "MetraSure — NAWI Test Report System",
  description: "Automated NAWI Testing, Compliance & Test Report Generation per OIML R-76",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${geistSans.variable} font-sans bg-slate-50 text-gray-900 antialiased`}>
        <nav className="bg-slate-900 text-white shadow-lg border-b border-slate-700">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between h-14">
              <div className="flex items-center space-x-8">
                <a href="/dashboard" className="flex items-center space-x-2">
                  <div className="w-7 h-7 bg-blue-500 rounded flex items-center justify-center">
                    <span className="text-white font-bold text-xs">M</span>
                  </div>
                  <span className="font-bold text-base tracking-tight">MetraSure</span>
                </a>
                <div className="hidden sm:flex items-center space-x-1">
                  <a href="/dashboard" className="text-slate-300 hover:text-white hover:bg-slate-800 px-3 py-1.5 rounded text-sm font-medium transition-colors">Dashboard</a>
                  <a href="/instruments" data-tour="instrument-registry" className="text-slate-300 hover:text-white hover:bg-slate-800 px-3 py-1.5 rounded text-sm font-medium transition-colors">Instruments</a>
                  <a href="/tests" className="text-slate-300 hover:text-white hover:bg-slate-800 px-3 py-1.5 rounded text-sm font-medium transition-colors">Tests</a>
                  <a href="/history" className="text-slate-300 hover:text-white hover:bg-slate-800 px-3 py-1.5 rounded text-sm font-medium transition-colors">History</a>
                  <div className="w-px h-5 bg-slate-700 mx-2"></div>
                  <a href="/admin/rules" className="text-indigo-300 hover:text-white hover:bg-indigo-900/50 px-3 py-1.5 rounded text-sm font-medium transition-colors flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-indigo-500"></span>
                    Rule Engine
                  </a>
                </div>
              </div>
              <div className="flex items-center gap-4">
                <span className="text-xs text-slate-400">OIML R-76 Compliance</span>
                <button id="tour-help-btn" className="text-xs font-semibold px-2 py-1 bg-slate-800 hover:bg-slate-700 rounded text-slate-300 transition-colors">Help & Tour</button>
              </div>
            </div>
          </div>
        </nav>
        <main className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
          {children}
        </main>
      </body>
    </html>
  );
}
