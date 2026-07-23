/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Enforces clean CORS headers proxy limits if needed
  async rewrites() {
    return [
      {
        source: '/api/v1/:path*',
        destination: 'http://localhost:8000/api/v1/:path*'
      }
    ];
  }
};

module.exports = nextConfig;
