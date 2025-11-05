/**
 * User Utility Functions
 * 
 * Helper functions for parsing and displaying user information
 */

export interface ParsedUser {
  fullName: string
  firstName: string
  lastName: string
  email: string
  displayName: string // "First Last" or falls back to user_id
}

/**
 * Parse user email_masked field which can be in format:
 * - "First Last <email@example.com>" (new format)
 * - "email@example.com" (simple email)
 * - "User Label — Description" (old format)
 * 
 * @param email_masked - The email_masked field from user object
 * @param user_id - The user_id as fallback
 * @returns ParsedUser object with name and email
 */
export function parseUserInfo(email_masked: string | null | undefined, user_id: string): ParsedUser {
  if (!email_masked) {
    return {
      fullName: user_id,
      firstName: user_id,
      lastName: '',
      email: '',
      displayName: user_id,
    }
  }

  // Check for "First Last <email@example.com>" format
  const nameEmailMatch = email_masked.match(/^([^<]+)\s*<([^>]+)>$/)
  if (nameEmailMatch) {
    const fullName = nameEmailMatch[1].trim()
    const email = nameEmailMatch[2].trim()
    const nameParts = fullName.split(' ')
    const firstName = nameParts[0] || fullName
    const lastName = nameParts.slice(1).join(' ') || ''
    
    return {
      fullName,
      firstName,
      lastName,
      email,
      displayName: fullName,
    }
  }

  // Check if it's just an email
  if (email_masked.includes('@')) {
    const namePart = email_masked.split('@')[0]
    // Try to extract name from email like "alice.martinez@example.com"
    const emailNameParts = namePart.split('.')
    if (emailNameParts.length >= 2) {
      const firstName = capitalizeFirst(emailNameParts[0])
      const lastName = capitalizeFirst(emailNameParts[1])
      return {
        fullName: `${firstName} ${lastName}`,
        firstName,
        lastName,
        email: email_masked,
        displayName: `${firstName} ${lastName}`,
      }
    }
  }

  // Fallback to email_masked or user_id
  return {
    fullName: email_masked,
    firstName: email_masked,
    lastName: '',
    email: email_masked.includes('@') ? email_masked : '',
    displayName: email_masked,
  }
}

function capitalizeFirst(str: string): string {
  return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase()
}

/**
 * Get a short display name for compact views
 * @param email_masked - The email_masked field from user object
 * @param user_id - The user_id as fallback
 * @returns Short display name like "Alice M." or "Alice"
 */
export function getShortDisplayName(email_masked: string | null | undefined, user_id: string): string {
  const parsed = parseUserInfo(email_masked, user_id)
  if (parsed.lastName) {
    return `${parsed.firstName} ${parsed.lastName.charAt(0)}.`
  }
  return parsed.firstName
}

/**
 * Format signal count for display
 * @param total - Total number of signals
 * @param detected - Number of detected signals
 * @returns Formatted string like "4 of 4 signals"
 */
export function formatSignalCount(detected: number, total: number = 4): string {
  return `${detected} of ${total} signal${total !== 1 ? 's' : ''}`
}

