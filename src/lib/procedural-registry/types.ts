export type DeletionDecision = 'DENY' | 'DEFER' | 'APPROVE' | 'REQUIRE_APPROVAL';

export interface RegistryConfig {
  retentionPolicies: {
    hipaaDays: number;
    pciDays: number;
    defaultDays: number;
  };
  synergyThreshold: number;
  storageQuotaGb: number;
  storageCriticalThreshold: number;
  legalHolds: string[];
  requiredApprovers: string[];
}

export interface Fragment {
  fragment_id: string;
  created_at?: string;
  timestamp?: string;
  synergy_score?: number;
  type?: string;
  rare_source?: boolean;
}

export interface StorageStats {
  total_fragments: number;
}

export interface FragmentationDataSource {
  get_fragment(fragmentId: string, principalId: string): Promise<Fragment | null>;
  get_synergies(fragmentId: string, principalId: string): Promise<unknown[]>;
  get_statistics(): Promise<StorageStats>;
}

export interface DeletionRequest {
  request_id: string;
  fragment_id: string;
  requesting_principal: string;
  requested_at: string;
  reason: string;
  decision?: DeletionDecision;
  decision_reason?: string;
  decided_at?: string;
}

export interface EvaluationResult {
  request_id: string;
  fragment_id: string;
  decision: DeletionDecision;
  reason_code: string;
  detail: string;
  decided_at: string;
  approvers_required?: string[];
}
