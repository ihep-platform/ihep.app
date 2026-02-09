/**
 * Integration tests for complete PQC system
 *
 * @module pqc-integration.test
 */

import { describe, it, expect } from 'vitest'
import { KyberKEM, KyberSecurityLevel } from '../pqc-kyber'
import { PQCSignature, PQCJWTSigner, SignatureSecurityLevel } from '../pqc-signatures'
import { HybridEncryption } from '../pqc-hybrid-encryption'
import { PQCKeyManager, KeyType, KeyStatus } from '../pqc-key-management'

describe('End-to-End PQC Integration', () => {
  describe('Secure Communication Flow', () => {
    it('should encrypt, sign, decrypt, and verify a message', async () => {
      // Setup: Generate keys for Alice and Bob
      const aliceEncryption = new KyberKEM(KyberSecurityLevel.LEVEL_3)
      const aliceEncKeys = await aliceEncryption.generateKeyPair()

      const aliceSigning = new PQCSignature(SignatureSecurityLevel.LEVEL_3)
      const aliceSignKeys = await aliceSigning.generateKeyPair(30)

      const bobEncryption = new KyberKEM(KyberSecurityLevel.LEVEL_3)
      const bobEncKeys = await bobEncryption.generateKeyPair()

      // Alice encrypts a message for Bob
      const message = 'Confidential patient data: BP=120/80, HR=72'
      const encryption = new HybridEncryption(KyberSecurityLevel.LEVEL_3)
      const encrypted = await encryption.encrypt(message, bobEncKeys.publicKey, bobEncKeys.keyId)

      expect(encrypted.ciphertext).toBeInstanceOf(Uint8Array)
      expect(encrypted.keyId).toBe(bobEncKeys.keyId)

      // Alice signs the encrypted message
      const signatureResult = await aliceSigning.sign(encrypted.ciphertext, aliceSignKeys.secretKey, aliceSignKeys.keyId)

      // Bob receives encrypted+signed message
      // First, verify signature
      const isValidSignature = await aliceSigning.verify(
        encrypted.ciphertext,
        signatureResult.signature,
        aliceSignKeys.publicKey
      )
      expect(isValidSignature).toBe(true)

      // Then decrypt message
      const decrypted = await encryption.decrypt(encrypted, bobEncKeys.secretKey)
      const recoveredMessage = new TextDecoder().decode(decrypted.plaintext)

      expect(recoveredMessage).toBe(message)
    })
  })

  describe('PHI Field-Level Encryption', () => {
    it('should encrypt and decrypt patient health records', async () => {
      const encryption = new HybridEncryption(KyberSecurityLevel.LEVEL_5)
      const kyber = new KyberKEM(KyberSecurityLevel.LEVEL_5)
      const keyPair = await kyber.generateKeyPair()

      // Patient health record with sensitive fields
      const patientRecord = {
        patientId: 'PT-12345',
        name: 'John Doe',
        ssn: '123-45-6789',
        diagnosis: 'Type 2 Diabetes',
        medications: ['Metformin 500mg', 'Lisinopril 10mg'],
        lastVisit: '2026-01-05',
        nextAppointment: '2026-02-15',
      }

      // Encrypt sensitive fields
      const fieldsToEncrypt = ['ssn', 'diagnosis', 'medications']
      const encryptedRecord = await encryption.encryptPHI(
        patientRecord,
        fieldsToEncrypt,
        keyPair.publicKey,
        keyPair.keyId
      )

      // Verify encrypted fields are not readable
      expect(encryptedRecord.ssn).not.toBe(patientRecord.ssn)
      expect(encryptedRecord.ssn_encrypted).toBe(true)
      expect(encryptedRecord.diagnosis_encrypted).toBe(true)

      // Verify non-encrypted fields are still readable
      expect(encryptedRecord.patientId).toBe(patientRecord.patientId)
      expect(encryptedRecord.name).toBe(patientRecord.name)

      // Decrypt PHI fields
      const decryptedRecord = await encryption.decryptPHI(encryptedRecord, fieldsToEncrypt, keyPair.secretKey)

      expect(decryptedRecord.ssn).toBe(patientRecord.ssn)
      expect(decryptedRecord.diagnosis).toBe(patientRecord.diagnosis)
      expect(decryptedRecord.medications).toEqual(patientRecord.medications)
      expect(decryptedRecord.ssn_encrypted).toBeUndefined()
    })
  })

  describe('JWT Authentication Flow', () => {
    it('should issue and verify PQC-signed JWT tokens', async () => {
      const jwtSigner = new PQCJWTSigner(SignatureSecurityLevel.LEVEL_3)
      const signingKey = await jwtSigner.generateSigningKey()

      // Create JWT payload
      const payload = {
        sub: 'user-12345',
        role: 'patient',
        iat: Math.floor(Date.now() / 1000),
        exp: Math.floor(Date.now() / 1000) + 1800, // 30 minutes
        jti: 'jwt-' + Math.random().toString(36),
      }

      // Sign JWT
      const token = await jwtSigner.signJWT(payload, signingKey.secretKey, signingKey.keyId)

      expect(token).toBeTruthy()
      expect(token.split('.')).toHaveLength(3) // header.payload.signature

      // Verify JWT
      const verified = await jwtSigner.verifyJWT(token, signingKey.publicKey)

      expect(verified).not.toBeNull()
      expect(verified?.sub).toBe(payload.sub)
      expect(verified?.role).toBe(payload.role)
    })

    it('should reject expired JWT tokens', async () => {
      const jwtSigner = new PQCJWTSigner(SignatureSecurityLevel.LEVEL_3)
      const signingKey = await jwtSigner.generateSigningKey()

      // Create expired token
      const payload = {
        sub: 'user-12345',
        role: 'patient',
        iat: Math.floor(Date.now() / 1000) - 3600,
        exp: Math.floor(Date.now() / 1000) - 1800, // Expired 30 minutes ago
        jti: 'jwt-' + Math.random().toString(36),
      }

      const token = await jwtSigner.signJWT(payload, signingKey.secretKey, signingKey.keyId)

      // Verify should return null for expired token
      const verified = await jwtSigner.verifyJWT(token, signingKey.publicKey)
      expect(verified).toBeNull()
    })
  })

  describe('Key Management and Rotation', () => {
    it('should manage complete key lifecycle', async () => {
      const keyManager = new PQCKeyManager()

      // Generate master encryption key
      const masterKey = await keyManager.generateEncryptionKey(
        KeyType.MASTER_KEY,
        'system',
        KyberSecurityLevel.LEVEL_5,
        {
          expiryDays: 365,
          tags: { purpose: 'root-encryption', compliance: 'HIPAA' },
        }
      )

      expect(masterKey.metadata.keyId).toBeTruthy()
      expect(masterKey.metadata.status).toBe(KeyStatus.ACTIVE)

      // Generate JWT signing key
      const jwtKey = await keyManager.generateSigningKey(
        KeyType.JWT_SIGNING,
        'auth-service',
        SignatureSecurityLevel.LEVEL_3,
        {
          expiryDays: 30,
          tags: { purpose: 'jwt-authentication' },
        }
      )

      // Retrieve keys
      const retrievedMasterKey = keyManager.getKey(masterKey.metadata.keyId)
      expect(retrievedMasterKey).toBeDefined()

      // Get primary JWT key
      const primaryJWT = keyManager.getPrimaryKey(KeyType.JWT_SIGNING)
      expect(primaryJWT?.metadata.keyId).toBe(jwtKey.metadata.keyId)

      // Record key usage
      keyManager.recordKeyUsage(jwtKey.metadata.keyId)
      const updatedKey = keyManager.getKey(jwtKey.metadata.keyId)
      expect(updatedKey?.metadata.usageCount).toBe(1)

      // Export key inventory
      const inventory = keyManager.exportKeyInventory()
      expect(inventory).toHaveLength(2)
      expect(inventory[0].keyType).toBeDefined()
    })

    it('should rotate keys when needed', async () => {
      const keyManager = new PQCKeyManager()

      // Generate key with short expiry
      const oldKey = await keyManager.generateEncryptionKey(KeyType.DATA_KEY, 'data-service', KyberSecurityLevel.LEVEL_3, {
        expiryDays: 0, // Immediate expiry for testing
      })

      // Rotate key
      const rotation = await keyManager.rotateKey(oldKey.metadata.keyId)

      expect(rotation.oldKeyId).toBe(oldKey.metadata.keyId)
      expect(rotation.newKeyId).not.toBe(oldKey.metadata.keyId)
      expect(rotation.reencryptionRequired).toBe(true)

      // Verify old key is deprecated
      const deprecatedKey = keyManager.getKey(oldKey.metadata.keyId)
      expect(deprecatedKey?.metadata.status).toBe(KeyStatus.DEPRECATED)

      // Verify new key is active
      const newKey = keyManager.getKey(rotation.newKeyId)
      expect(newKey?.metadata.status).toBe(KeyStatus.ACTIVE)
    })
  })

  describe('Data Re-encryption (Key Rotation)', () => {
    it('should re-encrypt data during key rotation', async () => {
      const encryption = new HybridEncryption(KyberSecurityLevel.LEVEL_3)
      const kyber = new KyberKEM(KyberSecurityLevel.LEVEL_3)

      // Generate old and new key pairs
      const oldKeyPair = await kyber.generateKeyPair()
      const newKeyPair = await kyber.generateKeyPair()

      // Encrypt with old key
      const originalMessage = 'Patient medical history - highly sensitive data'
      const encrypted = await encryption.encrypt(originalMessage, oldKeyPair.publicKey, oldKeyPair.keyId)

      // Re-encrypt for new key
      const reencrypted = await encryption.reencrypt(encrypted, oldKeyPair.secretKey, newKeyPair.publicKey, newKeyPair.keyId)

      expect(reencrypted.keyId).toBe(newKeyPair.keyId)
      expect(reencrypted.kyberCiphertext).not.toEqual(encrypted.kyberCiphertext)

      // Verify decryption with new key works
      const decrypted = await encryption.decrypt(reencrypted, newKeyPair.secretKey)
      const recoveredMessage = new TextDecoder().decode(decrypted.plaintext)

      expect(recoveredMessage).toBe(originalMessage)

      // Verify old key cannot decrypt new ciphertext
      await expect(encryption.decrypt(reencrypted, oldKeyPair.secretKey)).rejects.toThrow()
    })
  })

  describe('HIPAA Compliance Scenarios', () => {
    it('should support audit trail with immutable signatures', async () => {
      const signer = new PQCSignature(SignatureSecurityLevel.LEVEL_5)
      const signingKey = await signer.generateKeyPair()

      // Simulate audit log entries
      const auditEntries = [
        {
          timestamp: Date.now(),
          userId: 'admin-001',
          action: 'access-phi',
          resource: 'patient-12345',
          outcome: 'success',
        },
        {
          timestamp: Date.now() + 1000,
          userId: 'doctor-002',
          action: 'update-diagnosis',
          resource: 'patient-12345',
          outcome: 'success',
        },
      ]

      // Sign each audit entry
      const signedEntries = []
      let previousHash = '0'.repeat(128) // Genesis hash

      for (const entry of auditEntries) {
        const entryWithHash = {
          ...entry,
          previousHash,
        }

        const serialized = JSON.stringify(entryWithHash)
        const signature = await signer.sign(serialized, signingKey.secretKey, signingKey.keyId)

        signedEntries.push({
          entry: entryWithHash,
          signature: signature.signature,
        })

        // Compute hash for next entry (blockchain-style)
        previousHash = Buffer.from(signature.signature).toString('hex').slice(0, 128)
      }

      // Verify audit chain integrity
      for (let i = 0; i < signedEntries.length; i++) {
        const { entry, signature } = signedEntries[i]
        const serialized = JSON.stringify(entry)

        const isValid = await signer.verify(serialized, signature, signingKey.publicKey)
        expect(isValid).toBe(true)

        // Verify chain linkage
        if (i > 0) {
          const prevSignatureHash = Buffer.from(signedEntries[i - 1].signature).toString('hex').slice(0, 128)
          expect(entry.previousHash).toBe(prevSignatureHash)
        }
      }
    })
  })

  describe('Performance Under Load', () => {
    it('should maintain performance with 100 concurrent operations', async () => {
      const encryption = new HybridEncryption(KyberSecurityLevel.LEVEL_3)
      const kyber = new KyberKEM(KyberSecurityLevel.LEVEL_3)
      const keyPair = await kyber.generateKeyPair()

      const operations = []
      const startTime = performance.now()

      // 100 concurrent encryptions
      for (let i = 0; i < 100; i++) {
        operations.push(encryption.encrypt(`Message ${i}`, keyPair.publicKey, keyPair.keyId))
      }

      const encrypted = await Promise.all(operations)
      const encryptTime = performance.now() - startTime

      // Should complete in reasonable time (< 1 second for 100 operations)
      expect(encryptTime).toBeLessThan(1000)

      // Decrypt all
      const decryptStart = performance.now()
      const decryptOperations = encrypted.map((enc) => encryption.decrypt(enc, keyPair.secretKey))
      await Promise.all(decryptOperations)
      const decryptTime = performance.now() - decryptStart

      expect(decryptTime).toBeLessThan(1000)
    })
  })
})

