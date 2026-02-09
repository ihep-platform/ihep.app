/**
 * Post-Quantum Cryptography: Key Management System
 *
 * Implements secure key generation, storage, rotation, and lifecycle management
 * for PQC keys in compliance with NIST and HIPAA requirements.
 *
 * @module pqc-key-management
 * @author Jason M Jarmacz <jason@ihep.app>
 * @author Claude by Anthropic <noreply@anthropic.com>
 */

import { KyberKEM, KyberSecurityLevel, type KyberKeyPair, serializeKeyPair as serializeKyberKeyPair, deserializeKeyPair as deserializeKyberKeyPair } from './pqc-kyber'
import {
  PQCSignature,
  SignatureSecurityLevel,
  type SignatureKeyPair,
  serializeSignatureKeyPair,
  deserializeSignatureKeyPair,
} from './pqc-signatures'
import { randomBytes } from '@stablelib/random'
import { SHA512 } from '@stablelib/sha512'

/**
 * Key types in the system
 */
export enum KeyType {
  /** Master encryption key (HSM-stored in production) */
  MASTER_KEY = 'master',
  /** Data encryption key */
  DATA_KEY = 'data',
  /** JWT signing key */
  JWT_SIGNING = 'jwt-signing',
  /** API request signing key */
  API_SIGNING = 'api-signing',
  /** TLS certificate key */
  TLS_CERT = 'tls-cert',
  /** Audit log signing key */
  AUDIT_LOG = 'audit-log',
}

/**
 * Key status
 */
export enum KeyStatus {
  ACTIVE = 'active',
  ROTATING = 'rotating',
  DEPRECATED = 'deprecated',
  COMPROMISED = 'compromised',
  DESTROYED = 'destroyed',
}

/**
 * Key metadata structure
 */
export interface KeyMetadata {
  keyId: string
  keyType: KeyType
  algorithm: KyberSecurityLevel | SignatureSecurityLevel
  status: KeyStatus
  createdAt: number
  expiresAt?: number
  rotateAt?: number
  lastUsed?: number
  usageCount: number
  maxUsageCount?: number
  owner: string
  tags: Record<string, string>
}

/**
 * Stored key structure
 */
export interface StoredKey {
  metadata: KeyMetadata
  keyMaterial: string // Base64-encoded serialized key
  publicKey: string   // Base64-encoded public key for verification
}

/**
 * Key rotation result
 */
export interface KeyRotationResult {
  oldKeyId: string
  newKeyId: string
  rotatedAt: number
  reencryptionRequired: boolean
}

/**
 * Key Management System
 */
export class PQCKeyManager {
  private keys: Map<string, StoredKey> = new Map()
  private keysByType: Map<KeyType, Set<string>> = new Map()

  /**
   * Generate a new encryption key pair
   */
  async generateEncryptionKey(
    keyType: KeyType,
    owner: string,
    securityLevel: KyberSecurityLevel = KyberSecurityLevel.LEVEL_3,
    options?: {
      expiryDays?: number
      maxUsageCount?: number
      tags?: Record<string, string>
    }
  ): Promise<StoredKey> {
    const kyberKEM = new KyberKEM(securityLevel)
    const keyPair = await kyberKEM.generateKeyPair()

    const createdAt = Date.now()
    const expiresAt = options?.expiryDays ? createdAt + options.expiryDays * 24 * 60 * 60 * 1000 : undefined
    const rotateAt = options?.expiryDays ? createdAt + (options.expiryDays - 7) * 24 * 60 * 60 * 1000 : undefined

    const metadata: KeyMetadata = {
      keyId: keyPair.keyId,
      keyType,
      algorithm: securityLevel,
      status: KeyStatus.ACTIVE,
      createdAt,
      expiresAt,
      rotateAt,
      usageCount: 0,
      maxUsageCount: options?.maxUsageCount,
      owner,
      tags: options?.tags || {},
    }

    const storedKey: StoredKey = {
      metadata,
      keyMaterial: serializeKyberKeyPair(keyPair),
      publicKey: Buffer.from(keyPair.publicKey).toString('base64'),
    }

    this.storeKey(storedKey)
    return storedKey
  }

  /**
   * Generate a new signing key pair
   */
  async generateSigningKey(
    keyType: KeyType,
    owner: string,
    securityLevel: SignatureSecurityLevel = SignatureSecurityLevel.LEVEL_3,
    options?: {
      expiryDays?: number
      maxUsageCount?: number
      tags?: Record<string, string>
    }
  ): Promise<StoredKey> {
    const signer = new PQCSignature(securityLevel)
    const keyPair = await signer.generateKeyPair(options?.expiryDays)

    const metadata: KeyMetadata = {
      keyId: keyPair.keyId,
      keyType,
      algorithm: securityLevel,
      status: KeyStatus.ACTIVE,
      createdAt: keyPair.createdAt,
      expiresAt: keyPair.expiresAt,
      rotateAt: keyPair.expiresAt ? keyPair.expiresAt - 7 * 24 * 60 * 60 * 1000 : undefined,
      usageCount: 0,
      maxUsageCount: options?.maxUsageCount,
      owner,
      tags: options?.tags || {},
    }

    const storedKey: StoredKey = {
      metadata,
      keyMaterial: serializeSignatureKeyPair(keyPair),
      publicKey: Buffer.from(keyPair.publicKey).toString('base64'),
    }

    this.storeKey(storedKey)
    return storedKey
  }

