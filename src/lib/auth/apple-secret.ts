import { webcrypto } from 'crypto'
import { SignJWT } from 'jose'

const APPLE_AUDIENCE = 'https://appleid.apple.com'

const requireEnv = (name: string): string => {
  const value = process.env[name]
  if (!value) {
    throw new Error(`Missing required environment variable: ${name}`)
  }
  return value
}

const getPrivateKey = (): string => {
  // Support newline-escaped env values
  const raw = requireEnv('APPLE_PRIVATE_KEY')
  return raw.replace(/\\n/g, '\n')
}

export async function generateAppleClientSecret(): Promise<string> {
  const teamId = requireEnv('APPLE_TEAM_ID')
  const clientId = requireEnv('APPLE_CLIENT_ID')
  const keyId = requireEnv('APPLE_KEY_ID')
  const privateKey = getPrivateKey()

  const now = Math.floor(Date.now() / 1000)
  // Apple allows up to 6 months; we keep it short (5 minutes) for security.
  const exp = now + 5 * 60

  const token = await new SignJWT({
    iss: teamId,
    aud: APPLE_AUDIENCE,
    sub: clientId,
  })
    .setProtectedHeader({ alg: 'ES256', kid: keyId })
    .setIssuedAt(now)
    .setExpirationTime(exp)
    .sign(await importPKCS8(privateKey, 'ES256'))

  return token
}

// Local helper to import the PKCS8 key (kept inline to avoid another module).
const importPKCS8 = async (pem: string, alg: 'ES256') => {
  const pemContents = pem
    .replace('-----BEGIN PRIVATE KEY-----', '')
    .replace('-----END PRIVATE KEY-----', '')
    .replace(/\s+/g, '')
  const binaryDerString = Buffer.from(pemContents, 'base64').toString('binary')
  const binaryDer = new Uint8Array(binaryDerString.length)
  for (let i = 0; i < binaryDerString.length; i++) {
    binaryDer[i] = binaryDerString.charCodeAt(i)
  }
  return await webcrypto.subtle.importKey(
    'pkcs8',
    binaryDer.buffer,
    { name: 'ECDSA', namedCurve: 'P-256' },
    false,
    ['sign']
  )
}