describe('Security Validations', () => {
  it('should prevent tampering with encrypted data', async () => {
    const encryption = new HybridEncryption(KyberSecurityLevel.LEVEL_3)
    const kyber = new KyberKEM(KyberSecurityLevel.LEVEL_3)
    const keyPair = await kyber.generateKeyPair()

    const message = 'Original message'
    const encrypted = await encryption.encrypt(message, keyPair.publicKey, keyPair.keyId)

    // Tamper with ciphertext
    encrypted.ciphertext[0] ^= 0xff

    // Decryption should fail
    await expect(encryption.decrypt(encrypted, keyPair.secretKey)).rejects.toThrow()
  })

  it('should prevent metadata tampering', async () => {
    const encryption = new HybridEncryption(KyberSecurityLevel.LEVEL_3)
    const kyber = new KyberKEM(KyberSecurityLevel.LEVEL_3)
    const keyPair = await kyber.generateKeyPair()

    const message = 'Original message'
    const encrypted = await encryption.encrypt(message, keyPair.publicKey, keyPair.keyId)

    // Tamper with timestamp
    encrypted.timestamp += 1

    // Decryption should fail due to metadata integrity check
    await expect(encryption.decrypt(encrypted, keyPair.secretKey)).rejects.toThrow('Metadata integrity check failed')
  })

  it('should enforce key expiration', async () => {
    const keyManager = new PQCKeyManager()

    const expiredKey = await keyManager.generateSigningKey(
      KeyType.JWT_SIGNING,
      'test-service',
      SignatureSecurityLevel.LEVEL_3,
      { expiryDays: -1 } // Expired yesterday
    )

    const signer = new PQCSignature(SignatureSecurityLevel.LEVEL_3)
    expect(signer.isKeyExpired(JSON.parse(expiredKey.keyMaterial))).toBe(true)
  })
})
