/**
 * Rate Limiter for HousecallPro API
 * Handles rate limiting with exponential backoff and retry logic
 */

interface QueueItem<T> {
  fn: () => Promise<T>;
  resolve: (value: T) => void;
  reject: (error: Error) => void;
}

export class RateLimiter {
  private queue: QueueItem<any>[] = [];
  private processing = false;
  private requestsPerMinute: number;
  private retryAfter?: Date | null;
  private requestTimes: number[] = [];

  constructor(requestsPerMinute = 60) {
    this.requestsPerMinute = requestsPerMinute;
  }

  async execute<T>(fn: () => Promise<T>): Promise<T> {
    return new Promise((resolve, reject) => {
      this.queue.push({ fn, resolve, reject });
      this.processQueue();
    });
  }

  private async processQueue() {
    if (this.processing || this.queue.length === 0) return;

    this.processing = true;

    try {
      while (this.queue.length > 0) {
        // Check if we need to wait for rate limit reset
        if (this.retryAfter && new Date() < this.retryAfter) {
          const waitTime = this.retryAfter.getTime() - Date.now();
          console.log(`Rate limit active, waiting ${waitTime}ms...`);
          await this.sleep(waitTime);
          this.retryAfter = null;
        }

        // Clean old request times (older than 1 minute)
        const oneMinuteAgo = Date.now() - 60000;
        this.requestTimes = this.requestTimes.filter(time => time > oneMinuteAgo);

        // Check if we're at the rate limit
        if (this.requestTimes.length >= this.requestsPerMinute) {
          const oldestRequest = Math.min(...this.requestTimes);
          const waitTime = 60000 - (Date.now() - oldestRequest);
          if (waitTime > 0) {
            console.log(`Rate limit reached, waiting ${waitTime}ms...`);
            await this.sleep(waitTime);
            continue;
          }
        }

        const item = this.queue.shift()!;
        const startTime = Date.now();

        try {
          this.requestTimes.push(startTime);
          const result = await item.fn();
          item.resolve(result);
        } catch (error: any) {
          // Handle 429 rate limit errors
          if (error.status === 429) {
            console.log('429 Rate limit error received');
            
            // Extract retry-after header if available
            const retryAfterHeader = error.headers?.['retry-after'] || 
                                   error.headers?.['ratelimit-reset'];
            
            if (retryAfterHeader) {
              const retryAfterMs = parseInt(retryAfterHeader) * 1000;
              this.retryAfter = new Date(Date.now() + retryAfterMs);
              console.log(`Setting retry after: ${this.retryAfter}`);
            } else {
              // Default to 60 second backoff
              this.retryAfter = new Date(Date.now() + 60000);
            }

            // Put the request back at the front of the queue
            this.queue.unshift(item);
            continue;
          }

          item.reject(error);
        }

        // Minimum delay between requests to avoid overwhelming the API
        const minDelay = Math.ceil(60000 / this.requestsPerMinute);
        const elapsed = Date.now() - startTime;
        if (elapsed < minDelay) {
          await this.sleep(minDelay - elapsed);
        }
      }
    } finally {
      this.processing = false;
    }
  }

  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  // Get current queue status
  getStatus() {
    return {
      queueLength: this.queue.length,
      processing: this.processing,
      retryAfter: this.retryAfter,
      recentRequests: this.requestTimes.length,
      rateLimitRemaining: Math.max(0, this.requestsPerMinute - this.requestTimes.length)
    };
  }
}