export interface ApprovalRequest {
  id: string;
  category: string;
  priority: number;
  requesting_agent: string;
  department: string;
  action_type: string;
  action_payload: Record<string, any>;
  context: string;
  draft_content: string | null;
  status: 'PENDING' | 'APPROVED' | 'REJECTED' | 'EXPIRED' | 'CANCELLED';
  reviewer: string | null;
  review_notes: string | null;
  created_at: string;
  reviewed_at: string | null;
  expires_at: string | null;
}

export interface Department {
  id: string;
  name: string;
  cluster: string;
  description: string;
  head_agent_id: string;
}

export interface Agent {
  id: string;
  department_id: string;
  role: string;
  name: string;
  system_prompt: string;
  capabilities: string[];
  config: Record<string, any>;
  active: boolean;
  last_heartbeat: string | null;
  created_at: string;
}

export interface AuditEntry {
  id: string;
  timestamp: string;
  agent_id: string;
  department: string;
  action_type: string;
  action_details: Record<string, any> | null;
  approval_id: string | null;
  compliance_flags: string[];
  outcome: 'SUCCESS' | 'FAILURE' | 'BLOCKED' | 'PENDING';
  error_message: string | null;
  duration_ms: number | null;
}

export interface Task {
  id: string;
  task_type: string;
  payload: Record<string, any>;
  assigned_agent: string | null;
  assigned_department: string | null;
  priority: number;
  status: 'QUEUED' | 'ASSIGNED' | 'IN_PROGRESS' | 'COMPLETED' | 'FAILED' | 'CANCELLED';
  result: Record<string, any> | null;
  error_message: string | null;
  retry_count: number;
  max_retries: number;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
}

export interface DepartmentStats {
  department_id: string;
  name: string;
  cluster: string;
  agent_count: number;
  pending_approvals: number;
  completed_tasks: number;
  failed_tasks: number;
}

export interface SystemMetrics {
  total_agents: number;
  active_agents: number;
  pending_approvals: number;
  tasks_queued: number;
  tasks_completed_today: number;
  tasks_failed_today: number;
  departments: DepartmentStats[];
}

// ================== Investor Portal Types ==================

export interface InvestmentCategory {
  id: string;
  name: string;
  description: string | null;
  display_order: number;
  icon_name: string | null;
  active: boolean;
  created_at: string;
}

export interface InvestmentPhase {
  id: string;
  phase_number: number;
  name: string;
  description: string | null;
  start_year: number;
  end_year: number;
  total_budget: number | null;
  participant_target_min: number | null;
  participant_target_max: number | null;
  key_milestones: Array<{ year: number; milestone: string }>;
}

export interface InvestmentItem {
  id: string;
  category_id: string;
  name: string;
  description: string | null;
  unit_price: number;
  min_quantity: number;
  max_quantity: number | null;
  price_type: 'fixed' | 'monthly' | 'annual' | 'per_unit';
  phase_1_applicable: boolean;
  phase_2_applicable: boolean;
  phase_3_applicable: boolean;
  phase_4_applicable: boolean;
  roi_multiplier: number | null;
  roi_timeline_months: number | null;
  annual_return_rate: number | null;
  specs: Record<string, any>;
  featured: boolean;
  active: boolean;
  created_at: string;
  // Joined fields
  category_name?: string;
}

export type ContactCompanyType =
  | 'vc'
  | 're_developer'
  | 'coworking'
  | 'strategic'
  | 'individual'
  | 'foundation'
  | 'corporate';

export type ContactStatus =
  | 'prospect'
  | 'contacted'
  | 'qualified'
  | 'negotiating'
  | 'committed'
  | 'closed'
  | 'declined';

export interface InvestorContact {
  id: string;
  first_name: string | null;
  last_name: string | null;
  email: string | null;
  phone: string | null;
  company_name: string | null;
  company_type: ContactCompanyType | null;
  job_title: string | null;
  city: string | null;
  state: string | null;
  lead_source: string | null;
  status: ContactStatus;
  investment_interest: string[];
  target_investment_min: number | null;
  target_investment_max: number | null;
  target_locations: string[];
  notes: string | null;
  tags: string[];
  last_contacted_at: string | null;
  next_follow_up: string | null;
  created_at: string;
  updated_at: string;
}