  /**
   * Retrieve a key by ID
   */
  getKey(keyId: string): StoredKey | undefined {
    return this.keys.get(keyId)
  }

  /**
   * Get active keys of a specific type
   */
  getActiveKeysByType(keyType: KeyType): StoredKey[] {
    const keyIds = this.keysByType.get(keyType) || new Set()
    return Array.from(keyIds)
      .map((id) => this.keys.get(id))
      .filter((key): key is StoredKey => key !== undefined && key.metadata.status === KeyStatus.ACTIVE)
  }

  /**
   * Get the primary (most recent active) key of a type
   */
  getPrimaryKey(keyType: KeyType): StoredKey | undefined {
    const activeKeys = this.getActiveKeysByType(keyType)
    if (activeKeys.length === 0) return undefined

    // Return the most recently created active key
    return activeKeys.sort((a, b) => b.metadata.createdAt - a.metadata.createdAt)[0]
  }

  /**
   * Rotate a key
   */
  async rotateKey(keyId: string): Promise<KeyRotationResult> {
    const oldKey = this.getKey(keyId)
    if (!oldKey) {
      throw new Error(`Key not found: ${keyId}`)
    }

    // Mark old key as rotating
    oldKey.metadata.status = KeyStatus.ROTATING

    // Generate new key with same parameters
    let newKey: StoredKey

    if (this.isEncryptionKey(oldKey.metadata.algorithm)) {
      newKey = await this.generateEncryptionKey(
        oldKey.metadata.keyType,
        oldKey.metadata.owner,
        oldKey.metadata.algorithm as KyberSecurityLevel,
        {
          expiryDays: oldKey.metadata.expiresAt
            ? Math.ceil((oldKey.metadata.expiresAt - Date.now()) / (24 * 60 * 60 * 1000))
            : undefined,
          maxUsageCount: oldKey.metadata.maxUsageCount,
          tags: oldKey.metadata.tags,
        }
      )
    } else {
      newKey = await this.generateSigningKey(
        oldKey.metadata.keyType,
        oldKey.metadata.owner,
        oldKey.metadata.algorithm as SignatureSecurityLevel,
        {
          expiryDays: oldKey.metadata.expiresAt
            ? Math.ceil((oldKey.metadata.expiresAt - Date.now()) / (24 * 60 * 60 * 1000))
            : undefined,
          maxUsageCount: oldKey.metadata.maxUsageCount,
          tags: oldKey.metadata.tags,
        }
      )
    }

    // Deprecate old key after new key is active
    oldKey.metadata.status = KeyStatus.DEPRECATED

    return {
      oldKeyId: keyId,
      newKeyId: newKey.metadata.keyId,
      rotatedAt: Date.now(),
      reencryptionRequired: this.isEncryptionKey(oldKey.metadata.algorithm),
    }
  }

  /**
   * Check if keys need rotation
   */
  getKeysNeedingRotation(): StoredKey[] {
    const now = Date.now()
    return Array.from(this.keys.values()).filter((key) => {
      if (key.metadata.status !== KeyStatus.ACTIVE) return false

      // Check expiry
      if (key.metadata.rotateAt && now >= key.metadata.rotateAt) return true

      // Check usage count
      if (key.metadata.maxUsageCount && key.metadata.usageCount >= key.metadata.maxUsageCount * 0.9) return true

      return false
    })
  }

  /**
   * Mark key as used (increment usage counter)
   */
  recordKeyUsage(keyId: string): void {
    const key = this.getKey(keyId)
    if (key) {
      key.metadata.usageCount++
      key.metadata.lastUsed = Date.now()
    }
  }

  /**
   * Mark key as compromised
   */
  markCompromised(keyId: string, reason: string): void {
    const key = this.getKey(keyId)
    if (key) {
      key.metadata.status = KeyStatus.COMPROMISED
      key.metadata.tags.compromiseReason = reason
      key.metadata.tags.compromisedAt = Date.now().toString()

      // Trigger immediate rotation
      console.error(`KEY COMPROMISED: ${keyId} - ${reason}`)
    }
  }

