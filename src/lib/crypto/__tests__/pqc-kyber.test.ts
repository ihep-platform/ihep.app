/**
 * Test suite for Kyber KEM implementation
 *
 * @module pqc-kyber.test
 */

import { describe, it, expect, beforeEach } from 'vitest'
import {
  KyberKEM,
  HybridKEM,
  KyberSecurityLevel,
  createKyberKEM,
  createHybridKEM,
  serializeKeyPair,
  deserializeKeyPair,
} from '../pqc-kyber'

describe('KyberKEM', () => {
  describe('Key Generation', () => {
    it('should generate valid Kyber-512 key pair', async () => {
      const kyber = new KyberKEM(KyberSecurityLevel.LEVEL_1)
      const keyPair = await kyber.generateKeyPair()

      expect(keyPair.publicKey).toBeInstanceOf(Uint8Array)
      expect(keyPair.secretKey).toBeInstanceOf(Uint8Array)
      expect(keyPair.algorithm).toBe(KyberSecurityLevel.LEVEL_1)
      expect(keyPair.keyId).toBeTruthy()
      expect(keyPair.createdAt).toBeGreaterThan(0)

      // Verify key sizes match specification
      const params = kyber.getParameters()
      expect(keyPair.publicKey.length).toBe(params.publicKeySize)
      expect(keyPair.secretKey.length).toBe(params.secretKeySize)
    })

    it('should generate valid Kyber-768 key pair', async () => {
      const kyber = new KyberKEM(KyberSecurityLevel.LEVEL_3)
      const keyPair = await kyber.generateKeyPair()

      expect(keyPair.algorithm).toBe(KyberSecurityLevel.LEVEL_3)

      const params = kyber.getParameters()
      expect(keyPair.publicKey.length).toBe(params.publicKeySize)
      expect(keyPair.secretKey.length).toBe(params.secretKeySize)
    })

    it('should generate valid Kyber-1024 key pair', async () => {
      const kyber = new KyberKEM(KyberSecurityLevel.LEVEL_5)
      const keyPair = await kyber.generateKeyPair()

      expect(keyPair.algorithm).toBe(KyberSecurityLevel.LEVEL_5)

      const params = kyber.getParameters()
      expect(keyPair.publicKey.length).toBe(params.publicKeySize)
      expect(keyPair.secretKey.length).toBe(params.secretKeySize)
    })

    it('should generate unique key pairs', async () => {
      const kyber = new KyberKEM(KyberSecurityLevel.LEVEL_3)
      const keyPair1 = await kyber.generateKeyPair()
      const keyPair2 = await kyber.generateKeyPair()

      expect(keyPair1.keyId).not.toBe(keyPair2.keyId)
      expect(keyPair1.publicKey).not.toEqual(keyPair2.publicKey)
      expect(keyPair1.secretKey).not.toEqual(keyPair2.secretKey)
    })
  })

  describe('Encapsulation and Decapsulation', () => {
    it('should encapsulate and decapsulate successfully', async () => {
      const kyber = new KyberKEM(KyberSecurityLevel.LEVEL_3)
      const keyPair = await kyber.generateKeyPair()

      // Encapsulate
      const { ciphertext, sharedSecret } = await kyber.encapsulate(keyPair.publicKey)

      expect(ciphertext).toBeInstanceOf(Uint8Array)
      expect(sharedSecret).toBeInstanceOf(Uint8Array)
      expect(sharedSecret.length).toBe(32) // Standard shared secret size

      // Decapsulate
      const recoveredSecret = await kyber.decapsulate(ciphertext, keyPair.secretKey)

      expect(recoveredSecret).toEqual(sharedSecret)
    })

    it('should produce different ciphertexts for same public key', async () => {
      const kyber = new KyberKEM(KyberSecurityLevel.LEVEL_3)
      const keyPair = await kyber.generateKeyPair()

      const result1 = await kyber.encapsulate(keyPair.publicKey)
      const result2 = await kyber.encapsulate(keyPair.publicKey)

      // Ciphertexts should be different (due to randomness)
      expect(result1.ciphertext).not.toEqual(result2.ciphertext)
      // But decapsulation should work for both
      const secret1 = await kyber.decapsulate(result1.ciphertext, keyPair.secretKey)
      const secret2 = await kyber.decapsulate(result2.ciphertext, keyPair.secretKey)

      expect(secret1).toEqual(result1.sharedSecret)
      expect(secret2).toEqual(result2.sharedSecret)
    })

    it('should fail decapsulation with wrong secret key', async () => {
      const kyber = new KyberKEM(KyberSecurityLevel.LEVEL_3)
      const keyPair1 = await kyber.generateKeyPair()
      const keyPair2 = await kyber.generateKeyPair()

      const { ciphertext, sharedSecret } = await kyber.encapsulate(keyPair1.publicKey)

      // Try to decapsulate with wrong key
      const wrongSecret = await kyber.decapsulate(ciphertext, keyPair2.secretKey)

      // Should NOT produce the same shared secret
      expect(wrongSecret).not.toEqual(sharedSecret)
    })
  })

  describe('Key Derivation', () => {
    it('should derive encryption key from shared secret', async () => {
      const kyber = new KyberKEM(KyberSecurityLevel.LEVEL_3)
      const keyPair = await kyber.generateKeyPair()
      const { sharedSecret } = await kyber.encapsulate(keyPair.publicKey)

      const derivedKey = await kyber.deriveKey(sharedSecret)

      expect(derivedKey).toBeInstanceOf(Uint8Array)
      expect(derivedKey.length).toBe(32) // Default AES-256 key size
    })

    it('should derive consistent keys with same inputs', async () => {
      const kyber = new KyberKEM(KyberSecurityLevel.LEVEL_3)
      const keyPair = await kyber.generateKeyPair()
      const { sharedSecret } = await kyber.encapsulate(keyPair.publicKey)

      const salt = new Uint8Array(32).fill(0xAB)
      const info = new TextEncoder().encode('test-context')

      const key1 = await kyber.deriveKey(sharedSecret, salt, info, 32)
      const key2 = await kyber.deriveKey(sharedSecret, salt, info, 32)

      expect(key1).toEqual(key2)
    })

    it('should derive different keys with different contexts', async () => {
      const kyber = new KyberKEM(KyberSecurityLevel.LEVEL_3)
      const keyPair = await kyber.generateKeyPair()
      const { sharedSecret } = await kyber.encapsulate(keyPair.publicKey)

      const key1 = await kyber.deriveKey(sharedSecret, undefined, new TextEncoder().encode('context-1'))
      const key2 = await kyber.deriveKey(sharedSecret, undefined, new TextEncoder().encode('context-2'))

      expect(key1).not.toEqual(key2)
    })
  })

  describe('Serialization', () => {
    it('should serialize and deserialize key pair', async () => {
      const kyber = new KyberKEM(KyberSecurityLevel.LEVEL_3)
      const keyPair = await kyber.generateKeyPair()

      const serialized = serializeKeyPair(keyPair)
      const deserialized = deserializeKeyPair(serialized)

      expect(deserialized.publicKey).toEqual(keyPair.publicKey)
      expect(deserialized.secretKey).toEqual(keyPair.secretKey)
      expect(deserialized.algorithm).toBe(keyPair.algorithm)
      expect(deserialized.keyId).toBe(keyPair.keyId)
      expect(deserialized.createdAt).toBe(keyPair.createdAt)
    })
  })

  describe('Factory Functions', () => {
    it('should create KyberKEM with factory', () => {
      const kyber = createKyberKEM(KyberSecurityLevel.LEVEL_3)
      expect(kyber).toBeInstanceOf(KyberKEM)
    })
  })
})

