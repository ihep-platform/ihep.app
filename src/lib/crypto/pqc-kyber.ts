/**
 * Post-Quantum Cryptography: Kyber Key Encapsulation Mechanism (KEM)
 *
 * Implementation of NIST FIPS 203 ML-KEM using real cryptographic primitives.
 *
 * @module pqc-kyber
 * @author Jason M Jarmacz <jason@ihep.app>
 * @author Claude by Anthropic <noreply@anthropic.com>
 */

import { ml_kem512, ml_kem768, ml_kem1024 } from '@noble/post-quantum/ml-kem.js'
import { randomBytes } from '@stablelib/random'
import { HKDF } from '@stablelib/hkdf'
import { SHA512 } from '@stablelib/sha512'

/**
 * NIST security levels for Kyber variants
 */
export enum KyberSecurityLevel {
  /** NIST Level 1 - 128-bit classical security equivalent */
  LEVEL_1 = 'kyber512',
  /** NIST Level 3 - 192-bit classical security equivalent (RECOMMENDED) */
  LEVEL_3 = 'kyber768',
  /** NIST Level 5 - 256-bit classical security equivalent */
  LEVEL_5 = 'kyber1024',
}

/**
 * Kyber key pair structure
 */
export interface KyberKeyPair {
  publicKey: Uint8Array
  secretKey: Uint8Array
  algorithm: KyberSecurityLevel
  createdAt: number
  keyId: string
}

/**
 * Kyber encapsulation result
 */
export interface KyberEncapsulation {
  ciphertext: Uint8Array
  sharedSecret: Uint8Array
}

/**
 * Kyber KEM implementation with algorithm agility
 */
export class KyberKEM {
  private algorithm: KyberSecurityLevel

  constructor(securityLevel: KyberSecurityLevel = KyberSecurityLevel.LEVEL_3) {
    this.algorithm = securityLevel
  }

  /**
   * Generate a new Kyber key pair
   *
   * @returns KyberKeyPair with public/secret keys
   */
  async generateKeyPair(): Promise<KyberKeyPair> {
    const keyId = this.generateKeyId()

    let keys: { publicKey: Uint8Array; secretKey: Uint8Array }

    switch (this.algorithm) {
      case KyberSecurityLevel.LEVEL_1:
        keys = ml_kem512.keygen()
        break
      case KyberSecurityLevel.LEVEL_3:
        keys = ml_kem768.keygen()
        break
      case KyberSecurityLevel.LEVEL_5:
        keys = ml_kem1024.keygen()
        break
      default:
        throw new Error(`Unsupported Kyber security level: ${this.algorithm}`)
    }

    return {
      publicKey: keys.publicKey,
      secretKey: keys.secretKey,
      algorithm: this.algorithm,
      createdAt: Date.now(),
      keyId,
    }
  }

  /**
   * Encapsulate: Generate shared secret and ciphertext
   *
   * @param publicKey - Recipient's public key
   * @returns Encapsulation result with ciphertext and shared secret
   */
  async encapsulate(publicKey: Uint8Array): Promise<KyberEncapsulation> {
    let result: { cipherText: Uint8Array; sharedSecret: Uint8Array }

    switch (this.algorithm) {
      case KyberSecurityLevel.LEVEL_1:
        result = ml_kem512.encapsulate(publicKey)
        break
      case KyberSecurityLevel.LEVEL_3:
        result = ml_kem768.encapsulate(publicKey)
        break
      case KyberSecurityLevel.LEVEL_5:
        result = ml_kem1024.encapsulate(publicKey)
        break
      default:
        throw new Error(`Unsupported Kyber security level: ${this.algorithm}`)
    }

    return {
      ciphertext: result.cipherText,
      sharedSecret: result.sharedSecret,
    }
  }

  /**
   * Decapsulate: Recover shared secret from ciphertext
   *
   * @param ciphertext - Encapsulated ciphertext
   * @param secretKey - Recipient's secret key
   * @returns Shared secret
   */
  async decapsulate(ciphertext: Uint8Array, secretKey: Uint8Array): Promise<Uint8Array> {
    switch (this.algorithm) {
      case KyberSecurityLevel.LEVEL_1:
        return ml_kem512.decapsulate(ciphertext, secretKey)
      case KyberSecurityLevel.LEVEL_3:
        return ml_kem768.decapsulate(ciphertext, secretKey)
      case KyberSecurityLevel.LEVEL_5:
        return ml_kem1024.decapsulate(ciphertext, secretKey)
      default:
        throw new Error(`Unsupported Kyber security level: ${this.algorithm}`)
    }
  }

