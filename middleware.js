export default async function middleware(request) {
  const url = new URL(request.url);

  if (url.pathname.startsWith('/api/')) {
    
    // --- 1. DEVELOPER API TRAFFIC (UNKEY) ---
    const authHeader = request.headers.get('authorization');
    if (authHeader && authHeader.startsWith('Bearer ')) {
      const token = authHeader.split(' ')[1];
      const unkeyApiId = process.env.UNKEY_API_ID;
      
      if (!unkeyApiId) {
        console.error("UNKEY_API_ID is not configured in Vercel.");
        return new Response(JSON.stringify({ detail: "Server misconfiguration. UNKEY_API_ID missing." }), { status: 500 });
      }

      try {
        const verifyResponse = await fetch("https://api.unkey.dev/v1/keys.verify", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ key: token, apiId: unkeyApiId })
        });
        
        const data = await verifyResponse.json();
        
        if (!data.valid) {
          let errorMsg = "Invalid API Key.";
          let statusCode = 401;
          
          if (data.code === "RATE_LIMITED") {
             errorMsg = "API Key rate limit exceeded. Please try again later or upgrade your plan.";
             statusCode = 429;
          } else if (data.code === "USAGE_EXCEEDED") {
             errorMsg = "API Key usage quota exceeded.";
             statusCode = 429;
          }
          
          return new Response(
            JSON.stringify({ detail: errorMsg }),
            { status: statusCode, headers: { 'Content-Type': 'application/json' } }
          );
        }
        
        // If valid, allow request through to FastAPI (bypassing IP rate limit)
        return;
      } catch (err) {
        console.error("Failed to verify Unkey:", err);
        return new Response(JSON.stringify({ detail: "Internal Server Error verifying API key." }), { status: 500 });
      }
    }

    // --- 2. NORMAL WEBSITE TRAFFIC (UPSTASH REDIS) ---
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
