export default async function middleware(request) {
  const url = new URL(request.url);

  // Apply rate limiting to all API routes
  if (url.pathname.startsWith('/api/')) {
    const ip = request.headers.get('x-forwarded-for') || '127.0.0.1';
    const clientIp = ip.split(',')[0].trim();

    const redisUrl = process.env.UPSTASH_REDIS_REST_URL;
    const redisToken = process.env.UPSTASH_REDIS_REST_TOKEN;

    if (!redisUrl || !redisToken) {
      console.warn("Upstash Redis credentials are not configured in Vercel. Rate limiting is disabled.");
      return; // Allow request through
    }

    const currentMinute = Math.floor(Date.now() / 60000);
    const key = `ratelimit:${clientIp}:${currentMinute}`;

    try {
      // Send pipeline commands to Upstash Redis REST API
      const res = await fetch(`${redisUrl}/pipeline`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${redisToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify([
          ['INCR', key],
          ['EXPIRE', key, 60]
        ])
      });

      if (!res.ok) {
        console.error("Upstash Redis returned error status:", res.status);
        return; // Fallback: allow request through if DB is down
      }

      const results = await res.json();
      const count = results[0].result;

      // Limit: 10 requests per minute
      if (count > 10) {
        return new Response(
          JSON.stringify({
            detail: "Too many requests. You are allowed 10 requests per minute. Please try again later."
          }),
          {
            status: 429,
            headers: {
              'Content-Type': 'application/json',
              'Retry-After': '60'
            }
          }
        );
      }
    } catch (err) {
      console.error("Failed to run rate limit check:", err);
      return; // Fallback: allow request through
    }
  }
}