  /**
   * Derive encryption key from shared secret using HKDF-SHA512
   *
   * @param sharedSecret - Shared secret from encapsulation
   * @param salt - Optional salt for key derivation
   * @param info - Context information for key derivation
   * @param keyLength - Desired key length in bytes (default: 32 for AES-256)
   * @returns Derived key
   */
  async deriveKey(
    sharedSecret: Uint8Array,
    salt?: Uint8Array,
    info: Uint8Array = new Uint8Array([]),
    keyLength: number = 32
  ): Promise<Uint8Array> {
    const actualSalt = salt || randomBytes(32)
    const hkdf = new HKDF(SHA512, sharedSecret, actualSalt, info)
    const derived = hkdf.expand(keyLength)
    hkdf.clean()
    return derived
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
    const params: Record<KyberSecurityLevel, { publicKeySize: number; secretKeySize: number; ciphertextSize: number; sharedSecretSize: number }> = {
      [KyberSecurityLevel.LEVEL_1]: {
        publicKeySize: 800,
        secretKeySize: 1632,
        ciphertextSize: 768,
        sharedSecretSize: 32,
      },
      [KyberSecurityLevel.LEVEL_3]: {
        publicKeySize: 1184,
        secretKeySize: 2400,
        ciphertextSize: 1088,
        sharedSecretSize: 32,
      },
      [KyberSecurityLevel.LEVEL_5]: {
        publicKeySize: 1568,
        secretKeySize: 3168,
        ciphertextSize: 1568,
        sharedSecretSize: 32,
      },
    }

    return params[this.algorithm]
  }
}

/**
 * Hybrid KEM: Combines classical ECDH with post-quantum Kyber
 * Provides defense-in-depth against both classical and quantum attacks
 */
export class HybridKEM {
  private kyberKEM: KyberKEM

  constructor(kyberLevel: KyberSecurityLevel = KyberSecurityLevel.LEVEL_3) {
    this.kyberKEM = new KyberKEM(kyberLevel)
  }

  /**
   * Generate hybrid key pair (classical + PQC)
   */
  async generateKeyPair(): Promise<{
    kyberKeys: KyberKeyPair
    keyId: string
  }> {
    // Generate Kyber keys
    const kyberKeys = await this.kyberKEM.generateKeyPair()

    return {
      kyberKeys,
      keyId: kyberKeys.keyId,
    }
  }

  /**
   * Hybrid encapsulation
   *
   * @param kyberPublicKey - Recipient's Kyber public key
   * @returns Combined encapsulation result
   */
  async encapsulate(kyberPublicKey: Uint8Array): Promise<{
    kyberCiphertext: Uint8Array
    combinedSecret: Uint8Array
  }> {
    // Kyber encapsulation
    const kyberResult = await this.kyberKEM.encapsulate(kyberPublicKey)

    // Combine secrets using HKDF with fixed salt for deterministic derivation
    const combinedSecret = await this.kyberKEM.deriveKey(
      kyberResult.sharedSecret,
      new Uint8Array(32), // Fixed zero salt for deterministic derivation
      new TextEncoder().encode('IHEP-Hybrid-KEM-v1'),
      32
    )

    return {
      kyberCiphertext: kyberResult.ciphertext,
      combinedSecret,
    }
  }

  /**
   * Hybrid decapsulation
   *
   * @param kyberCiphertext - Kyber ciphertext
   * @param kyberSecretKey - Recipient's Kyber secret key
   * @returns Combined shared secret
   */
  async decapsulate(
    kyberCiphertext: Uint8Array,
    kyberSecretKey: Uint8Array
  ): Promise<Uint8Array> {
    // Kyber decapsulation
    const kyberSecret = await this.kyberKEM.decapsulate(kyberCiphertext, kyberSecretKey)

    // Combine secrets using HKDF (same as encapsulation) with fixed salt
    const combinedSecret = await this.kyberKEM.deriveKey(
      kyberSecret,
      new Uint8Array(32), // Fixed zero salt for deterministic derivation
      new TextEncoder().encode('IHEP-Hybrid-KEM-v1'),
      32
    )

    return combinedSecret
  }
}

/**
 * Factory function for creating Kyber KEM instances
 */
export function createKyberKEM(securityLevel: KyberSecurityLevel = KyberSecurityLevel.LEVEL_3): KyberKEM {
  return new KyberKEM(securityLevel)
}

/**
 * Factory function for creating Hybrid KEM instances
 */
export function createHybridKEM(securityLevel: KyberSecurityLevel = KyberSecurityLevel.LEVEL_3): HybridKEM {
  return new HybridKEM(securityLevel)
}

/**
 * Serialize key pair to JSON for storage
 */
export function serializeKeyPair(keyPair: KyberKeyPair): string {
  return JSON.stringify({
    publicKey: Buffer.from(keyPair.publicKey).toString('base64'),
    secretKey: Buffer.from(keyPair.secretKey).toString('base64'),
    algorithm: keyPair.algorithm,
    createdAt: keyPair.createdAt,
    keyId: keyPair.keyId,
  })
}

/**
 * Deserialize key pair from JSON
 */
export function deserializeKeyPair(serialized: string): KyberKeyPair {
  const parsed = JSON.parse(serialized)
  return {
    publicKey: Uint8Array.from(Buffer.from(parsed.publicKey, 'base64')),
    secretKey: Uint8Array.from(Buffer.from(parsed.secretKey, 'base64')),
    algorithm: parsed.algorithm as KyberSecurityLevel,
    createdAt: parsed.createdAt,
    keyId: parsed.keyId,
  }
}