export type InteractionType =
  | 'email'
  | 'call'
  | 'meeting'
  | 'note'
  | 'task'
  | 'proposal_sent'
  | 'contract_sent';

export interface ContactInteraction {
  id: string;
  contact_id: string;
  interaction_type: InteractionType;
  direction: 'inbound' | 'outbound' | null;
  subject: string | null;
  content: string | null;
  metadata: Record<string, any>;
  created_by: string | null;
  created_at: string;
}

export type PartnerStatus =
  | 'target'
  | 'outreach_sent'
  | 'discovery'
  | 'pilot'
  | 'negotiating'
  | 'legal'
  | 'signed'
  | 'active'
  | 'paused'
  | 'declined';

export type PartnerType =
  | 'health_system'
  | 'payer'
  | 'pharma'
  | 'research'
  | 'data'
  | 'platform'
  | 'employer'
  | 'university'
  | 'channel';

export interface PartnerAccount {
  id: string;
  name: string;
  partner_type: PartnerType | null;
  status: PartnerStatus;
  owner: string | null;
  priority: string | null;
  estimated_value: number | null;
  integration_type: string | null;
  notes: string | null;
  last_contacted_at: string | null;
  next_step: string | null;
  created_at: string;
  updated_at: string;
}

export interface PartnerAccountContact {
  partner_account_id: string;
  contact_id: string;
  role: string | null;
  is_primary: boolean;
  created_at: string;
  // Joined fields
  contact_name?: string;
  email?: string | null;
  job_title?: string | null;
  company_name?: string | null;
}

export type REProspectStatus =
  | 'identified'
  | 'contacted'
  | 'touring'
  | 'negotiating'
  | 'loi_signed'
  | 'closed'
  | 'declined';

export interface REProspect {
  id: string;
  contact_id: string;
  property_type: string | null;
  market: 'Orlando' | 'Miami' | string;
  address: string | null;
  square_footage: number | null;
  monthly_lease_rate: number | null;
  proposed_term_months: number;
  total_lease_value: number | null;
  status: REProspectStatus;
  notes: string | null;
  created_at: string;
  // Joined fields
  contact_name?: string;
  company_name?: string;
}

export type PackageStatus =
  | 'draft'
  | 'submitted'
  | 'under_review'
  | 'approved'
  | 'contracted'
  | 'funded'
  | 'cancelled';

export interface InvestmentPackage {
  id: string;
  contact_id: string | null;
  name: string | null;
  status: PackageStatus;
  total_investment: number;
  projected_total_return: number;
  projected_irr: number | null;
  payback_months: number | null;
  target_phases: number[];
  contract_document_url: string | null;
  submitted_at: string | null;
  reviewed_at: string | null;
  reviewed_by: string | null;
  review_notes: string | null;
  created_at: string;
  // Joined fields
  contact_name?: string;
  line_items?: PackageLineItem[];
}

export interface PhaseAllocation {
  '1': number;
  '2': number;
  '3': number;
  '4': number;
}

export interface PackageLineItem {
  id: string;
  package_id: string;
  investment_item_id: string;
  quantity: number;
  unit_price: number;
  total_price: number;
  phase_allocation: PhaseAllocation;
  projected_return: number | null;
  created_at: string;
  // Joined fields
  item_name?: string;
  item_category?: string;
}

export type ContractStatus =
  | 'draft'
  | 'sent'
  | 'investor_signed'
  | 'fully_executed'
  | 'cancelled';

export interface InvestmentContract {
  id: string;
  package_id: string | null;
  contact_id: string | null;
  contract_type: string | null;
  version: number;
  content_markdown: string | null;
  content_html: string | null;
  pdf_url: string | null;
  status: ContractStatus;
  investor_signed_at: string | null;
  company_signed_at: string | null;
  created_at: string;
  // Joined fields
  contact_name?: string;
  package_name?: string;
}

// Investor Portal Dashboard Stats
export interface InvestorPortalStats {
  total_contacts: number;
  active_prospects: number;
  packages_in_review: number;
  total_committed: number;
  pipeline_value: number;
  categories: InvestmentCategory[];
  phases: InvestmentPhase[];
}

