function passwordError(value) {
  const characters = Array.from(value.normalize('NFC'))
  if (characters.some((character) => {
    const codepoint = character.codePointAt(0)
    return codepoint >= 0xD800 && codepoint <= 0xDFFF
  })) return 'Enter valid Unicode characters.'
  if (characters.length < 15 || characters.length > 128) return 'Use between 15 and 128 characters.'
  return null
}

export function validateLoginFields(fields) {
  const errors = {}
  if (!fields.email.trim()) errors.email = 'Enter your email address.'
  const message = passwordError(fields.password)
  if (message) errors.password = message
  return errors
}

export function validateRegistrationFields(fields) {
  const errors = validateLoginFields(fields)
  const message = passwordError(fields.password_confirmation)
  if (message) errors.password_confirmation = message
  if (!errors.password_confirmation &&
      fields.password.normalize('NFC') !== fields.password_confirmation.normalize('NFC')) {
    errors.password_confirmation = 'Passwords must match.'
  }
  return errors
}
