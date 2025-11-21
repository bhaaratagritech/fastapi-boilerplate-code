"""
Rate Limiting Dependency for FastAPI.

This module provides rate limiting functionality using Redis as the distributed storage backend.
Rate limiting prevents abuse by restricting the number of requests a client can make within a
specified time window.

How It Works:
-------------
1. **Initialization**: The rate limiter is initialized in `app/main.py` during application startup
   with the Redis client. This connects the limiter to a shared Redis instance.

2. **Request Tracking**: When a request hits an endpoint with rate limiting enabled:
   - The limiter extracts a unique identifier to track the client
   - It checks Redis to see how many requests that identifier has made in the current time window
   - If under the limit: request proceeds, counter increments in Redis
   - If over the limit: request is rejected with HTTP 429 (Too Many Requests)

Client Identification:
---------------------
**By default, fastapi-limiter uses the CLIENT IP ADDRESS as the identifier.**

The identifier is extracted from `request.client.host`, which contains the client's IP address.
This means:
- ✅ Rate limiting is per IP address (not per user)
- ✅ Multiple users behind the same NAT/proxy share the same limit
- ✅ Works even for unauthenticated requests
- ⚠️ Users can bypass limits by changing IP addresses (using VPNs, proxies, etc.)

**How to Find the Identifier:**
1. Check Redis keys: Rate limit counters are stored in Redis with keys like:
   ```
   fastapi-limiter:<identifier>:<endpoint_path>
   ```
   Example: `fastapi-limiter:192.168.1.100:/users/`

2. Inspect request: The IP address used is available in:
   ```python
   request.client.host  # e.g., "192.168.1.100"
   ```

3. Check logs: The rate limiter logs can show which identifier triggered the limit

**Customizing the Identifier:**
To use a different identifier (e.g., user ID from JWT token), you can customize the key function.
See the example below (this is for reference - current implementation uses IP address):

Example custom key function:
    from fastapi import Request
    from fastapi_limiter.depends import RateLimiter

    def get_user_id_key(request: Request) -> str:
        # If user is authenticated, use user ID
        if hasattr(request.state, "user") and request.state.user:
            return f"user:{request.state.user.get('sub')}"
        # Fallback to IP address for unauthenticated requests
        return request.client.host if request.client else "unknown"

    # Custom rate limiter with user ID as identifier
    rate_limiter = RateLimiter(
        times=_settings.rate_limit_per_minute,
        minutes=1,
        identifier=get_user_id_key  # Custom key function
    )

**Current Implementation:**
The current code uses the default behavior (IP address). To verify:
- Look at `app/main.py` line 53: `FastAPILimiter.init(redis_client)` - no custom identifier function
- Look at `app/dependencies/rate_limit.py` line 97: `RateLimiter(...)` - no `identifier` parameter

This means rate limiting is currently **per IP address**, not per user.

3. **Time Window**: Uses a sliding window algorithm. The limit resets after the specified time
   period (e.g., 60 requests per 1 minute).

4. **Redis Storage**: All rate limit counters are stored in Redis, making it:
   - **Distributed**: Multiple application instances share the same rate limit state
   - **Persistent**: Rate limit state survives application restarts
   - **Fast**: Redis in-memory operations are extremely fast

Distributed Environment Behavior:
---------------------------------
When multiple instances of the application are running (e.g., behind a load balancer):

✅ **Shared State**: All instances connect to the same Redis instance/cluster
✅ **Consistent Limits**: A client hitting Instance A or Instance B sees the same rate limit
✅ **No Double Counting**: Requests are tracked centrally, preventing limit bypass
✅ **High Availability**: Redis can be configured as a cluster for redundancy

Example Scenario:
-----------------
- 3 application instances (A, B, C) behind a load balancer
- Rate limit: 60 requests/minute
- Client makes 30 requests to Instance A, 20 to Instance B, 10 to Instance C
- Total: 60 requests (limit reached)
- Next request to any instance → HTTP 429 error

Configuration:
--------------
- `RATE_LIMIT_PER_MINUTE`: Number of requests allowed per time window (default: 60)
- The time window is fixed at 1 minute in this implementation
- Configured via environment variable or `.env` file

Usage:
------
Rate limiting is applied at the router level:

```python
from fastapi import APIRouter, Depends
from .dependencies.rate_limit import rate_limiter

router = APIRouter(dependencies=[Depends(rate_limiter)])
```

All endpoints in this router will be rate limited.

Error Response:
---------------
When rate limit is exceeded, the client receives:
- Status Code: 429 (Too Many Requests)
- Headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`

Dependencies:
-------------
- Redis: Must be running and accessible (see `app/services/cache/redis_cache.py`)
- fastapi-limiter: Handles the rate limiting logic
- If Redis is unavailable, rate limiting is disabled (graceful degradation)

Best Practices:
---------------
1. **Redis High Availability**: Use Redis Sentinel or Cluster for production
2. **Monitoring**: Monitor Redis memory usage and connection health
3. **Tuning**: Adjust `RATE_LIMIT_PER_MINUTE` based on your API's capacity
4. **Different Limits**: Consider different limits for different endpoints/users
5. **Graceful Degradation**: Application continues if Redis is unavailable (current behavior)
"""

from __future__ import annotations

from fastapi_limiter.depends import RateLimiter

from ..core.config import get_settings

_settings = get_settings()

# Create a rate limiter instance
# - times: Maximum number of requests allowed in the time window
# - minutes: Time window duration (1 minute = 60 seconds)
# This creates a sliding window rate limiter that allows _settings.rate_limit_per_minute
# requests per minute per client (identified by IP address or custom key)
rate_limiter = RateLimiter(times=_settings.rate_limit_per_minute, minutes=1)



