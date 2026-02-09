import { randomUUID } from 'crypto';
import type {
  DeletionDecision,
  DeletionRequest,
  EvaluationResult,
  Fragment,
  FragmentationDataSource,
  RegistryConfig,
} from './types';

const nowIso = (): string => new Date().toISOString();

const defaultConfig = (): RegistryConfig => ({
  retentionPolicies: {
    hipaaDays: 6 * 365,
    pciDays: 1 * 365,
    defaultDays: 10 * 365,
  },
  synergyThreshold: 0.7,
  storageQuotaGb: 1000,
  storageCriticalThreshold: 0.85,
  legalHolds: [],
  requiredApprovers: ['security_lead', 'compliance_officer', 'data_scientist'],
});

export class ProceduralRegistry {
  private readonly fragmentationDb: FragmentationDataSource;
  private readonly config: RegistryConfig;
  private readonly decisions: DeletionRequest[] = [];

  constructor(fragmentationDb: FragmentationDataSource, config?: Partial<RegistryConfig>) {
    this.fragmentationDb = fragmentationDb;
    this.config = { ...defaultConfig(), ...config } as RegistryConfig;
  }

  async evaluateDeletionRequest(
    fragmentId: string,
    requestingPrincipal: string,
    reason = 'Storage optimization',
  ): Promise<EvaluationResult> {
    const request: DeletionRequest = {
      request_id: randomUUID(),
      fragment_id: fragmentId,
      requesting_principal: requestingPrincipal,
      requested_at: nowIso(),
      reason,
    };

    const fragment = await this.fragmentationDb.get_fragment(fragmentId, 'registry');
    if (!fragment) {
      return this.deny(request, 'FRAGMENT_NOT_FOUND', 'Fragment does not exist');
    }

    const decision = await this.runPipeline(request, fragment);
    this.decisions.push(request);
    return decision;
  }

  private async runPipeline(
    request: DeletionRequest,
    fragment: Fragment,
  ): Promise<EvaluationResult> {
    // 1. Legal holds
    if (this.config.legalHolds.includes(fragment.fragment_id)) {
      return this.deny(request, 'LEGAL_HOLD', 'Fragment under legal/compliance hold');
    }

    // 2. Retention policy
    const retention = this.checkRetention(fragment);
    if (!retention.canDelete) {
      return this.deny(request, 'HIPAA_RETENTION', retention.reason);
    }

    // 3. Synergy value
    const synergy = this.checkSynergy(fragment);
    if (!synergy.canDelete) {
      return this.deny(request, 'HIGH_SYNERGY', synergy.reason);
    }

    // 4. Active correlations
    const correlations = await this.checkCorrelations(fragment);
    if (!correlations.canDelete) {
      return this.deny(request, 'ACTIVE_CORRELATIONS', correlations.reason);
    }

    // 5. Predictive value
    const predictive = this.checkPredictiveValue(fragment);
    if (!predictive.canDelete) {
      return this.deny(request, 'PREDICTED_VALUE', predictive.reason);
    }

    // 6. Storage criticality
    const storage = await this.checkStorage();
    if (!storage.critical) {
      return this.defer(request, 'STORAGE_NOT_CRITICAL', storage.reason);
    }

    // Require multi-approver sign-off
    return this.requireApproval(request, fragment);
  }

  private checkRetention(fragment: Fragment): { canDelete: boolean; reason: string } {
    const createdAtStr = fragment.created_at ?? fragment.timestamp;
    if (!createdAtStr) {
      return { canDelete: false, reason: 'Cannot determine fragment age' };
    }
    let ageDays: number;
    try {
      const created = new Date(createdAtStr);
      ageDays = Math.floor((Date.now() - created.getTime()) / (1000 * 60 * 60 * 24));
    } catch (err) {
      return { canDelete: false, reason: `Invalid timestamp: ${String(err)}` };
    }
    const hipaaRetention = this.config.retentionPolicies.hipaaDays;
    if (ageDays < hipaaRetention) {
      return {
        canDelete: false,
        reason: `HIPAA retention: ${ageDays} days old; must be at least ${hipaaRetention} days`,
      };
    }
    return { canDelete: true, reason: `Age ${ageDays} days exceeds retention minimum` };
  }