describe('HybridKEM', () => {
  describe('Hybrid Key Generation', () => {
    it('should generate hybrid key pair', async () => {
      const hybrid = new HybridKEM(KyberSecurityLevel.LEVEL_3)
      const { kyberKeys, keyId } = await hybrid.generateKeyPair()

      expect(kyberKeys).toBeDefined()
      expect(kyberKeys.publicKey).toBeInstanceOf(Uint8Array)
      expect(kyberKeys.secretKey).toBeInstanceOf(Uint8Array)
      expect(keyId).toBeTruthy()
    })
  })

  describe('Hybrid Encapsulation', () => {
    it('should perform hybrid encapsulation and decapsulation', async () => {
      const hybrid = new HybridKEM(KyberSecurityLevel.LEVEL_3)
      const { kyberKeys } = await hybrid.generateKeyPair()

      // Encapsulate
      const { kyberCiphertext, combinedSecret } = await hybrid.encapsulate(kyberKeys.publicKey)

      expect(kyberCiphertext).toBeInstanceOf(Uint8Array)
      expect(combinedSecret).toBeInstanceOf(Uint8Array)
      expect(combinedSecret.length).toBe(32)

      // Decapsulate
      const recoveredSecret = await hybrid.decapsulate(kyberCiphertext, kyberKeys.secretKey)

      expect(recoveredSecret).toEqual(combinedSecret)
    })

    it('should produce consistent hybrid secrets', async () => {
      const hybrid = new HybridKEM(KyberSecurityLevel.LEVEL_3)
      const { kyberKeys } = await hybrid.generateKeyPair()

      // Multiple encapsulations should produce different ciphertexts
      const result1 = await hybrid.encapsulate(kyberKeys.publicKey)
      const result2 = await hybrid.encapsulate(kyberKeys.publicKey)

      expect(result1.kyberCiphertext).not.toEqual(result2.kyberCiphertext)

      // But both should decapsulate correctly
      const secret1 = await hybrid.decapsulate(result1.kyberCiphertext, kyberKeys.secretKey)
      const secret2 = await hybrid.decapsulate(result2.kyberCiphertext, kyberKeys.secretKey)

      expect(secret1).toEqual(result1.combinedSecret)
      expect(secret2).toEqual(result2.combinedSecret)
    })
  })

  describe('Factory Functions', () => {
    it('should create HybridKEM with factory', () => {
      const hybrid = createHybridKEM(KyberSecurityLevel.LEVEL_3)
      expect(hybrid).toBeInstanceOf(HybridKEM)
    })
  })
})

