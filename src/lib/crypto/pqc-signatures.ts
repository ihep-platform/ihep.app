/**
 * Post-Quantum Cryptography: Digital Signatures (ML-DSA / Dilithium)
 *
 * Implementation of NIST FIPS 204 ML-DSA for quantum-resistant digital signatures.
 *
 * @module pqc-signatures
 * @author Jason M Jarmacz <jason@ihep.app>
 * @author Claude by Anthropic <noreply@anthropic.com>
 */

import { ml_dsa44, ml_dsa65, ml_dsa87 } from '@noble/post-quantum/ml-dsa.js'
import { randomBytes } from '@stablelib/random'
import { SHA512 } from '@stablelib/sha512'

/**
 * ML-DSA (Dilithium) security levels
 */
export enum SignatureSecurityLevel {
  /** NIST Level 2 - 128-bit security */
  LEVEL_2 = 'dilithium2',
  /** NIST Level 3 - 192-bit security (RECOMMENDED) */
  LEVEL_3 = 'dilithium3',
  /** NIST Level 5 - 256-bit security */
  LEVEL_5 = 'dilithium5',
}

/**
 * Signature key pair structure
 */
export interface SignatureKeyPair {
  publicKey: Uint8Array
  secretKey: Uint8Array
  algorithm: SignatureSecurityLevel
  createdAt: number
  keyId: string
  expiresAt?: number
}

/**
 * Signature result structure
 */
export interface SignatureResult {
  signature: Uint8Array
  algorithm: SignatureSecurityLevel
  keyId: string
  timestamp: number
}

/**
 * ML-DSA (Dilithium) Digital Signature implementation
 */
export class PQCSignature {
  private algorithm: SignatureSecurityLevel

  constructor(securityLevel: SignatureSecurityLevel = SignatureSecurityLevel.LEVEL_3) {
    this.algorithm = securityLevel
  }

  /**
   * Generate a new signature key pair
   *
   * @param expiryDays - Optional expiry in days (default: 30 days for JWT signing keys)
   * @returns SignatureKeyPair with public/secret keys
   */
  async generateKeyPair(expiryDays?: number): Promise<SignatureKeyPair> {
    const keyId = this.generateKeyId()
    const createdAt = Date.now()
    const expiresAt = expiryDays ? createdAt + expiryDays * 24 * 60 * 60 * 1000 : undefined

    let keys: { publicKey: Uint8Array; secretKey: Uint8Array }

    switch (this.algorithm) {
      case SignatureSecurityLevel.LEVEL_2:
        keys = ml_dsa44.keygen()
        break
      case SignatureSecurityLevel.LEVEL_3:
        keys = ml_dsa65.keygen()
        break
      case SignatureSecurityLevel.LEVEL_5:
        keys = ml_dsa87.keygen()
        break
      default:
        throw new Error(`Unsupported signature security level: ${this.algorithm}`)
    }

    return {
      publicKey: keys.publicKey,
      secretKey: keys.secretKey,
      algorithm: this.algorithm,
      createdAt,
      keyId,
      expiresAt,
    }
  }

  /**
   * Sign a message
   *
   * @param message - Message to sign (can be string or Uint8Array)
   * @param secretKey - Signer's secret key
   * @param keyId - Key identifier for signature metadata
   * @returns SignatureResult with signature and metadata
   */
  async sign(
    message: string | Uint8Array,
    secretKey: Uint8Array,
    keyId: string
  ): Promise<SignatureResult> {
    const messageBytes = typeof message === 'string' ? new TextEncoder().encode(message) : message

    // Hash message with SHA-512 for consistent input size
    const hasher = new SHA512()
    hasher.update(messageBytes)
    const messageHash = hasher.digest()

    let signature: Uint8Array

    switch (this.algorithm) {
      case SignatureSecurityLevel.LEVEL_2:
        signature = ml_dsa44.sign(secretKey, messageHash)
        break
      case SignatureSecurityLevel.LEVEL_3:
        signature = ml_dsa65.sign(secretKey, messageHash)
        break
      case SignatureSecurityLevel.LEVEL_5:
        signature = ml_dsa87.sign(secretKey, messageHash)
        break
      default:
        throw new Error(`Unsupported signature security level: ${this.algorithm}`)
    }

    return {
      signature,
      algorithm: this.algorithm,
      keyId,
      timestamp: Date.now(),
    }
  }

