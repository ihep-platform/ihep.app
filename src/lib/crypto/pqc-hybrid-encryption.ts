/**
 * Post-Quantum Hybrid Encryption System
 *
 * Implements AES-256-GCM with Kyber-wrapped keys for quantum-resistant data encryption.
 * Follows NIST guidelines for hybrid cryptography.
 *
 * @module pqc-hybrid-encryption
 * @author Jason M Jarmacz <jason@ihep.app>
 * @author Claude by Anthropic <noreply@anthropic.com>
 */

import { XChaCha20Poly1305 } from '@stablelib/xchacha20poly1305'
import { randomBytes } from '@stablelib/random'
import { KyberKEM, KyberSecurityLevel, type KyberKeyPair } from './pqc-kyber'
import { SHA512 } from '@stablelib/sha512'

/**
 * Encrypted data structure
 */
export interface EncryptedData {
  /** Encrypted ciphertext */
  ciphertext: Uint8Array
  /** Kyber ciphertext (wrapped DEK) */
  kyberCiphertext: Uint8Array
  /** XChaCha20Poly1305 nonce */
  nonce: Uint8Array
  /** Algorithm identifier */
  algorithm: string
  /** Recipient key ID */
  keyId: string
  /** Encryption timestamp */
  timestamp: number
  /** AEAD authentication tag (included in ciphertext by XChaCha20Poly1305) */
  /** Metadata hash for integrity */
  metadataHash: Uint8Array
}

/**
 * Decrypted data structure
 */
export interface DecryptedData {
  plaintext: Uint8Array
  metadata: {
    algorithm: string
    keyId: string
    timestamp: number
  }
}

/**
 * Hybrid Encryption System
 *
 * Encryption flow:
 * 1. Generate random Data Encryption Key (DEK) - 256 bits
 * 2. Encrypt plaintext with XChaCha20-Poly1305 using DEK
 * 3. Encapsulate DEK using Kyber KEM
 * 4. Store: {ciphertext, kyber_ciphertext, nonce, metadata}
 *
 * Decryption flow:
 * 1. Decapsulate DEK using Kyber secret key
 * 2. Decrypt ciphertext with XChaCha20-Poly1305 using recovered DEK
 * 3. Verify metadata integrity
 */
export class HybridEncryption {
  private kyberKEM: KyberKEM
  private securityLevel: KyberSecurityLevel

  constructor(securityLevel: KyberSecurityLevel = KyberSecurityLevel.LEVEL_3) {
    this.kyberKEM = new KyberKEM(securityLevel)
    this.securityLevel = securityLevel
  }

  /**
   * Encrypt data with hybrid PQC encryption
   *
   * @param plaintext - Data to encrypt (string or bytes)
   * @param recipientPublicKey - Recipient's Kyber public key
   * @param keyId - Recipient's key identifier
   * @returns EncryptedData structure
   */
  async encrypt(
    plaintext: string | Uint8Array,
    recipientPublicKey: Uint8Array,
    keyId: string
  ): Promise<EncryptedData> {
    // Convert plaintext to bytes
    const plaintextBytes = typeof plaintext === 'string' ? new TextEncoder().encode(plaintext) : plaintext

    // Step 1: Generate random DEK (32 bytes for XChaCha20-Poly1305)
    const dek = randomBytes(32)

    // Step 2: Encrypt plaintext with XChaCha20-Poly1305
    const nonce = randomBytes(24) // XChaCha20 uses 24-byte nonce
    const cipher = new XChaCha20Poly1305(dek)
    const ciphertext = cipher.seal(nonce, plaintextBytes)

    // Step 3: Encapsulate DEK with Kyber
    const { ciphertext: kyberCiphertext, sharedSecret } = await this.kyberKEM.encapsulate(recipientPublicKey)

    // Derive encryption key for DEK from Kyber shared secret
    const dekEncryptionKey = await this.kyberKEM.deriveKey(
      sharedSecret,
      undefined,
      new TextEncoder().encode('IHEP-DEK-Wrapping-v1'),
      32
    )

    // Wrap DEK with derived key
    const dekNonce = randomBytes(24)
    const dekCipher = new XChaCha20Poly1305(dekEncryptionKey)
    const wrappedDEK = dekCipher.seal(dekNonce, dek)

    // Step 4: Create metadata and compute hash
    const timestamp = Date.now()
    const algorithm = `XChaCha20-Poly1305+${this.securityLevel}`

    const metadata = JSON.stringify({
      algorithm,
      keyId,
      timestamp,
    })

    const metadataHash = this.hashMetadata(metadata)

    // Return encrypted structure
    return {
      ciphertext,
      kyberCiphertext,
      nonce,
      algorithm,
      keyId,
      timestamp,
      metadataHash,
    }
  }

