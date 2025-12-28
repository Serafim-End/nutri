import { useState, useEffect, useCallback, useMemo } from 'react'

interface CountdownResult {
  /** Total seconds remaining */
  totalSeconds: number
  /** Minutes component */
  minutes: number
  /** Seconds component */
  seconds: number
  /** Formatted string "MM:SS" */
  formatted: string
  /** Is the countdown expired? */
  isExpired: boolean
  /** Is the countdown running? */
  isRunning: boolean
}

/**
 * Hook for countdown timer functionality.
 * Accepts an ISO timestamp string (UTC) and counts down to zero.
 * 
 * @param targetTimestamp - ISO 8601 timestamp string (e.g., "2024-12-27T10:00:00Z")
 * @returns CountdownResult with remaining time and status
 */
export function useCountdown(targetTimestamp: string | null | undefined): CountdownResult {
  const [totalSeconds, setTotalSeconds] = useState<number>(0)

  // Parse target timestamp and calculate initial remaining seconds
  const targetDate = useMemo(() => {
    if (!targetTimestamp) return null
    try {
      const date = new Date(targetTimestamp)
      return isNaN(date.getTime()) ? null : date
    } catch {
      return null
    }
  }, [targetTimestamp])

  // Calculate remaining seconds
  const calculateRemaining = useCallback(() => {
    if (!targetDate) return 0
    const now = new Date()
    const diff = Math.floor((targetDate.getTime() - now.getTime()) / 1000)
    return Math.max(0, diff)
  }, [targetDate])

  // Initialize and update countdown
  useEffect(() => {
    setTotalSeconds(calculateRemaining())

    if (!targetDate) return

    const interval = setInterval(() => {
      const remaining = calculateRemaining()
      setTotalSeconds(remaining)
      
      // Stop interval when expired
      if (remaining <= 0) {
        clearInterval(interval)
      }
    }, 1000)

    return () => clearInterval(interval)
  }, [targetDate, calculateRemaining])

  // Derive display values
  const minutes = Math.floor(totalSeconds / 60)
  const seconds = totalSeconds % 60
  const formatted = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`
  const isExpired = totalSeconds <= 0
  const isRunning = !isExpired && targetDate !== null

  return {
    totalSeconds,
    minutes,
    seconds,
    formatted,
    isExpired,
    isRunning,
  }
}

/**
 * Format a duration in seconds to a human-readable string.
 * @param seconds - Duration in seconds
 * @returns Formatted string like "10:00" or "1:23:45" for hours
 */
export function formatDuration(seconds: number): string {
  if (seconds < 0) return '00:00'
  
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = seconds % 60

  if (hours > 0) {
    return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }
  return `${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
}