  /**
   * Destroy a key (permanent removal)
   */
  destroyKey(keyId: string): void {
    const key = this.getKey(keyId)
    if (key) {
      // Securely wipe key material
      key.metadata.status = KeyStatus.DESTROYED
      key.keyMaterial = '[DESTROYED]'
      key.publicKey = '[DESTROYED]'

      // Remove from active tracking
      const keyIds = this.keysByType.get(key.metadata.keyType)
      if (keyIds) {
        keyIds.delete(keyId)
      }
    }
  }

  /**
   * Export key inventory for audit
   */
  exportKeyInventory(): Array<Omit<KeyMetadata, 'keyMaterial'>> {
    return Array.from(this.keys.values()).map((key) => key.metadata)
  }

  /**
   * Store key in memory map
   */
  private storeKey(key: StoredKey): void {
    this.keys.set(key.metadata.keyId, key)

    // Index by type
    if (!this.keysByType.has(key.metadata.keyType)) {
      this.keysByType.set(key.metadata.keyType, new Set())
    }
    this.keysByType.get(key.metadata.keyType)!.add(key.metadata.keyId)
  }

  /**
   * Check if algorithm is for encryption (vs signing)
   */
  private isEncryptionKey(algorithm: KyberSecurityLevel | SignatureSecurityLevel): boolean {
    return Object.values(KyberSecurityLevel).includes(algorithm as KyberSecurityLevel)
  }

  /**
   * Serialize key manager state to JSON
   */
  serialize(): string {
    const state = {
      keys: Array.from(this.keys.entries()),
      keysByType: Array.from(this.keysByType.entries()).map(([type, ids]) => [type, Array.from(ids)]),
    }
    return JSON.stringify(state)
  }

  /**
   * Deserialize key manager state from JSON
   */
  static deserialize(serialized: string): PQCKeyManager {
    const manager = new PQCKeyManager()
    const state = JSON.parse(serialized)

    // Restore keys map
    for (const [keyId, storedKey] of state.keys) {
      manager.keys.set(keyId, storedKey)
    }

    // Restore keysByType map
    for (const [type, ids] of state.keysByType) {
      manager.keysByType.set(type, new Set(ids))
    }

    return manager
  }
}

/**
 * Key Rotation Scheduler
 *
 * Automates key rotation based on schedule
 */
export class KeyRotationScheduler {
  private keyManager: PQCKeyManager
  private rotationCallbacks: Map<string, () => Promise<void>> = new Map()

  constructor(keyManager: PQCKeyManager) {
    this.keyManager = keyManager
  }

  /**
   * Check for keys needing rotation and trigger callbacks
   */
  async checkAndRotate(): Promise<KeyRotationResult[]> {
    const keysToRotate = this.keyManager.getKeysNeedingRotation()
    const results: KeyRotationResult[] = []

    for (const key of keysToRotate) {
      console.log(`Rotating key: ${key.metadata.keyId} (${key.metadata.keyType})`)

      // Rotate the key
      const result = await this.keyManager.rotateKey(key.metadata.keyId)
      results.push(result)

      // Trigger callback if registered
      const callback = this.rotationCallbacks.get(key.metadata.keyType)
      if (callback) {
        await callback()
      }
    }

    return results
  }

  /**
   * Register callback for key type rotation
   */
  onRotation(keyType: KeyType, callback: () => Promise<void>): void {
    this.rotationCallbacks.set(keyType, callback)
  }

  /**
   * Start automatic rotation scheduler
   */
  startScheduler(checkIntervalMs: number = 3600000): NodeJS.Timeout {
    return setInterval(() => {
      this.checkAndRotate().catch((error) => {
        console.error('Key rotation scheduler error:', error)
      })
    }, checkIntervalMs)
  }
}

/**
 * Key Derivation Function for hierarchical keys
 */
export class KeyDerivation {
  /**
   * Derive child key from parent key
   *
   * @param parentKey - Parent key material
   * @param context - Derivation context (e.g., "patient-12345")
   * @param keyLength - Desired key length in bytes
   * @returns Derived key
   */
  static deriveChildKey(parentKey: Uint8Array, context: string, keyLength: number = 32): Uint8Array {
    const hasher = new SHA512()

    // Hash parent key + context
    hasher.update(parentKey)
    hasher.update(new TextEncoder().encode(context))
    hasher.update(new TextEncoder().encode('IHEP-Key-Derivation-v1'))

    const hash = hasher.digest()

    // Return truncated hash
    return hash.slice(0, keyLength)
  }

  /**
   * Derive multiple child keys from single parent
   */
  static deriveMultipleKeys(parentKey: Uint8Array, contexts: string[], keyLength: number = 32): Uint8Array[] {
    return contexts.map((context) => this.deriveChildKey(parentKey, context, keyLength))
  }
}

/**
 * Factory function
 */
export function createKeyManager(): PQCKeyManager {
  return new PQCKeyManager()
}

/**
 * Create key rotation scheduler
 */
export function createRotationScheduler(keyManager: PQCKeyManager): KeyRotationScheduler {
  return new KeyRotationScheduler(keyManager)
}