// ================== Investment Ledger Types ==================

export type LedgerEntryType = 'commitment' | 'payment_received' | 'refund' | 'adjustment';
export type PaymentMethod = 'wire' | 'ach' | 'check' | 'crypto';
export type AccountingSystem = 'quickbooks' | 'xero' | 'netsuite';
export type SyncStatus = 'pending' | 'synced' | 'failed';

export interface LedgerEntry {
  id: string;
  package_id: string;
  contact_id: string | null;
  entry_type: LedgerEntryType;
  amount: number;
  running_balance: number;
  reference_number: string | null;
  payment_method: PaymentMethod | null;
  bank_reference: string | null;
  notes: string | null;
  recorded_by: string | null;
  created_at: string;
  // Joined fields
  package_name?: string;
  contact_name?: string;
}

export interface PaymentReceipt {
  id: string;
  ledger_entry_id: string | null;
  package_id: string;
  amount: number;
  payment_date: string;
  payment_method: string;
  sender_name: string | null;
  sender_bank: string | null;
  sender_account_last4: string | null;
  reference_number: string | null;
  confirmation_number: string | null;
  receipt_document_url: string | null;
  verified: boolean;
  verified_by: string | null;
  verified_at: string | null;
  created_at: string;
}

export interface AccountingSyncLog {
  id: string;
  ledger_entry_id: string;
  external_system: AccountingSystem;
  external_id: string | null;
  sync_status: SyncStatus;
  sync_error: string | null;
  synced_at: string | null;
  created_at: string;
}

// Input types for creating records
export interface CreateLedgerEntry {
  package_id: string;
  contact_id?: string | null;
  entry_type: LedgerEntryType;
  amount: number;
  reference_number?: string;
  payment_method?: PaymentMethod;
  bank_reference?: string;
  notes?: string;
  recorded_by?: string;
}

export interface CreatePaymentReceipt {
  package_id: string;
  amount: number;
  payment_date: string;
  payment_method: string;
  sender_name?: string;
  sender_bank?: string;
  sender_account_last4?: string;
  reference_number?: string;
  confirmation_number?: string;
  receipt_document_url?: string;
}

export interface PaymentDetails {
  amount: number;
  payment_date: string;
  payment_method: PaymentMethod;
  sender_name?: string;
  sender_bank?: string;
  sender_account_last4?: string;
  reference_number?: string;
  confirmation_number?: string;
  notes?: string;
  recorded_by?: string;
}

// ================== Proposal Document Types ==================

export type DocumentType = 'proposal' | 'pitch_deck' | 'term_sheet' | 'contract_draft' | 'other';
export type DocumentEntityType = 'contact' | 'partner' | 'global';

export interface ProposalDocument {
  id: string;
  entity_type: DocumentEntityType;
  entity_id: string | null;
  file_name: string;
  file_type: string;
  file_size: number;
  document_type: DocumentType;
  description: string | null;
  tags: string[];
  uploaded_by: string | null;
  created_at: string;
  // Note: file_data (bytea) excluded — fetched separately via download route
}

// ================== Threat Response Types ==================

export interface ThreatEvent {
  id: string;
  source: string;  // suricata, crowdsec, fail2ban, ic3
  severity: 'low' | 'medium' | 'high' | 'critical';
  description: string;
  source_ip: string | null;
  destination_ip: string | null;
  rule_id: string | null;
  action_taken: string | null;
  metadata: Record<string, any>;
  created_at: string;
}

export interface ThreatSummary {
  total_events_24h: number;
  critical_count: number;
  high_count: number;
  blocked_ips: number;
  active_jails: number;
  suricata_rules: number;
  crowdsec_decisions: number;
}

// ================== Campaign Types ==================

export type CampaignStatus = 'draft' | 'active' | 'paused' | 'completed' | 'cancelled';

export interface CampaignRecord {
  id: string;
  name: string;
  description: string | null;
  audience: string | null;
  channels: string[];
  budget: number | null;
  status: CampaignStatus;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
}

