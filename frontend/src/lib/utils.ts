import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

/**
 * Utility function to merge Tailwind CSS classes.
 * 
 * Why this exists:
 * - Combines clsx for conditional classes and tailwind-merge for deduplication
 * - Used throughout components for dynamic className composition
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/**
 * Check if the app is running in development mode with debug enabled.
 * 
 * Why this exists:
 * - Controls visibility of dev-only features (decision traces, debug panels)
 * - Combines Vite's DEV mode with custom VITE_SHOW_DEBUG env variable
 * 
 * Usage:
 * - {isDevMode() && <DevDebugPanel />}
 */
export function isDevMode(): boolean {
  return import.meta.env.DEV && import.meta.env.VITE_SHOW_DEBUG === 'true'
}