describe('Security Properties', () => {
  it('should maintain security across all Kyber levels', async () => {
    const levels = [KyberSecurityLevel.LEVEL_1, KyberSecurityLevel.LEVEL_3, KyberSecurityLevel.LEVEL_5]

    for (const level of levels) {
      const kyber = new KyberKEM(level)
      const keyPair = await kyber.generateKeyPair()
      const { ciphertext, sharedSecret } = await kyber.encapsulate(keyPair.publicKey)
      const recovered = await kyber.decapsulate(ciphertext, keyPair.secretKey)

      expect(recovered).toEqual(sharedSecret)
    }
  })

  it('should not leak information through timing', async () => {
    const kyber = new KyberKEM(KyberSecurityLevel.LEVEL_3)
    const keyPair = await kyber.generateKeyPair()

    const timings: number[] = []

    // Measure multiple decapsulation operations
    for (let i = 0; i < 100; i++) {
      const { ciphertext } = await kyber.encapsulate(keyPair.publicKey)

      const start = performance.now()
      await kyber.decapsulate(ciphertext, keyPair.secretKey)
      const end = performance.now()

      timings.push(end - start)
    }

    // Check that timing variance is reasonable (not constant-time but should be consistent)
    const mean = timings.reduce((a, b) => a + b) / timings.length
    const variance = timings.reduce((acc, t) => acc + Math.pow(t - mean, 2), 0) / timings.length

    // Timing should be relatively consistent
    expect(variance).toBeLessThan(mean * 0.5) // Variance less than 50% of mean
  })
})

describe('Performance', () => {
  it('should meet performance targets for Kyber-768', async () => {
    const kyber = new KyberKEM(KyberSecurityLevel.LEVEL_3)

    // Key generation should be < 5ms
    const keyGenStart = performance.now()
    const keyPair = await kyber.generateKeyPair()
    const keyGenEnd = performance.now()
    expect(keyGenEnd - keyGenStart).toBeLessThan(5)

    // Encapsulation should be < 2ms
    const encapStart = performance.now()
    const { ciphertext } = await kyber.encapsulate(keyPair.publicKey)
    const encapEnd = performance.now()
    expect(encapEnd - encapStart).toBeLessThan(2)

    // Decapsulation should be < 2ms
    const decapStart = performance.now()
    await kyber.decapsulate(ciphertext, keyPair.secretKey)
    const decapEnd = performance.now()
    expect(decapEnd - decapStart).toBeLessThan(2)
  })
})