  /**
   * Decrypt data with hybrid PQC decryption
   *
   * @param encrypted - EncryptedData structure
   * @param recipientSecretKey - Recipient's Kyber secret key
   * @returns Decrypted plaintext
   */
  async decrypt(encrypted: EncryptedData, recipientSecretKey: Uint8Array): Promise<DecryptedData> {
    // Step 1: Verify metadata integrity
    const reconstructedMetadata = JSON.stringify({
      algorithm: encrypted.algorithm,
      keyId: encrypted.keyId,
      timestamp: encrypted.timestamp,
    })

    const expectedHash = this.hashMetadata(reconstructedMetadata)
    if (!this.constantTimeEqual(expectedHash, encrypted.metadataHash)) {
      throw new Error('Metadata integrity check failed')
    }

    // Step 2: Decapsulate to recover shared secret
    const sharedSecret = await this.kyberKEM.decapsulate(encrypted.kyberCiphertext, recipientSecretKey)

    // Derive DEK decryption key
    const dekEncryptionKey = await this.kyberKEM.deriveKey(
      sharedSecret,
      undefined,
      new TextEncoder().encode('IHEP-DEK-Wrapping-v1'),
      32
    )

    // Step 3: Decrypt ciphertext with recovered DEK
    const cipher = new XChaCha20Poly1305(dekEncryptionKey)

    let plaintext: Uint8Array
    try {
      const decrypted = cipher.open(encrypted.nonce, encrypted.ciphertext)
      if (decrypted === null) {
        throw new Error('Decryption failed: Invalid ciphertext or authentication tag')
      }
      plaintext = decrypted
    } catch (error) {
      throw new Error('Decryption failed: Invalid ciphertext or authentication tag')
    }

    return {
      plaintext,
      metadata: {
        algorithm: encrypted.algorithm,
        keyId: encrypted.keyId,
        timestamp: encrypted.timestamp,
      },
    }
  }

  /**
   * Encrypt PHI (Protected Health Information) with field-level encryption
   *
   * @param data - Object with fields to encrypt
   * @param fieldsToEncrypt - Array of field names to encrypt
   * @param recipientPublicKey - Recipient's public key
   * @param keyId - Key identifier
   * @returns Object with encrypted fields
   */
  async encryptPHI(
    data: Record<string, unknown>,
    fieldsToEncrypt: string[],
    recipientPublicKey: Uint8Array,
    keyId: string
  ): Promise<Record<string, unknown>> {
    const result: Record<string, unknown> = { ...data }

    for (const field of fieldsToEncrypt) {
      if (field in data && data[field] !== null && data[field] !== undefined) {
        const plaintext = JSON.stringify(data[field])
        const encrypted = await this.encrypt(plaintext, recipientPublicKey, keyId)

        // Store encrypted field as base64-encoded JSON
        result[field] = this.serializeEncryptedData(encrypted)
        result[`${field}_encrypted`] = true
      }
    }

    return result
  }

  /**
   * Decrypt PHI fields
   *
   * @param data - Object with encrypted fields
   * @param fieldsToDecrypt - Array of field names to decrypt
   * @param recipientSecretKey - Recipient's secret key
   * @returns Object with decrypted fields
   */
  async decryptPHI(
    data: Record<string, unknown>,
    fieldsToDecrypt: string[],
    recipientSecretKey: Uint8Array
  ): Promise<Record<string, unknown>> {
    const result: Record<string, unknown> = { ...data }

    for (const field of fieldsToDecrypt) {
      if (`${field}_encrypted` in data && data[`${field}_encrypted`] === true) {
        const encryptedData = this.deserializeEncryptedData(data[field] as string)
        const decrypted = await this.decrypt(encryptedData, recipientSecretKey)

        // Parse JSON to restore original type
        result[field] = JSON.parse(new TextDecoder().decode(decrypted.plaintext))
        delete result[`${field}_encrypted`]
      }
    }

    return result
  }

  /**
   * Re-encrypt data for a new recipient (key rotation)
   *
   * @param encrypted - Currently encrypted data
   * @param oldSecretKey - Current recipient's secret key
   * @param newPublicKey - New recipient's public key
   * @param newKeyId - New recipient's key ID
   * @returns Re-encrypted data
   */
  async reencrypt(
    encrypted: EncryptedData,
    oldSecretKey: Uint8Array,
    newPublicKey: Uint8Array,
    newKeyId: string
  ): Promise<EncryptedData> {
    // Decrypt with old key
    const decrypted = await this.decrypt(encrypted, oldSecretKey)

    // Encrypt with new key
    return await this.encrypt(decrypted.plaintext, newPublicKey, newKeyId)
  }

