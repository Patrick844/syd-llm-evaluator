/** PostHog product analytics — thin, safe wrapper.
 *
 *  Loads PostHog ONLY when VITE_POSTHOG_KEY is set, so local dev and any build
 *  without the key stay completely untracked (every function becomes a no-op).
 *  SYD stores nothing server-side, so this is the only record of how it's used
 *  (questions asked, how often the guardrail blocks an answer).
 *
 *  Set VITE_POSTHOG_KEY (and optionally VITE_POSTHOG_HOST) in the production
 *  build env only. The key is a *public* project key — safe to ship in client JS.
 */
import posthog from "posthog-js";

// The PostHog project key is PUBLIC (it ships in client JS), so it's safe to
// commit as the production default. It only activates in production builds
// (import.meta.env.PROD), so local `npm run dev` stays untracked. An env var
// (VITE_POSTHOG_KEY) overrides it — e.g. to point at a separate staging project.
const DEFAULT_KEY = "phc_C2h9R66JM7NHMX247wtD8RaZ8FMkfWZT6myTR4EDexp9";
const KEY =
  (import.meta.env.VITE_POSTHOG_KEY as string | undefined) ||
  (import.meta.env.PROD ? DEFAULT_KEY : undefined);
const HOST = (import.meta.env.VITE_POSTHOG_HOST as string | undefined) || "https://eu.i.posthog.com";

let enabled = false;

/** Call once at app startup. No-op when no key is configured. */
export function initAnalytics(): void {
  if (!KEY) return;
  posthog.init(KEY, {
    api_host: HOST,
    capture_pageview: true,
    capture_pageleave: true,
    autocapture: true,
    persistence: "localStorage+cookie",
  });
  enabled = true;
}

/** Record a named event with optional context properties. */
export function track(event: string, props?: Record<string, unknown>): void {
  if (!enabled) return;
  posthog.capture(event, props);
}
