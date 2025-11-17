import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";

// Import providers directly - they're already marked "use client" so they'll handle SSR properly
import { ThemeProvider } from "@/components/providers/theme-provider";
import { ApiClientInitializer } from "@/components/providers/api-client-initializer";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-sans",
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
});

export const metadata: Metadata = {
  title: "MCP Agent Maestro Dashboard",
  description: "Premium multi-agent system dashboard with real-time monitoring and control capabilities",
  keywords: ["agent", "mcp", "dashboard", "multi-agent", "ai", "automation"],
  authors: [{ name: "MCP Maestro Team" }],
  openGraph: {
    title: "MCP Agent Maestro - Orchestrating AI Agents Like a Symphony",
    description: "A sophisticated multi-agent orchestration framework that coordinates specialized AI agents to work harmoniously on complex software development tasks.",
    url: "https://github.com/jreakin/MCP-Agent-Maestro",
    siteName: "MCP Agent Maestro",
    images: [
      {
        url: "https://raw.githubusercontent.com/jreakin/MCP-Agent-Maestro/main/assets/images/agent-mcp-maestro-banner.png",
        width: 1640,
        height: 608,
        alt: "MCP Agent Maestro Logo",
      },
    ],
    locale: "en_US",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "MCP Agent Maestro - Orchestrating AI Agents Like a Symphony",
    description: "A sophisticated multi-agent orchestration framework that coordinates specialized AI agents.",
    images: ["https://raw.githubusercontent.com/jreakin/MCP-Agent-Maestro/main/assets/images/agent-mcp-maestro-banner.png"],
  },
};

export const viewport = {
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <meta name="theme-color" content="#BB0000" />
      </head>
      <body
        className={`${inter.variable} ${jetbrainsMono.variable} font-sans antialiased`}
        suppressHydrationWarning
      >
        <ThemeProvider>
          <ApiClientInitializer />
          {children}
        </ThemeProvider>
      </body>
    </html>
  );
}