  /**
   * Hash metadata for integrity verification
   */
  private hashMetadata(metadata: string): Uint8Array {
    const hasher = new SHA512()
    hasher.update(new TextEncoder().encode(metadata))
    return hasher.digest()
  }

  /**
   * Constant-time comparison to prevent timing attacks
   */
  private constantTimeEqual(a: Uint8Array, b: Uint8Array): boolean {
    if (a.length !== b.length) return false

    let diff = 0
    for (let i = 0; i < a.length; i++) {
      diff |= a[i] ^ b[i]
    }

    return diff === 0
  }

  /**
   * Serialize encrypted data to base64 JSON
   */
  private serializeEncryptedData(encrypted: EncryptedData): string {
    return Buffer.from(
      JSON.stringify({
        ciphertext: Buffer.from(encrypted.ciphertext).toString('base64'),
        kyberCiphertext: Buffer.from(encrypted.kyberCiphertext).toString('base64'),
        nonce: Buffer.from(encrypted.nonce).toString('base64'),
        algorithm: encrypted.algorithm,
        keyId: encrypted.keyId,
        timestamp: encrypted.timestamp,
        metadataHash: Buffer.from(encrypted.metadataHash).toString('base64'),
      })
    ).toString('base64')
  }

  /**
   * Deserialize encrypted data from base64 JSON
   */
  private deserializeEncryptedData(serialized: string): EncryptedData {
    const json = Buffer.from(serialized, 'base64').toString('utf-8')
    const parsed = JSON.parse(json)

    return {
      ciphertext: Uint8Array.from(Buffer.from(parsed.ciphertext, 'base64')),
      kyberCiphertext: Uint8Array.from(Buffer.from(parsed.kyberCiphertext, 'base64')),
      nonce: Uint8Array.from(Buffer.from(parsed.nonce, 'base64')),
      algorithm: parsed.algorithm,
      keyId: parsed.keyId,
      timestamp: parsed.timestamp,
      metadataHash: Uint8Array.from(Buffer.from(parsed.metadataHash, 'base64')),
    }
  }
}

/**
 * Batch encryption for multiple recipients
 */
export class MultiRecipientEncryption {
  private encryption: HybridEncryption

  constructor(securityLevel: KyberSecurityLevel = KyberSecurityLevel.LEVEL_3) {
    this.encryption = new HybridEncryption(securityLevel)
  }

  /**
   * Encrypt data for multiple recipients
   *
   * @param plaintext - Data to encrypt
   * @param recipients - Array of {publicKey, keyId}
   * @returns Array of encrypted data (one per recipient)
   */
  async encryptForMultiple(
    plaintext: string | Uint8Array,
    recipients: Array<{ publicKey: Uint8Array; keyId: string }>
  ): Promise<EncryptedData[]> {
    const encrypted: EncryptedData[] = []

    for (const recipient of recipients) {
      const result = await this.encryption.encrypt(plaintext, recipient.publicKey, recipient.keyId)
      encrypted.push(result)
    }

    return encrypted
  }
}

/**
 * Factory functions
 */
export function createHybridEncryption(securityLevel: KyberSecurityLevel = KyberSecurityLevel.LEVEL_3): HybridEncryption {
  return new HybridEncryption(securityLevel)
}

export function createMultiRecipientEncryption(
  securityLevel: KyberSecurityLevel = KyberSecurityLevel.LEVEL_3
): MultiRecipientEncryption {
  return new MultiRecipientEncryption(securityLevel)
}

/**
 * Serialize encrypted data to JSON
 */
export function serializeEncryptedData(encrypted: EncryptedData): string {
  return JSON.stringify({
    ciphertext: Buffer.from(encrypted.ciphertext).toString('base64'),
    kyberCiphertext: Buffer.from(encrypted.kyberCiphertext).toString('base64'),
    nonce: Buffer.from(encrypted.nonce).toString('base64'),
    algorithm: encrypted.algorithm,
    keyId: encrypted.keyId,
    timestamp: encrypted.timestamp,
    metadataHash: Buffer.from(encrypted.metadataHash).toString('base64'),
  })
}

/**
 * Deserialize encrypted data from JSON
 */
export function deserializeEncryptedData(serialized: string): EncryptedData {
  const parsed = JSON.parse(serialized)
  return {
    ciphertext: Uint8Array.from(Buffer.from(parsed.ciphertext, 'base64')),
    kyberCiphertext: Uint8Array.from(Buffer.from(parsed.kyberCiphertext, 'base64')),
    nonce: Uint8Array.from(Buffer.from(parsed.nonce, 'base64')),
    algorithm: parsed.algorithm,
    keyId: parsed.keyId,
    timestamp: parsed.timestamp,
    metadataHash: Uint8Array.from(Buffer.from(parsed.metadataHash, 'base64')),
  }
}