  private checkSynergy(fragment: Fragment): { canDelete: boolean; reason: string } {
    const score = fragment.synergy_score ?? 0;
    const threshold = this.config.synergyThreshold;
    if (score > threshold) {
      return {
        canDelete: false,
        reason: `High synergy: score ${score.toFixed(2)} exceeds threshold ${threshold}`,
      };
    }
    return { canDelete: true, reason: `Synergy ${score.toFixed(2)} below threshold` };
  }

  private async checkCorrelations(fragment: Fragment): Promise<{ canDelete: boolean; reason: string }> {
    try {
      const synergies = await this.fragmentationDb.get_synergies(fragment.fragment_id, 'registry');
      if (synergies.length > 0) {
        return {
          canDelete: false,
          reason: `${synergies.length} active correlations depend on this fragment`,
        };
      }
      return { canDelete: true, reason: 'No active correlations' };
    } catch (err) {
      return { canDelete: false, reason: `Cannot verify correlations: ${String(err)}` };
    }
  }

  private checkPredictiveValue(fragment: Fragment): { canDelete: boolean; reason: string } {
    const highValueTypes = new Set([
      'failed_login',
      'port_scan',
      'anomaly',
      'reconnaissance',
      'unusual_access',
    ]);
    if (fragment.type && highValueTypes.has(fragment.type)) {
      return {
        canDelete: false,
        reason: `Type "${fragment.type}" has high predictive value for future correlation`,
      };
    }
    if (fragment.rare_source) {
      return { canDelete: false, reason: 'Fragment from rare source - high correlation potential' };
    }
    return { canDelete: true, reason: 'Low predicted future value' };
  }

  private async checkStorage(): Promise<{ critical: boolean; reason: string }> {
    const stats = await this.fragmentationDb.get_statistics();
    const estimatedStorageGb = (stats.total_fragments * 1) / 1024; // ~1KB per fragment
    const quota = this.config.storageQuotaGb;
    const usageRatio = quota > 0 ? estimatedStorageGb / quota : 0;
    if (usageRatio < this.config.storageCriticalThreshold) {
      return {
        critical: false,
        reason: `Storage not critical: ${(usageRatio * 100).toFixed(1)}% used (${estimatedStorageGb.toFixed(
          1,
        )}GB / ${quota}GB). Retain fragment.`,
      };
    }
    return {
      critical: true,
      reason: `Storage critical: ${(usageRatio * 100).toFixed(1)}% used (${estimatedStorageGb.toFixed(
        1,
      )}GB / ${quota}GB)`,
    };
  }

  private deny(request: DeletionRequest, reasonCode: string, detail: string): EvaluationResult {
    return this.finishDecision(request, 'DENY', reasonCode, detail);
  }

  private defer(request: DeletionRequest, reasonCode: string, detail: string): EvaluationResult {
    return this.finishDecision(request, 'DEFER', reasonCode, detail);
  }

  private requireApproval(request: DeletionRequest, fragment: Fragment): EvaluationResult {
    const detail = `Multi-approver required for fragment ${fragment.fragment_id}`;
    return this.finishDecision(request, 'REQUIRE_APPROVAL', 'MULTI_APPROVER_REQUIRED', detail, this.config.requiredApprovers);
  }

  private finishDecision(
    request: DeletionRequest,
    decision: DeletionDecision,
    reasonCode: string,
    detail: string,
    approvers?: string[],
  ): EvaluationResult {
    request.decision = decision;
    request.decision_reason = `${reasonCode}: ${detail}`;
    request.decided_at = nowIso();
    return {
      request_id: request.request_id,
      fragment_id: request.fragment_id,
      decision,
      reason_code: reasonCode,
      detail,
      decided_at: request.decided_at,
      approvers_required: approvers,
    };
  }
}