export interface CampaignStepRecord {
  id: string;
  campaign_id: string;
  name: string;
  step_type: string;
  config: Record<string, any>;
  status: string;
  executed_at: string | null;
  result: Record<string, any>;
  created_at: string;
}

export interface CampaignMetrics {
  id: string;
  campaign_id: string;
  metrics: Record<string, any>;
  created_at: string;
}

// ================== Project Timeline Types ==================

export type ProjectStatus = 'active' | 'completed' | 'on_hold' | 'cancelled';
export type MilestoneStatus = 'pending' | 'in_progress' | 'completed' | 'blocked' | 'cancelled';

export interface ProjectTimelineRecord {
  id: string;
  name: string;
  description: string | null;
  status: ProjectStatus;
  created_at: string;
  // Computed fields
  milestone_count?: number;
  completed_milestones?: number;
}

export interface ProjectMilestoneRecord {
  id: string;
  project_id: string;
  name: string;
  target_date: string | null;
  actual_date: string | null;
  status: MilestoneStatus;
  depends_on: string[];
  created_at: string;
}

// ================== Discovery Engine Types ==================

export type CandidateStatus = 'discovered' | 'scored' | 'qualified' | 'promoted' | 'rejected' | 'duplicate';

export type DiscoveryCategory =
  | 'venture_capital'
  | 'angel_investor'
  | 'philanthropist'
  | 'medical_insurance'
  | 'real_estate'
  | 'tech_manufacturer'
  | 'service_provider'
  | 'growth_equity'
  | 'grant_program'
  | 'government_grant'
  | 'foundation_grant';

export type SweepStatus = 'running' | 'completed' | 'failed' | 'partial';

export type SweepSource =
  | 'perplexity_mcp'
  | 'perplexity_api'
  | 'sec_edgar'
  | 'crunchbase'
  | 'github'
  | 'browser'
  | 'manual'
  | 'grant_search';

export type EnrichmentType =
  | 'email_pattern'
  | 'email_verify'
  | 'linkedin'
  | 'phone'
  | 'firm_data'
  | 'portfolio'
  | 'recent_activity';

export type EnrichmentStatus = 'pending' | 'completed' | 'failed' | 'skipped';

export interface DiscoverySweep {
  id: string;
  sweep_type: string;
  category: DiscoveryCategory;
  source: SweepSource;
  query_params: Record<string, any> | null;
  results_count: number;
  new_candidates: number;
  duplicates_found: number;
  status: SweepStatus;
  error_message: string | null;
  started_at: string;
  completed_at: string | null;
}

export interface InvestorCandidate {
  id: string;
  sweep_id: string | null;
  name: string;
  firm: string | null;
  title: string | null;
  email: string | null;
  linkedin_url: string | null;
  website: string | null;
  category: DiscoveryCategory;
  source: SweepSource;
  raw_data: Record<string, any> | null;
  total_score: number;
  thesis_alignment_score: number;
  check_size_score: number;
  stage_fit_score: number;
  portfolio_synergy_score: number;
  activity_recency_score: number;
  accessibility_score: number;
  geographic_score: number;
  scoring_rationale: string | null;
  status: CandidateStatus;
  promoted_at: string | null;
  pipeline_id: string | null;
  hubspot_id: string | null;
  fingerprint: string | null;
  created_at: string;
  updated_at: string;
}

export interface EnrichmentLogEntry {
  id: string;
  candidate_id: string;
  enrichment_type: EnrichmentType;
  source: string | null;
  status: EnrichmentStatus;
  input_data: Record<string, any> | null;
  result_data: Record<string, any> | null;
  confidence: number | null;
  created_at: string;
  completed_at: string | null;
}

export interface DiscoveryStats {
  total_candidates: number;
  promoted_count: number;
  rejected_count: number;
  avg_score: number;
  active_sweeps: number;
  total_sweeps: number;
  enrichments_completed: number;
}

export interface CategoryStats {
  category: DiscoveryCategory;
  candidate_count: number;
  avg_score: number;
  promoted_count: number;
  qualified_count: number;
}

// ================== Service Health Types ==================

export interface ServiceHealth {
  name: string;
  url: string;
  status: 'healthy' | 'degraded' | 'down' | 'unknown';
  response_time_ms: number | null;
  last_checked: string;
  details: Record<string, any>;
}

