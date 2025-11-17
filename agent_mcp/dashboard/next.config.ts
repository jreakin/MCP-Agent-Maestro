import type { NextConfig } from "next";

// Bundle analyzer
const withBundleAnalyzer = require('@next/bundle-analyzer')({
  enabled: process.env.ANALYZE === 'true',
})

const nextConfig: NextConfig = {
  // Enable standalone output for Docker (production) or normal dev mode
  output: process.env.DOCKER_BUILD === 'true' ? 'standalone' : undefined,
  
  // Enable static export for serving through Python backend (only if not Docker)
  // output: process.env.NODE_ENV === 'production' && process.env.DOCKER_BUILD !== 'true' ? 'export' : undefined,
  
  // Configure output directory
  distDir: process.env.NODE_ENV === 'production' && process.env.DOCKER_BUILD !== 'true' ? '../static' : '.next',
  
  // Disable image optimization for static export
  images: {
    unoptimized: true
  },
  
  // Configure trailing slash for better static serving
  trailingSlash: true,
  
  // Base path configuration (can be updated if needed)
  basePath: '',
  
  // Asset prefix for CDN support if needed later
  assetPrefix: '',

  eslint: {
    ignoreDuringBuilds: true,
  },
  
  // Suppress hydration warnings for now while we fix SSR issues
  reactStrictMode: true,
  
  // Suppress console errors during build/SSR
  onDemandEntries: {
    maxInactiveAge: 25 * 1000,
    pagesBufferLength: 2,
  },
};

export default withBundleAnalyzer(nextConfig);
