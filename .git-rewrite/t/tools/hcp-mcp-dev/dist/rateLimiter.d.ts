/**
 * Rate Limiter for HousecallPro API
 * Handles rate limiting with exponential backoff and retry logic
 */
export declare class RateLimiter {
    private queue;
    private processing;
    private requestsPerMinute;
    private retryAfter?;
    private requestTimes;
    constructor(requestsPerMinute?: number);
    execute<T>(fn: () => Promise<T>): Promise<T>;
    private processQueue;
    private sleep;
    getStatus(): {
        queueLength: number;
        processing: boolean;
        retryAfter: Date | null | undefined;
        recentRequests: number;
        rateLimitRemaining: number;
    };
}
//# sourceMappingURL=rateLimiter.d.ts.map