// ================== Procedural Registry Types ==================

export type EnforcementLevel = 'advisory' | 'soft' | 'hard';
export type ProcedureCategory = 'agent' | 'service' | 'workflow' | 'deployment' | 'api';
export type RuleType = 'require' | 'prohibit' | 'limit' | 'sequence';
export type RuleSeverity = 'info' | 'warning' | 'error';
export type EnforcementResult = 'logged' | 'warned' | 'blocked';

export interface Procedure {
  id: string;
  name: string;
  description: string | null;
  category: ProcedureCategory;
  enforcement_level: EnforcementLevel;
  active: boolean;
  created_at: string;
  updated_at: string;
  // Joined fields
  rules?: ProcedureRule[];
  assignments?: ProcedureAssignment[];
  rule_count?: number;
  assignment_count?: number;
}

export interface ProcedureRule {
  id: string;
  procedure_id: string;
  rule_type: RuleType;
  condition: Record<string, unknown>;
  message: string;
  severity: RuleSeverity;
  created_at: string;
}

export interface ProcedureAssignment {
  id: string;
  procedure_id: string;
  target_type: string;
  target_id: string | null;
  priority: number;
  created_at: string;
}

export interface ProcedureViolation {
  id: string;
  procedure_id: string;
  rule_id: string;
  actor_type: string;
  actor_id: string;
  action: string;
  context: Record<string, unknown> | null;
  enforcement_result: EnforcementResult;
  created_at: string;
  // Joined fields
  procedure_name?: string;
  rule_message?: string;
}

export interface ProcedureExecution {
  id: string;
  procedure_id: string;
  actor_type: string;
  actor_id: string;
  action: string;
  passed: boolean;
  rules_evaluated: number;
  rules_failed: number;
  execution_ms: number;
  created_at: string;
}

export interface CreateProcedure {
  name: string;
  description?: string;
  category: ProcedureCategory;
  enforcement_level?: EnforcementLevel;
}

export interface CreateProcedureRule {
  procedure_id: string;
  rule_type: RuleType;
  condition: Record<string, unknown>;
  message: string;
  severity?: RuleSeverity;
}

export interface CreateProcedureAssignment {
  procedure_id: string;
  target_type: string;
  target_id?: string | null;
  priority?: number;
}

export interface CreateViolation {
  procedure_id: string;
  rule_id: string;
  actor_type: string;
  actor_id: string;
  action: string;
  context?: Record<string, unknown>;
  enforcement_result: EnforcementResult;
}

export interface CreateExecution {
  procedure_id: string;
  actor_type: string;
  actor_id: string;
  action: string;
  passed: boolean;
  rules_evaluated: number;
  rules_failed: number;
  execution_ms: number;
}

export interface ValidationRequest {
  actor_type: string;
  actor_id: string;
  action: string;
  context?: Record<string, unknown>;
}

export interface ValidationResult {
  allowed: boolean;
  enforcement_level: EnforcementLevel;
  violations: Array<{
    procedure_id: string;
    procedure_name: string;
    rule_id: string;
    message: string;
    severity: RuleSeverity;
  }>;
  execution_ms: number;
}

export interface ViolationFilters {
  procedure_id?: string;
  actor_type?: string;
  actor_id?: string;
  enforcement_result?: EnforcementResult;
  start_date?: string;
  end_date?: string;
  limit?: number;
  offset?: number;
}

export interface ViolationStats {
  total_violations: number;
  logged_count: number;
  warned_count: number;
  blocked_count: number;
  by_procedure: Array<{
    procedure_id: string;
    procedure_name: string;
    count: number;
  }>;
  by_actor: Array<{
    actor_type: string;
    actor_id: string;
    count: number;
  }>;
}

export interface ProcedureStats {
  total_procedures: number;
  active_procedures: number;
  violations_24h: number;
  blocked_24h: number;
  executions_24h: number;
  by_category: Array<{
    category: ProcedureCategory;
    count: number;
  }>;
  by_enforcement: Array<{
    enforcement_level: EnforcementLevel;
    count: number;
  }>;
}
