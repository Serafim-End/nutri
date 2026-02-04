/**
 * Client-side constants.
 * Backend base URL (without /api) - same host as API for docs, media, etc.
 */
const apiBase = (import.meta.env.VITE_API_BASE_URL || '/api').replace(/\/api\/?$/, '')

/** URL to the public offer for booking and payment (client-facing) */
export const BOOKING_OFFER_URL = apiBase ? `${apiBase}/docs/booking-offer.pdf` : ''
