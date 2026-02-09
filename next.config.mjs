import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  poweredByHeader: false,
  output: 'standalone',
  // Enable React Compiler for performance optimizations
  reactCompiler: true,
  // Transpile Three.js and related packages for proper bundling
  transpilePackages: ['three', 'three-usdz-loader'],
  // Force correct repo root selection to avoid monorepo lockfile confusion
  outputFileTracingRoot: path.join(__dirname),

  // Turbopack configuration (Next.js 16+ default bundler)
  // Empty config to silence warning when using webpack for specific features
  turbopack: {},

  // Webpack configuration for Three.js compatibility
  // Used when --webpack flag is passed or for specific optimizations
  webpack: (config, { isServer }) => {
    // Handle Three.js module resolution
    config.resolve.alias = {
      ...config.resolve.alias,
      'three': path.resolve(__dirname, 'node_modules/three'),
    }

    // Ensure proper handling of Three.js examples/addons
    config.module.rules.push({
      test: /three\/examples\/jsm/,
      sideEffects: true,
    })

    // Handle GLSL shader files
    config.module.rules.push({
      test: /\.(glsl|vs|fs|vert|frag)$/,
      type: 'asset/source',
    })

    // Handle USDZ/USD file loading
    config.module.rules.push({
      test: /\.(usdz|usda|usdc)$/,
      type: 'asset/resource',
    })

    // Exclude Three.js from server-side bundling (WebGL not available)
    if (isServer) {
      config.externals = config.externals || []
      config.externals.push('three')
    }

    return config
  },
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'images.unsplash.com',
      },
      {
        protocol: 'https',
        hostname: 'via.placeholder.com',
      },
    ],
  },
  async headers() {
    const isDev = process.env.NODE_ENV === 'development'
    // CSP: Allow unsafe-inline and unsafe-eval in development for hot reload
    const cspValue = isDev
      ? "default-src 'self'; base-uri 'self'; frame-ancestors 'none'; object-src 'none'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; font-src 'self' data:; connect-src 'self' ws: wss:; form-action 'self'"
      : "default-src 'self'; base-uri 'self'; frame-ancestors 'none'; object-src 'none'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; font-src 'self' data:; connect-src 'self'; form-action 'self'; upgrade-insecure-requests"
    return [
      {
        source: '/(.*)',
        headers: [
          { key: 'Strict-Transport-Security', value: 'max-age=63072000; includeSubDomains; preload' },
          { key: 'X-Content-Type-Options', value: 'nosniff' },
          { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
          { key: 'X-Frame-Options', value: 'DENY' },
          { key: 'Content-Security-Policy', value: cspValue },
          // Required for SharedArrayBuffer (USDZ WASM loader)
          { key: 'Cross-Origin-Opener-Policy', value: 'same-origin' },
          { key: 'Cross-Origin-Embedder-Policy', value: 'require-corp' }
        ]
      },
      {
        source: '/_next/static/(.*)',
        headers: [
          { key: 'Cache-Control', value: 'public, max-age=31536000, immutable' }
        ]
      },
      {
        source: '/assets/(.*)',
        headers: [
          { key: 'Cache-Control', value: 'public, max-age=31536000, immutable' }
        ]
      }
    ]
  },
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: '/api/:path*'
      }
    ]
  }
}

export default nextConfig;