  /**
   * Verify a signature
   *
   * @param message - Original message
   * @param signature - Signature to verify
   * @param publicKey - Signer's public key
   * @returns true if signature is valid, false otherwise
   */
  async verify(message: string | Uint8Array, signature: Uint8Array, publicKey: Uint8Array): Promise<boolean> {
    try {
      const messageBytes = typeof message === 'string' ? new TextEncoder().encode(message) : message

      // Hash message with SHA-512 (same as signing)
      const hasher = new SHA512()
      hasher.update(messageBytes)
      const messageHash = hasher.digest()

      let isValid: boolean

      switch (this.algorithm) {
        case SignatureSecurityLevel.LEVEL_2:
          isValid = ml_dsa44.verify(publicKey, messageHash, signature)
          break
        case SignatureSecurityLevel.LEVEL_3:
          isValid = ml_dsa65.verify(publicKey, messageHash, signature)
          break
        case SignatureSecurityLevel.LEVEL_5:
          isValid = ml_dsa87.verify(publicKey, messageHash, signature)
          break
        default:
          throw new Error(`Unsupported signature security level: ${this.algorithm}`)
      }

      return isValid
    } catch (error) {
      // Signature verification failures throw exceptions in noble
      return false
    }
  }

  /**
   * Check if a key pair is expired
   */
  isKeyExpired(keyPair: SignatureKeyPair): boolean {
    if (!keyPair.expiresAt) return false
    return Date.now() > keyPair.expiresAt
  }

  /**
   * Generate unique key identifier
   */
  private generateKeyId(): string {
    const randomPart = randomBytes(16)
    const timestamp = Date.now()
    return `${this.algorithm}-${timestamp}-${Buffer.from(randomPart).toString('hex').slice(0, 16)}`
  }

  /**
   * Get algorithm parameters
   */
  getParameters() {
    const params: Record<
      SignatureSecurityLevel,
      { publicKeySize: number; secretKeySize: number; signatureSize: number }
    > = {
      [SignatureSecurityLevel.LEVEL_2]: {
        publicKeySize: 1312,
        secretKeySize: 2560,
        signatureSize: 2420,
      },
      [SignatureSecurityLevel.LEVEL_3]: {
        publicKeySize: 1952,
        secretKeySize: 4032,
        signatureSize: 3293,
      },
      [SignatureSecurityLevel.LEVEL_5]: {
        publicKeySize: 2592,
        secretKeySize: 4896,
        signatureSize: 4595,
      },
    }

    return params[this.algorithm]
  }
}

/**
 * JWT Token signing with PQC signatures
 */
export class PQCJWTSigner {
  private signer: PQCSignature

  constructor(securityLevel: SignatureSecurityLevel = SignatureSecurityLevel.LEVEL_3) {
    this.signer = new PQCSignature(securityLevel)
  }

  /**
   * Generate signing key pair for JWT tokens
   */
  async generateSigningKey(): Promise<SignatureKeyPair> {
    // JWT signing keys rotate every 30 days
    return this.signer.generateKeyPair(30)
  }

  /**
   * Sign JWT payload
   *
   * @param payload - JWT payload object
   * @param secretKey - Signing key
   * @param keyId - Key identifier
   * @returns Complete JWT token with PQC signature
   */
  async signJWT(payload: Record<string, unknown>, secretKey: Uint8Array, keyId: string): Promise<string> {
    // Create JWT header
    const header = {
      alg: this.signer['algorithm'], // Access private field for algorithm
      typ: 'JWT',
      kid: keyId,
    }

    // Encode header and payload
    const encodedHeader = this.base64UrlEncode(JSON.stringify(header))
    const encodedPayload = this.base64UrlEncode(JSON.stringify(payload))

    // Sign header.payload
    const message = `${encodedHeader}.${encodedPayload}`
    const signatureResult = await this.signer.sign(message, secretKey, keyId)

    // Encode signature
    const encodedSignature = this.base64UrlEncode(Buffer.from(signatureResult.signature).toString('base64'))

    // Return complete JWT
    return `${message}.${encodedSignature}`
  }

  /**
   * Verify JWT token
   *
   * @param token - Complete JWT token
   * @param publicKey - Verification public key
   * @returns Decoded payload if valid, null if invalid
   */
  async verifyJWT(token: string, publicKey: Uint8Array): Promise<Record<string, unknown> | null> {
    try {
      const parts = token.split('.')
      if (parts.length !== 3) return null

      const [encodedHeader, encodedPayload, encodedSignature] = parts

      // Decode signature
      const signatureBuffer = Buffer.from(this.base64UrlDecode(encodedSignature), 'base64')
      const signature = new Uint8Array(signatureBuffer)

      // Verify signature
      const message = `${encodedHeader}.${encodedPayload}`
      const isValid = await this.signer.verify(message, signature, publicKey)

      if (!isValid) return null

      // Decode and return payload
      const payload = JSON.parse(this.base64UrlDecode(encodedPayload))

      // Check expiry
      if (payload.exp && Date.now() / 1000 > payload.exp) {
        return null // Token expired
      }

      return payload
    } catch (error) {
      return null
    }
  }

  /**
   * Base64 URL-safe encoding
   */
  private base64UrlEncode(input: string): string {
    return Buffer.from(input)
      .toString('base64')
      .replace(/\+/g, '-')
      .replace(/\//g, '_')
      .replace(/=/g, '')
  }

  /**
   * Base64 URL-safe decoding
   */
  private base64UrlDecode(input: string): string {
    // Add padding
    let padded = input
    while (padded.length % 4 !== 0) {
      padded += '='
    }

    // Replace URL-safe characters
    const base64 = padded.replace(/-/g, '+').replace(/_/g, '/')

    return Buffer.from(base64, 'base64').toString('utf-8')
  }
}

/**
 * API Request Signing with PQC
 */
export class PQCAPISigner {
  private signer: PQCSignature

  constructor(securityLevel: SignatureSecurityLevel = SignatureSecurityLevel.LEVEL_3) {
    this.signer = new PQCSignature(securityLevel)
  }

  /**
   * Sign API request
   *
   * @param method - HTTP method (GET, POST, etc.)
   * @param path - Request path
   * @param body - Request body (if any)
   * @param secretKey - API secret key
   * @param keyId - Key identifier
   * @returns Signature headers to include in request
   */
  async signRequest(
    method: string,
    path: string,
    body: unknown,
    secretKey: Uint8Array,
    keyId: string
  ): Promise<Record<string, string>> {
    // Canonical request format
    const timestamp = Date.now()
    const bodyString = body ? JSON.stringify(body) : ''

    const canonicalRequest = [method.toUpperCase(), path, timestamp.toString(), bodyString].join('\n')

    // Sign canonical request
    const signatureResult = await this.signer.sign(canonicalRequest, secretKey, keyId)

    return {
      'X-PQC-Algorithm': signatureResult.algorithm,
      'X-PQC-KeyId': keyId,
      'X-PQC-Timestamp': timestamp.toString(),
      'X-PQC-Signature': Buffer.from(signatureResult.signature).toString('base64'),
    }
  }

  /**
   * Verify API request signature
   */
  async verifyRequest(
    method: string,
    path: string,
    body: unknown,
    headers: Record<string, string>,
    publicKey: Uint8Array
  ): Promise<boolean> {
    try {
      const timestamp = parseInt(headers['X-PQC-Timestamp'] || '0')
      const signatureBase64 = headers['X-PQC-Signature']

      if (!timestamp || !signatureBase64) return false

      // Check timestamp (reject if > 5 minutes old to prevent replay attacks)
      const age = Date.now() - timestamp
      if (age > 5 * 60 * 1000 || age < 0) {
        return false
      }

      // Reconstruct canonical request
      const bodyString = body ? JSON.stringify(body) : ''
      const canonicalRequest = [method.toUpperCase(), path, timestamp.toString(), bodyString].join('\n')

      // Decode signature
      const signature = Uint8Array.from(Buffer.from(signatureBase64, 'base64'))

      // Verify
      return await this.signer.verify(canonicalRequest, signature, publicKey)
    } catch (error) {
      return false
    }
  }
}

/**
 * Factory functions
 */
export function createPQCSignature(securityLevel: SignatureSecurityLevel = SignatureSecurityLevel.LEVEL_3): PQCSignature {
  return new PQCSignature(securityLevel)
}

export function createPQCJWTSigner(securityLevel: SignatureSecurityLevel = SignatureSecurityLevel.LEVEL_3): PQCJWTSigner {
  return new PQCJWTSigner(securityLevel)
}

export function createPQCAPISigner(securityLevel: SignatureSecurityLevel = SignatureSecurityLevel.LEVEL_3): PQCAPISigner {
  return new PQCAPISigner(securityLevel)
}

/**
 * Serialize key pair to JSON for storage
 */
export function serializeSignatureKeyPair(keyPair: SignatureKeyPair): string {
  return JSON.stringify({
    publicKey: Buffer.from(keyPair.publicKey).toString('base64'),
    secretKey: Buffer.from(keyPair.secretKey).toString('base64'),
    algorithm: keyPair.algorithm,
    createdAt: keyPair.createdAt,
    keyId: keyPair.keyId,
    expiresAt: keyPair.expiresAt,
  })
}

/**
 * Deserialize key pair from JSON
 */
export function deserializeSignatureKeyPair(serialized: string): SignatureKeyPair {
  const parsed = JSON.parse(serialized)
  return {
    publicKey: Uint8Array.from(Buffer.from(parsed.publicKey, 'base64')),
    secretKey: Uint8Array.from(Buffer.from(parsed.secretKey, 'base64')),
    algorithm: parsed.algorithm as SignatureSecurityLevel,
    createdAt: parsed.createdAt,
    keyId: parsed.keyId,
    expiresAt: parsed.expiresAt,
  }
}
