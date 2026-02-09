import { query, queryOne } from './db';
import { calculatePackageProjection, calculateEffectiveTotalPrice } from './investment-calculations';
import type {
  ApprovalRequest,
  Department,
  Agent,
  AuditEntry,
  Task,
  SystemMetrics,
  DepartmentStats,
  InvestmentCategory,
  InvestmentItem,
  InvestmentPhase,
  InvestorContact,
  ContactInteraction,
  PartnerAccount,
  PartnerAccountContact,
  PartnerStatus,
  PartnerType,
  REProspect,
  InvestmentPackage,
  PackageLineItem,
  InvestmentContract,
  InvestorPortalStats,
  ContactStatus,
  ContactCompanyType,
  REProspectStatus,
  PackageStatus,
  ContractStatus,
  PhaseAllocation,
  LedgerEntry,
  PaymentReceipt,
  CreateLedgerEntry,
  PaymentDetails,
  ProposalDocument,
  DocumentType,
  DocumentEntityType,
  ThreatEvent,
  ThreatSummary,
  CampaignRecord,
  CampaignStepRecord,
  CampaignMetrics,
  CampaignStatus,
  ProjectTimelineRecord,
  ProjectMilestoneRecord,
  ProjectStatus,
  MilestoneStatus,
  ServiceHealth,
  DiscoverySweep,
  InvestorCandidate,
  EnrichmentLogEntry,
  DiscoveryStats,
  CategoryStats,
  CandidateStatus,
  DiscoveryCategory,
  SweepStatus,
  // Procedural Registry types
  Procedure,
  ProcedureRule,
  ProcedureAssignment,
  ProcedureViolation,
  ProcedureExecution,
  ProcedureCategory,
  EnforcementLevel,
  CreateProcedure,
  CreateProcedureRule,
  CreateProcedureAssignment,
  CreateViolation,
  CreateExecution,
  ViolationFilters,
  ViolationStats,
  ProcedureStats,
} from './types';

// Approval Requests
export async function getApprovalRequests(status?: string, department?: string, limit = 50): Promise<ApprovalRequest[]> {
  let sql = `
    SELECT id, category, priority, requesting_agent, department, action_type,
           action_payload, context, draft_content, status, reviewer, review_notes,
           created_at, reviewed_at, expires_at
    FROM approval_requests
    WHERE 1=1
  `;
  const params: any[] = [];

  if (status) {
    params.push(status);
    sql += ` AND status = $${params.length}`;
  }

  if (department) {
    params.push(department);
    sql += ` AND department = $${params.length}`;
  }

  params.push(limit);
  sql += ` ORDER BY priority ASC, created_at DESC LIMIT $${params.length}`;

  return query<ApprovalRequest>(sql, params);
}

export async function getApprovalRequest(id: string): Promise<ApprovalRequest | null> {
  return queryOne<ApprovalRequest>(
    `SELECT * FROM approval_requests WHERE id = $1`,
    [id]
  );
}

export async function approveRequest(id: string, reviewer: string, notes: string = ''): Promise<ApprovalRequest | null> {
  return queryOne<ApprovalRequest>(
    `UPDATE approval_requests
     SET status = 'APPROVED', reviewer = $2, review_notes = $3, reviewed_at = NOW()
     WHERE id = $1
     RETURNING *`,
    [id, reviewer, notes]
  );
}

export async function rejectRequest(id: string, reviewer: string, reason: string): Promise<ApprovalRequest | null> {
  return queryOne<ApprovalRequest>(
    `UPDATE approval_requests
     SET status = 'REJECTED', reviewer = $2, review_notes = $3, reviewed_at = NOW()
     WHERE id = $1
     RETURNING *`,
    [id, reviewer, reason]
  );
}

export async function updateApprovalContent(
  id: string,
  editedContent: {
    subject: string;
    body: string;
    to_email: string;
    to_name: string;
    firm?: string;
    contact_id?: string;
    deal_id?: string;
  }
): Promise<ApprovalRequest | null> {
  // Get current approval to merge payload
  const current = await getApprovalRequest(id);
  if (!current) return null;

  // Update action_payload with edited content
  const updatedPayload = {
    ...current.action_payload,
    subject: editedContent.subject,
    body: editedContent.body,
    body_text: editedContent.body,
    to_email: editedContent.to_email,
    to_name: editedContent.to_name,
    firm: editedContent.firm || current.action_payload?.firm,
    contact_id: editedContent.contact_id || current.action_payload?.contact_id,
    deal_id: editedContent.deal_id || current.action_payload?.deal_id,
    edited_by_human: true,
  };

  // Update draft_content with new subject and body
  const updatedDraftContent = `To: ${editedContent.to_name} <${editedContent.to_email}>
Subject: ${editedContent.subject}

${editedContent.body}`;

  return queryOne<ApprovalRequest>(
    `UPDATE approval_requests
     SET action_payload = $2, draft_content = $3
     WHERE id = $1
     RETURNING *`,
    [id, JSON.stringify(updatedPayload), updatedDraftContent]
  );
}

// Departments
export async function getDepartments(): Promise<Department[]> {
  return query<Department>(`SELECT * FROM departments ORDER BY cluster, name`);
}

export async function getDepartment(id: string): Promise<Department | null> {
  return queryOne<Department>(`SELECT * FROM departments WHERE id = $1`, [id]);
}

// Agents
export async function getAgents(departmentId?: string): Promise<Agent[]> {
  if (departmentId) {
    return query<Agent>(
      `SELECT * FROM agents WHERE department_id = $1 ORDER BY role DESC, name`,
      [departmentId]
    );
  }
  return query<Agent>(`SELECT * FROM agents ORDER BY department_id, role DESC, name`);
}

export async function getAgent(id: string): Promise<Agent | null> {
  return queryOne<Agent>(`SELECT * FROM agents WHERE id = $1`, [id]);
}

// Tasks
export async function getTasks(status?: string, limit = 50): Promise<Task[]> {
  let sql = `SELECT * FROM task_queue WHERE 1=1`;
  const params: any[] = [];

  if (status) {
    params.push(status);
    sql += ` AND status = $${params.length}`;
  }

  params.push(limit);
  sql += ` ORDER BY priority ASC, created_at DESC LIMIT $${params.length}`;

  return query<Task>(sql, params);
}

// Audit Log
export async function getAuditLog(limit = 100, agentId?: string): Promise<AuditEntry[]> {
  let sql = `SELECT * FROM audit_log WHERE 1=1`;
  const params: any[] = [];

  if (agentId) {
    params.push(agentId);
    sql += ` AND agent_id = $${params.length}`;
  }

  params.push(limit);
  sql += ` ORDER BY timestamp DESC LIMIT $${params.length}`;

  return query<AuditEntry>(sql, params);
}

// System Metrics
export async function getSystemMetrics(): Promise<SystemMetrics> {
  const [
    agentStats,
    approvalStats,
    taskStats,
    departmentStats
  ] = await Promise.all([
    query<{ total: string; active: string }>(`
      SELECT
        COUNT(*) as total,
        COUNT(*) FILTER (WHERE active = true) as active
      FROM agents
    `),
    query<{ pending: string }>(`
      SELECT COUNT(*) as pending FROM approval_requests WHERE status = 'PENDING'
    `),
    query<{ queued: string; completed_today: string; failed_today: string }>(`
      SELECT
        COUNT(*) FILTER (WHERE status = 'QUEUED') as queued,
        COUNT(*) FILTER (WHERE status = 'COMPLETED' AND completed_at >= CURRENT_DATE) as completed_today,
        COUNT(*) FILTER (WHERE status = 'FAILED' AND completed_at >= CURRENT_DATE) as failed_today
      FROM task_queue
    `),
    query<DepartmentStats>(`
      SELECT
        d.id as department_id,
        d.name,
        d.cluster,
        COUNT(DISTINCT a.id) as agent_count,
        COUNT(DISTINCT ar.id) FILTER (WHERE ar.status = 'PENDING') as pending_approvals,
        COUNT(DISTINCT t.id) FILTER (WHERE t.status = 'COMPLETED') as completed_tasks,
        COUNT(DISTINCT t.id) FILTER (WHERE t.status = 'FAILED') as failed_tasks
      FROM departments d
      LEFT JOIN agents a ON a.department_id = d.id
      LEFT JOIN approval_requests ar ON ar.department = d.id
      LEFT JOIN task_queue t ON t.assigned_department = d.id
      GROUP BY d.id, d.name, d.cluster
      ORDER BY d.cluster, d.name
    `)
  ]);

  return {
    total_agents: parseInt(agentStats[0]?.total || '0'),
    active_agents: parseInt(agentStats[0]?.active || '0'),
    pending_approvals: parseInt(approvalStats[0]?.pending || '0'),
    tasks_queued: parseInt(taskStats[0]?.queued || '0'),
    tasks_completed_today: parseInt(taskStats[0]?.completed_today || '0'),
    tasks_failed_today: parseInt(taskStats[0]?.failed_today || '0'),
    departments: departmentStats.map(d => ({
      ...d,
      agent_count: typeof d.agent_count === 'string' ? parseInt(d.agent_count) : d.agent_count,
      pending_approvals: typeof d.pending_approvals === 'string' ? parseInt(d.pending_approvals) : d.pending_approvals,
      completed_tasks: typeof d.completed_tasks === 'string' ? parseInt(d.completed_tasks) : d.completed_tasks,
      failed_tasks: typeof d.failed_tasks === 'string' ? parseInt(d.failed_tasks) : d.failed_tasks,
    }))
  };
}

// ================== Investor Portal Functions ==================

// Investment Categories
export async function getInvestmentCategories(): Promise<InvestmentCategory[]> {
  return query<InvestmentCategory>(
    `SELECT * FROM investment_categories WHERE active = true ORDER BY display_order, name`
  );
}

export async function getInvestmentCategory(id: string): Promise<InvestmentCategory | null> {
  return queryOne<InvestmentCategory>(
    `SELECT * FROM investment_categories WHERE id = $1`,
    [id]
  );
}

// Investment Phases
export async function getInvestmentPhases(): Promise<InvestmentPhase[]> {
  return query<InvestmentPhase>(
    `SELECT * FROM investment_phases ORDER BY phase_number`
  );
}

export async function getInvestmentPhase(phaseNumber: number): Promise<InvestmentPhase | null> {
  return queryOne<InvestmentPhase>(
    `SELECT * FROM investment_phases WHERE phase_number = $1`,
    [phaseNumber]
  );
}

// Investment Items (Catalog)
export async function getInvestmentItems(categoryId?: string, featured?: boolean): Promise<InvestmentItem[]> {
  let sql = `
    SELECT i.*, c.name as category_name
    FROM investment_items i
    JOIN investment_categories c ON i.category_id = c.id
    WHERE i.active = true
  `;
  const params: any[] = [];

  if (categoryId) {
    params.push(categoryId);
    sql += ` AND i.category_id = $${params.length}`;
  }

  if (featured !== undefined) {
    params.push(featured);
    sql += ` AND i.featured = $${params.length}`;
  }

  sql += ` ORDER BY i.featured DESC, c.display_order, i.unit_price ASC`;

  return query<InvestmentItem>(sql, params);
}

export async function getInvestmentItem(id: string): Promise<InvestmentItem | null> {
  return queryOne<InvestmentItem>(
    `SELECT i.*, c.name as category_name
     FROM investment_items i
     JOIN investment_categories c ON i.category_id = c.id
     WHERE i.id = $1`,
    [id]
  );
}

// Investor Contacts (CRM)
export async function getInvestorContacts(
  status?: ContactStatus,
  companyType?: ContactCompanyType,
  limit = 100
): Promise<InvestorContact[]> {
  let sql = `SELECT * FROM investor_contacts WHERE 1=1`;
  const params: any[] = [];

  if (status) {
    params.push(status);
    sql += ` AND status = $${params.length}`;
  }

  if (companyType) {
    params.push(companyType);
    sql += ` AND company_type = $${params.length}`;
  }

  params.push(limit);
  sql += ` ORDER BY updated_at DESC LIMIT $${params.length}`;

  return query<InvestorContact>(sql, params);
}

export async function getInvestorContact(id: string): Promise<InvestorContact | null> {
  return queryOne<InvestorContact>(
    `SELECT * FROM investor_contacts WHERE id = $1`,
    [id]
  );
}

export async function createInvestorContact(contact: Omit<InvestorContact, 'id' | 'created_at' | 'updated_at'>): Promise<InvestorContact | null> {
  return queryOne<InvestorContact>(
    `INSERT INTO investor_contacts (
      first_name, last_name, email, phone, company_name, company_type,
      job_title, city, state, lead_source, status, investment_interest,
      target_investment_min, target_investment_max, target_locations, notes, tags,
      last_contacted_at, next_follow_up
    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19)
    RETURNING *`,
    [
      contact.first_name, contact.last_name, contact.email, contact.phone,
      contact.company_name, contact.company_type, contact.job_title,
      contact.city, contact.state, contact.lead_source, contact.status || 'prospect',
      JSON.stringify(contact.investment_interest || []),
      contact.target_investment_min, contact.target_investment_max,
      JSON.stringify(contact.target_locations || []),
      contact.notes, JSON.stringify(contact.tags || []),
      contact.last_contacted_at, contact.next_follow_up
    ]
  );
}

export async function updateInvestorContact(id: string, updates: Partial<InvestorContact>): Promise<InvestorContact | null> {
  const fields: string[] = [];
  const params: any[] = [];

  const allowedFields = [
    'first_name', 'last_name', 'email', 'phone', 'company_name', 'company_type',
    'job_title', 'city', 'state', 'lead_source', 'status', 'investment_interest',
    'target_investment_min', 'target_investment_max', 'target_locations', 'notes',
    'tags', 'last_contacted_at', 'next_follow_up'
  ];

  for (const [key, value] of Object.entries(updates)) {
    if (allowedFields.includes(key)) {
      params.push(Array.isArray(value) ? JSON.stringify(value) : value);
      fields.push(`${key} = $${params.length}`);
    }
  }

  if (fields.length === 0) return getInvestorContact(id);

  params.push(id);
  const sql = `UPDATE investor_contacts SET ${fields.join(', ')}, updated_at = NOW() WHERE id = $${params.length} RETURNING *`;

  return queryOne<InvestorContact>(sql, params);
}

export async function deleteInvestorContact(id: string): Promise<boolean> {
  const result = await queryOne<{ id: string }>(
    `DELETE FROM investor_contacts WHERE id = $1 RETURNING id`,
    [id]
  );
  return result !== null;
}

// Contact Interactions
export async function getContactInteractions(contactId: string, limit = 50): Promise<ContactInteraction[]> {
  return query<ContactInteraction>(
    `SELECT * FROM contact_interactions WHERE contact_id = $1 ORDER BY created_at DESC LIMIT $2`,
    [contactId, limit]
  );
}

export async function createContactInteraction(
  interaction: Omit<ContactInteraction, 'id' | 'created_at'>
): Promise<ContactInteraction | null> {
  return queryOne<ContactInteraction>(
    `INSERT INTO contact_interactions (contact_id, interaction_type, direction, subject, content, metadata, created_by)
     VALUES ($1, $2, $3, $4, $5, $6, $7)
     RETURNING *`,
    [
      interaction.contact_id,
      interaction.interaction_type,
      interaction.direction,
      interaction.subject,
      interaction.content,
      JSON.stringify(interaction.metadata || {}),
      interaction.created_by
    ]
  );
}

// Partner Accounts (Strategic Partnerships)
export async function getPartnerAccounts(
  status?: PartnerStatus,
  partnerType?: PartnerType,
  limit = 100
): Promise<PartnerAccount[]> {
  let sql = `SELECT * FROM partner_accounts WHERE 1=1`;
  const params: any[] = [];

  if (status) {
    params.push(status);
    sql += ` AND status = $${params.length}`;
  }

  if (partnerType) {
    params.push(partnerType);
    sql += ` AND partner_type = $${params.length}`;
  }

  params.push(limit);
  sql += ` ORDER BY updated_at DESC LIMIT $${params.length}`;

  return query<PartnerAccount>(sql, params);
}

export async function getPartnerAccount(id: string): Promise<PartnerAccount | null> {
  return queryOne<PartnerAccount>(
    `SELECT * FROM partner_accounts WHERE id = $1`,
    [id]
  );
}

export async function createPartnerAccount(
  account: Omit<PartnerAccount, 'id' | 'created_at' | 'updated_at'>
): Promise<PartnerAccount | null> {
  return queryOne<PartnerAccount>(
    `INSERT INTO partner_accounts (
      name, partner_type, status, owner, priority, estimated_value,
      integration_type, notes, last_contacted_at, next_step
    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
    RETURNING *`,
    [
      account.name,
      account.partner_type,
      account.status || 'target',
      account.owner,
      account.priority,
      account.estimated_value,
      account.integration_type,
      account.notes,
      account.last_contacted_at,
      account.next_step,
    ]
  );
}

export async function updatePartnerAccount(
  id: string,
  updates: Partial<PartnerAccount>
): Promise<PartnerAccount | null> {
  const fields: string[] = [];
  const params: any[] = [];

  const allowedFields = [
    'name',
    'partner_type',
    'status',
    'owner',
    'priority',
    'estimated_value',
    'integration_type',
    'notes',
    'last_contacted_at',
    'next_step',
  ];

  for (const [key, value] of Object.entries(updates)) {
    if (allowedFields.includes(key)) {
      params.push(value);
      fields.push(`${key} = $${params.length}`);
    }
  }

  if (fields.length === 0) return getPartnerAccount(id);

  params.push(id);
  const sql = `UPDATE partner_accounts SET ${fields.join(', ')}, updated_at = NOW() WHERE id = $${params.length} RETURNING *`;
  return queryOne<PartnerAccount>(sql, params);
}

export async function deletePartnerAccount(id: string): Promise<boolean> {
  const result = await queryOne<{ id: string }>(
    `DELETE FROM partner_accounts WHERE id = $1 RETURNING id`,
    [id]
  );
  return result !== null;
}

export async function getPartnerAccountContacts(partnerAccountId: string): Promise<PartnerAccountContact[]> {
  return query<PartnerAccountContact>(
    `SELECT pac.*, 
            CONCAT(c.first_name, ' ', c.last_name) as contact_name,
            c.email, c.job_title, c.company_name
     FROM partner_account_contacts pac
     JOIN investor_contacts c ON pac.contact_id = c.id
     WHERE pac.partner_account_id = $1
     ORDER BY pac.is_primary DESC, c.last_name ASC`,
    [partnerAccountId]
  );
}

export async function linkPartnerContact(
  partnerAccountId: string,
  contactId: string,
  role?: string | null,
  isPrimary: boolean = false
): Promise<PartnerAccountContact | null> {
  if (isPrimary) {
    await query(
      `UPDATE partner_account_contacts SET is_primary = FALSE WHERE partner_account_id = $1`,
      [partnerAccountId]
    );
  }

  return queryOne<PartnerAccountContact>(
    `INSERT INTO partner_account_contacts (partner_account_id, contact_id, role, is_primary)
     VALUES ($1, $2, $3, $4)
     ON CONFLICT (partner_account_id, contact_id)
     DO UPDATE SET role = EXCLUDED.role, is_primary = EXCLUDED.is_primary
     RETURNING *`,
    [partnerAccountId, contactId, role, isPrimary]
  );
}

export async function unlinkPartnerContact(
  partnerAccountId: string,
  contactId: string
): Promise<boolean> {
  const result = await queryOne<{ partner_account_id: string }>(
    `DELETE FROM partner_account_contacts WHERE partner_account_id = $1 AND contact_id = $2 RETURNING partner_account_id`,
    [partnerAccountId, contactId]
  );
  return result !== null;
}

// RE Prospects
export async function getREProspects(market?: string, status?: REProspectStatus): Promise<REProspect[]> {
  let sql = `
    SELECT p.*, CONCAT(c.first_name, ' ', c.last_name) as contact_name, c.company_name
    FROM re_prospects p
    JOIN investor_contacts c ON p.contact_id = c.id
    WHERE 1=1
  `;
  const params: any[] = [];

  if (market) {
    params.push(market);
    sql += ` AND p.market = $${params.length}`;
  }

  if (status) {
    params.push(status);
    sql += ` AND p.status = $${params.length}`;
  }

  sql += ` ORDER BY p.created_at DESC`;

  return query<REProspect>(sql, params);
}

export async function getREProspect(id: string): Promise<REProspect | null> {
  return queryOne<REProspect>(
    `SELECT p.*, CONCAT(c.first_name, ' ', c.last_name) as contact_name, c.company_name
     FROM re_prospects p
     JOIN investor_contacts c ON p.contact_id = c.id
     WHERE p.id = $1`,
    [id]
  );
}

export async function createREProspect(prospect: Omit<REProspect, 'id' | 'created_at' | 'contact_name' | 'company_name'>): Promise<REProspect | null> {
  return queryOne<REProspect>(
    `INSERT INTO re_prospects (contact_id, property_type, market, address, square_footage,
     monthly_lease_rate, proposed_term_months, total_lease_value, status, notes)
     VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
     RETURNING *`,
    [
      prospect.contact_id, prospect.property_type, prospect.market, prospect.address,
      prospect.square_footage, prospect.monthly_lease_rate, prospect.proposed_term_months,
      prospect.total_lease_value, prospect.status || 'identified', prospect.notes
    ]
  );
}

export async function updateREProspect(id: string, updates: Partial<REProspect>): Promise<REProspect | null> {
  const fields: string[] = [];
  const params: any[] = [];

  const allowedFields = [
    'property_type', 'market', 'address', 'square_footage', 'monthly_lease_rate',
    'proposed_term_months', 'total_lease_value', 'status', 'notes'
  ];

  for (const [key, value] of Object.entries(updates)) {
    if (allowedFields.includes(key)) {
      params.push(value);
      fields.push(`${key} = $${params.length}`);
    }
  }

  if (fields.length === 0) return getREProspect(id);

  params.push(id);
  const sql = `UPDATE re_prospects SET ${fields.join(', ')} WHERE id = $${params.length} RETURNING *`;

  return queryOne<REProspect>(sql, params);
}

// Investment Packages
export async function getInvestmentPackages(contactId?: string, status?: PackageStatus): Promise<InvestmentPackage[]> {
  let sql = `
    SELECT p.*, CONCAT(c.first_name, ' ', c.last_name) as contact_name
    FROM investment_packages p
    LEFT JOIN investor_contacts c ON p.contact_id = c.id
    WHERE 1=1
  `;
  const params: any[] = [];

  if (contactId) {
    params.push(contactId);
    sql += ` AND p.contact_id = $${params.length}`;
  }

  if (status) {
    params.push(status);
    sql += ` AND p.status = $${params.length}`;
  }

  sql += ` ORDER BY p.created_at DESC`;

  return query<InvestmentPackage>(sql, params);
}

export async function getInvestmentPackage(id: string): Promise<InvestmentPackage | null> {
  const pkg = await queryOne<InvestmentPackage>(
    `SELECT p.*, CONCAT(c.first_name, ' ', c.last_name) as contact_name
     FROM investment_packages p
     LEFT JOIN investor_contacts c ON p.contact_id = c.id
     WHERE p.id = $1`,
    [id]
  );

  if (pkg) {
    pkg.line_items = await getPackageLineItems(id);
  }

  return pkg;
}

export async function createInvestmentPackage(pkg: {
  contact_id?: string;
  name?: string;
  target_phases?: number[];
}): Promise<InvestmentPackage | null> {
  return queryOne<InvestmentPackage>(
    `INSERT INTO investment_packages (contact_id, name, target_phases)
     VALUES ($1, $2, $3)
     RETURNING *`,
    [pkg.contact_id, pkg.name, JSON.stringify(pkg.target_phases || [1, 2, 3, 4])]
  );
}

export async function updateInvestmentPackage(id: string, updates: Partial<InvestmentPackage>): Promise<InvestmentPackage | null> {
  const fields: string[] = [];
  const params: any[] = [];

  const allowedFields = [
    'contact_id', 'name', 'status', 'total_investment', 'projected_total_return',
    'projected_irr', 'payback_months', 'target_phases', 'contract_document_url',
    'submitted_at', 'reviewed_at', 'reviewed_by', 'review_notes'
  ];

  for (const [key, value] of Object.entries(updates)) {
    if (allowedFields.includes(key)) {
      params.push(Array.isArray(value) ? JSON.stringify(value) : value);
      fields.push(`${key} = $${params.length}`);
    }
  }

  if (fields.length === 0) return getInvestmentPackage(id);

  params.push(id);
  const sql = `UPDATE investment_packages SET ${fields.join(', ')} WHERE id = $${params.length} RETURNING *`;

  return queryOne<InvestmentPackage>(sql, params);
}

export async function deleteInvestmentPackage(id: string): Promise<boolean> {
  const result = await queryOne<{ id: string }>(
    `DELETE FROM investment_packages WHERE id = $1 RETURNING id`,
    [id]
  );
  return result !== null;
}

// Package Line Items
export async function getPackageLineItems(packageId: string): Promise<PackageLineItem[]> {
  return query<PackageLineItem>(
    `SELECT li.*, i.name as item_name, c.name as item_category
     FROM package_line_items li
     JOIN investment_items i ON li.investment_item_id = i.id
     JOIN investment_categories c ON i.category_id = c.id
     WHERE li.package_id = $1
     ORDER BY li.created_at`,
    [packageId]
  );
}

export async function addPackageLineItem(item: {
  package_id: string;
  investment_item_id: string;
  quantity: number;
  unit_price: number;
  phase_allocation?: PhaseAllocation;
}): Promise<PackageLineItem | null> {
  // Fetch item details for price_type and specs
  const investmentItem = await queryOne<{ price_type: string; specs: Record<string, any>; roi_multiplier: number | null }>(
    `SELECT price_type, specs, roi_multiplier FROM investment_items WHERE id = $1`,
    [item.investment_item_id]
  );
  const specs = investmentItem?.specs ?? {};
  const priceType = investmentItem?.price_type ?? 'fixed';
  const totalPrice = calculateEffectiveTotalPrice(item.unit_price, item.quantity, priceType, specs);
  const roiMultiplier = investmentItem?.roi_multiplier ?? 7.0;
  const projectedReturn = totalPrice * Number(roiMultiplier);
  const allocation = item.phase_allocation || { '1': 25, '2': 25, '3': 25, '4': 25 };

  const lineItem = await queryOne<PackageLineItem>(
    `INSERT INTO package_line_items (package_id, investment_item_id, quantity, unit_price, total_price, phase_allocation, projected_return)
     VALUES ($1, $2, $3, $4, $5, $6, $7)
     RETURNING *`,
    [item.package_id, item.investment_item_id, item.quantity, item.unit_price, totalPrice, JSON.stringify(allocation), projectedReturn]
  );

  // Recalculate package totals
  if (lineItem) {
    await recalculatePackageTotals(item.package_id);
  }

  return lineItem;
}

export async function updatePackageLineItem(id: string, updates: {
  quantity?: number;
  phase_allocation?: PhaseAllocation;
}): Promise<PackageLineItem | null> {
  const current = await queryOne<PackageLineItem & { investment_item_id: string }>(
    `SELECT * FROM package_line_items WHERE id = $1`,
    [id]
  );

  if (!current) return null;

  // Fetch item details for price_type and specs
  const investmentItem = await queryOne<{ price_type: string; specs: Record<string, any>; roi_multiplier: number | null }>(
    `SELECT price_type, specs, roi_multiplier FROM investment_items WHERE id = $1`,
    [current.investment_item_id]
  );
  const specs = investmentItem?.specs ?? {};
  const priceType = investmentItem?.price_type ?? 'fixed';

  const quantity = updates.quantity ?? current.quantity;
  const totalPrice = calculateEffectiveTotalPrice(Number(current.unit_price), quantity, priceType, specs);
  const allocation = updates.phase_allocation ?? current.phase_allocation;

  const updated = await queryOne<PackageLineItem>(
    `UPDATE package_line_items
     SET quantity = $2, total_price = $3, phase_allocation = $4
     WHERE id = $1
     RETURNING *`,
    [id, quantity, totalPrice, JSON.stringify(allocation)]
  );

  if (updated) {
    await recalculatePackageTotals(current.package_id);
  }

  return updated;
}

export async function removePackageLineItem(id: string): Promise<boolean> {
  const item = await queryOne<PackageLineItem>(
    `SELECT package_id FROM package_line_items WHERE id = $1`,
    [id]
  );

  if (!item) return false;

  await queryOne<{ id: string }>(
    `DELETE FROM package_line_items WHERE id = $1 RETURNING id`,
    [id]
  );

  await recalculatePackageTotals(item.package_id);
  return true;
}

export async function recalculatePackageTotals(packageId: string): Promise<void> {
  // Fetch line items with investment item details for proper financial modeling
  const lineItems = await query<PackageLineItem & { roi_multiplier: number | null; roi_timeline_months: number | null }>(
    `SELECT li.*, i.roi_multiplier, i.roi_timeline_months
     FROM package_line_items li
     JOIN investment_items i ON li.investment_item_id = i.id
     WHERE li.package_id = $1`,
    [packageId]
  );

  if (lineItems.length === 0) {
    await queryOne(
      `UPDATE investment_packages
       SET total_investment = 0, projected_total_return = 0, projected_irr = NULL, payback_months = NULL
       WHERE id = $1`,
      [packageId]
    );
    return;
  }

  // Use calculatePackageProjection for proper IRR (Newton-Raphson), payback, and cash flow modeling
  const projection = calculatePackageProjection(
    lineItems.map(li => ({
      total_price: Number(li.total_price),
      phase_allocation: typeof li.phase_allocation === 'string'
        ? JSON.parse(li.phase_allocation as unknown as string)
        : li.phase_allocation,
      investment_item: {
        roi_multiplier: li.roi_multiplier != null ? Number(li.roi_multiplier) : null,
        roi_timeline_months: li.roi_timeline_months != null ? Number(li.roi_timeline_months) : null,
      },
    }))
  );

  await queryOne(
    `UPDATE investment_packages
     SET total_investment = $2, projected_total_return = $3, projected_irr = $4, payback_months = $5
     WHERE id = $1`,
    [packageId, projection.totalInvestment, projection.projectedTotalReturn, projection.projectedIRR, projection.paybackMonths]
  );
}

// Investment Contracts
export async function getInvestmentContracts(packageId?: string, contactId?: string): Promise<InvestmentContract[]> {
  let sql = `
    SELECT ct.*, CONCAT(c.first_name, ' ', c.last_name) as contact_name, p.name as package_name
    FROM investment_contracts ct
    LEFT JOIN investor_contacts c ON ct.contact_id = c.id
    LEFT JOIN investment_packages p ON ct.package_id = p.id
    WHERE 1=1
  `;
  const params: any[] = [];

  if (packageId) {
    params.push(packageId);
    sql += ` AND ct.package_id = $${params.length}`;
  }

  if (contactId) {
    params.push(contactId);
    sql += ` AND ct.contact_id = $${params.length}`;
  }

  sql += ` ORDER BY ct.created_at DESC`;

  return query<InvestmentContract>(sql, params);
}

export async function getInvestmentContract(id: string): Promise<InvestmentContract | null> {
  return queryOne<InvestmentContract>(
    `SELECT ct.*, CONCAT(c.first_name, ' ', c.last_name) as contact_name, p.name as package_name
     FROM investment_contracts ct
     LEFT JOIN investor_contacts c ON ct.contact_id = c.id
     LEFT JOIN investment_packages p ON ct.package_id = p.id
     WHERE ct.id = $1`,
    [id]
  );
}

export async function createInvestmentContract(contract: {
  package_id?: string;
  contact_id?: string;
  contract_type?: string;
  content_markdown?: string;
  content_html?: string;
}): Promise<InvestmentContract | null> {
  return queryOne<InvestmentContract>(
    `INSERT INTO investment_contracts (package_id, contact_id, contract_type, content_markdown, content_html)
     VALUES ($1, $2, $3, $4, $5)
     RETURNING *`,
    [contract.package_id, contract.contact_id, contract.contract_type, contract.content_markdown, contract.content_html]
  );
}

export async function updateInvestmentContract(id: string, updates: Partial<InvestmentContract>): Promise<InvestmentContract | null> {
  const fields: string[] = [];
  const params: any[] = [];

  const allowedFields = [
    'contract_type', 'content_markdown', 'content_html', 'pdf_url', 'status',
    'investor_signed_at', 'company_signed_at'
  ];

  for (const [key, value] of Object.entries(updates)) {
    if (allowedFields.includes(key)) {
      params.push(value);
      fields.push(`${key} = $${params.length}`);
    }
  }

  // Handle version increment
  if (updates.content_markdown || updates.content_html) {
    fields.push(`version = version + 1`);
  }

  if (fields.length === 0) return getInvestmentContract(id);

  params.push(id);
  const sql = `UPDATE investment_contracts SET ${fields.join(', ')} WHERE id = $${params.length} RETURNING *`;

  return queryOne<InvestmentContract>(sql, params);
}

// Investor Portal Stats
export async function getInvestorPortalStats(): Promise<InvestorPortalStats> {
  const [
    contactStats,
    packageStats,
    categories,
    phases
  ] = await Promise.all([
    query<{ total: string; active: string }>(`
      SELECT
        COUNT(*) as total,
        COUNT(*) FILTER (WHERE status IN ('contacted', 'qualified', 'negotiating')) as active
      FROM investor_contacts
    `),
    query<{ in_review: string; committed: string; pipeline: string }>(`
      SELECT
        COUNT(*) FILTER (WHERE status IN ('submitted', 'under_review')) as in_review,
        COALESCE(SUM(total_investment) FILTER (WHERE status IN ('contracted', 'funded')), 0) as committed,
        COALESCE(SUM(total_investment) FILTER (WHERE status NOT IN ('cancelled')), 0) as pipeline
      FROM investment_packages
    `),
    getInvestmentCategories(),
    getInvestmentPhases()
  ]);

  return {
    total_contacts: parseInt(contactStats[0]?.total || '0'),
    active_prospects: parseInt(contactStats[0]?.active || '0'),
    packages_in_review: parseInt(packageStats[0]?.in_review || '0'),
    total_committed: parseFloat(packageStats[0]?.committed || '0'),
    pipeline_value: parseFloat(packageStats[0]?.pipeline || '0'),
    categories,
    phases
  };
}

// ================== Package Status Transitions ==================

export async function submitPackage(id: string): Promise<InvestmentPackage | null> {
  const pkg = await queryOne<InvestmentPackage>(
    `SELECT id, status FROM investment_packages WHERE id = $1`,
    [id]
  );
  if (!pkg) return null;
  if (pkg.status !== 'draft') {
    throw new Error('Only draft packages can be submitted');
  }

  // Validate package has line items
  const items = await query<{ count: string }>(
    `SELECT COUNT(*) as count FROM package_line_items WHERE package_id = $1`,
    [id]
  );
  if (parseInt(items[0]?.count || '0') === 0) {
    throw new Error('Package must have at least one line item to submit');
  }

  return queryOne<InvestmentPackage>(
    `UPDATE investment_packages
     SET status = 'submitted', submitted_at = NOW()
     WHERE id = $1
     RETURNING *`,
    [id]
  );
}

export async function startPackageReview(id: string, reviewer: string): Promise<InvestmentPackage | null> {
  const pkg = await queryOne<InvestmentPackage>(
    `SELECT id, status FROM investment_packages WHERE id = $1`,
    [id]
  );
  if (!pkg) return null;
  if (pkg.status !== 'submitted') {
    throw new Error('Only submitted packages can be put under review');
  }

  return queryOne<InvestmentPackage>(
    `UPDATE investment_packages
     SET status = 'under_review', reviewed_by = $2
     WHERE id = $1
     RETURNING *`,
    [id, reviewer]
  );
}

export async function approvePackage(id: string, reviewer: string, notes?: string): Promise<InvestmentPackage | null> {
  const pkg = await queryOne<InvestmentPackage>(
    `SELECT id, status FROM investment_packages WHERE id = $1`,
    [id]
  );
  if (!pkg) return null;
  if (pkg.status !== 'under_review') {
    throw new Error('Only packages under review can be approved');
  }

  return queryOne<InvestmentPackage>(
    `UPDATE investment_packages
     SET status = 'approved', reviewed_at = NOW(), reviewed_by = $2, review_notes = $3
     WHERE id = $1
     RETURNING *`,
    [id, reviewer, notes || null]
  );
}

export async function rejectPackage(id: string, reviewer: string, reason: string): Promise<InvestmentPackage | null> {
  const pkg = await queryOne<InvestmentPackage>(
    `SELECT id, status FROM investment_packages WHERE id = $1`,
    [id]
  );
  if (!pkg) return null;
  if (pkg.status !== 'under_review') {
    throw new Error('Only packages under review can be rejected');
  }

  return queryOne<InvestmentPackage>(
    `UPDATE investment_packages
     SET status = 'cancelled', reviewed_at = NOW(), reviewed_by = $2, review_notes = $3
     WHERE id = $1
     RETURNING *`,
    [id, reviewer, reason]
  );
}

export async function generatePackageContract(id: string): Promise<InvestmentPackage | null> {
  const pkg = await queryOne<InvestmentPackage>(
    `SELECT p.id, p.status, p.contact_id, p.name, p.total_investment
     FROM investment_packages p WHERE p.id = $1`,
    [id]
  );
  if (!pkg) return null;
  if (pkg.status !== 'approved') {
    throw new Error('Only approved packages can generate contracts');
  }

  // Create a contract record
  await queryOne<InvestmentContract>(
    `INSERT INTO investment_contracts (package_id, contact_id, contract_type, status)
     VALUES ($1, $2, 'investment', 'draft')
     RETURNING *`,
    [id, pkg.contact_id]
  );

  return queryOne<InvestmentPackage>(
    `UPDATE investment_packages
     SET status = 'contracted'
     WHERE id = $1
     RETURNING *`,
    [id]
  );
}

export async function fundPackage(id: string, payment: PaymentDetails): Promise<InvestmentPackage | null> {
  const pkg = await queryOne<InvestmentPackage>(
    `SELECT p.id, p.status, p.contact_id, p.total_investment
     FROM investment_packages p WHERE p.id = $1`,
    [id]
  );
  if (!pkg) return null;
  if (pkg.status !== 'contracted') {
    throw new Error('Only contracted packages can be funded');
  }

  // Get current running balance for this package
  const lastEntry = await queryOne<{ running_balance: string }>(
    `SELECT running_balance FROM investment_ledger
     WHERE package_id = $1 ORDER BY created_at DESC LIMIT 1`,
    [id]
  );
  const currentBalance = parseFloat(lastEntry?.running_balance || '0');
  const newBalance = currentBalance + payment.amount;

  // Create ledger entry
  const ledgerEntry = await queryOne<LedgerEntry>(
    `INSERT INTO investment_ledger
     (package_id, contact_id, entry_type, amount, running_balance, reference_number, payment_method, bank_reference, notes, recorded_by)
     VALUES ($1, $2, 'payment_received', $3, $4, $5, $6, $7, $8, $9)
     RETURNING *`,
    [
      id, pkg.contact_id, payment.amount, newBalance,
      payment.reference_number || null, payment.payment_method,
      payment.sender_bank || null, payment.notes || null, payment.recorded_by || null
    ]
  );

  // Create payment receipt
  await queryOne<PaymentReceipt>(
    `INSERT INTO payment_receipts
     (ledger_entry_id, package_id, amount, payment_date, payment_method, sender_name, sender_bank, sender_account_last4, reference_number, confirmation_number)
     VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
     RETURNING *`,
    [
      ledgerEntry?.id, id, payment.amount, payment.payment_date,
      payment.payment_method, payment.sender_name || null,
      payment.sender_bank || null, payment.sender_account_last4 || null,
      payment.reference_number || null, payment.confirmation_number || null
    ]
  );

  // Update package funding totals
  await queryOne(
    `UPDATE investment_packages
     SET amount_received = COALESCE(amount_received, 0) + $2,
         status = 'funded', funded_at = NOW(), funded_by = $3
     WHERE id = $1`,
    [id, payment.amount, payment.recorded_by || null]
  );

  // Update contact totals if contact exists
  if (pkg.contact_id) {
    await queryOne(
      `UPDATE investor_contacts
       SET total_funded = COALESCE(total_funded, 0) + $2
       WHERE id = $1`,
      [pkg.contact_id, payment.amount]
    );
  }

  return getInvestmentPackage(id);
}

// ================== Ledger Operations ==================

export async function getLedgerEntries(filters?: {
  package_id?: string;
  contact_id?: string;
  date_from?: string;
  date_to?: string;
}): Promise<LedgerEntry[]> {
  let sql = `
    SELECT l.*, p.name as package_name, CONCAT(c.first_name, ' ', c.last_name) as contact_name
    FROM investment_ledger l
    LEFT JOIN investment_packages p ON l.package_id = p.id
    LEFT JOIN investor_contacts c ON l.contact_id = c.id
    WHERE 1=1
  `;
  const params: any[] = [];

  if (filters?.package_id) {
    params.push(filters.package_id);
    sql += ` AND l.package_id = $${params.length}`;
  }
  if (filters?.contact_id) {
    params.push(filters.contact_id);
    sql += ` AND l.contact_id = $${params.length}`;
  }
  if (filters?.date_from) {
    params.push(filters.date_from);
    sql += ` AND l.created_at >= $${params.length}`;
  }
  if (filters?.date_to) {
    params.push(filters.date_to);
    sql += ` AND l.created_at <= $${params.length}`;
  }

  sql += ` ORDER BY l.created_at DESC`;

  return query<LedgerEntry>(sql, params);
}

export async function getPackageLedger(packageId: string): Promise<LedgerEntry[]> {
  return query<LedgerEntry>(
    `SELECT l.*, p.name as package_name, CONCAT(c.first_name, ' ', c.last_name) as contact_name
     FROM investment_ledger l
     LEFT JOIN investment_packages p ON l.package_id = p.id
     LEFT JOIN investor_contacts c ON l.contact_id = c.id
     WHERE l.package_id = $1
     ORDER BY l.created_at DESC`,
    [packageId]
  );
}

export async function createLedgerEntry(entry: CreateLedgerEntry): Promise<LedgerEntry | null> {
  // Get current running balance for this package
  const lastEntry = await queryOne<{ running_balance: string }>(
    `SELECT running_balance FROM investment_ledger
     WHERE package_id = $1 ORDER BY created_at DESC LIMIT 1`,
    [entry.package_id]
  );
  const currentBalance = parseFloat(lastEntry?.running_balance || '0');
  const newBalance = entry.entry_type === 'refund'
    ? currentBalance - entry.amount
    : currentBalance + entry.amount;

  return queryOne<LedgerEntry>(
    `INSERT INTO investment_ledger
     (package_id, contact_id, entry_type, amount, running_balance, reference_number, payment_method, bank_reference, notes, recorded_by)
     VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
     RETURNING *`,
    [
      entry.package_id, entry.contact_id || null, entry.entry_type,
      entry.amount, newBalance, entry.reference_number || null,
      entry.payment_method || null, entry.bank_reference || null,
      entry.notes || null, entry.recorded_by || null
    ]
  );
}

// ================== Payment Operations ==================

export async function getPackagePayments(packageId: string): Promise<PaymentReceipt[]> {
  return query<PaymentReceipt>(
    `SELECT * FROM payment_receipts WHERE package_id = $1 ORDER BY payment_date DESC`,
    [packageId]
  );
}

export async function recordPayment(packageId: string, payment: PaymentDetails): Promise<PaymentReceipt | null> {
  // Get package details
  const pkg = await queryOne<InvestmentPackage>(
    `SELECT id, contact_id FROM investment_packages WHERE id = $1`,
    [packageId]
  );
  if (!pkg) return null;

  // Create ledger entry
  const ledgerEntry = await createLedgerEntry({
    package_id: packageId,
    contact_id: pkg.contact_id,
    entry_type: 'payment_received',
    amount: payment.amount,
    reference_number: payment.reference_number,
    payment_method: payment.payment_method,
    bank_reference: payment.sender_bank,
    notes: payment.notes,
    recorded_by: payment.recorded_by,
  });

  // Create payment receipt
  const receipt = await queryOne<PaymentReceipt>(
    `INSERT INTO payment_receipts
     (ledger_entry_id, package_id, amount, payment_date, payment_method, sender_name, sender_bank, sender_account_last4, reference_number, confirmation_number)
     VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
     RETURNING *`,
    [
      ledgerEntry?.id, packageId, payment.amount, payment.payment_date,
      payment.payment_method, payment.sender_name || null,
      payment.sender_bank || null, payment.sender_account_last4 || null,
      payment.reference_number || null, payment.confirmation_number || null
    ]
  );

  // Update package received amount
  await queryOne(
    `UPDATE investment_packages
     SET amount_received = COALESCE(amount_received, 0) + $2
     WHERE id = $1`,
    [packageId, payment.amount]
  );

  return receipt;
}

export async function verifyPayment(receiptId: string, verifiedBy: string): Promise<PaymentReceipt | null> {
  return queryOne<PaymentReceipt>(
    `UPDATE payment_receipts
     SET verified = true, verified_by = $2, verified_at = NOW()
     WHERE id = $1
     RETURNING *`,
    [receiptId, verifiedBy]
  );
}

// ================== Proposal Document Operations ==================

const DOCUMENT_LIST_FIELDS = `id, entity_type, entity_id, file_name, file_type, file_size, document_type, description, tags, uploaded_by, created_at`;

export async function getDocuments(
  entityType?: DocumentEntityType,
  entityId?: string,
  documentType?: DocumentType
): Promise<ProposalDocument[]> {
  let sql = `SELECT ${DOCUMENT_LIST_FIELDS} FROM proposal_documents WHERE 1=1`;
  const params: any[] = [];

  if (entityType) {
    params.push(entityType);
    sql += ` AND entity_type = $${params.length}`;
  }

  if (entityId) {
    params.push(entityId);
    sql += ` AND entity_id = $${params.length}`;
  }

  if (documentType) {
    params.push(documentType);
    sql += ` AND document_type = $${params.length}`;
  }

  sql += ` ORDER BY created_at DESC`;

  return query<ProposalDocument>(sql, params);
}

export async function getDocument(id: string): Promise<ProposalDocument | null> {
  return queryOne<ProposalDocument>(
    `SELECT ${DOCUMENT_LIST_FIELDS} FROM proposal_documents WHERE id = $1`,
    [id]
  );
}

export async function getDocumentData(id: string): Promise<{ file_data: Buffer; file_name: string; file_type: string } | null> {
  return queryOne<{ file_data: Buffer; file_name: string; file_type: string }>(
    `SELECT file_data, file_name, file_type FROM proposal_documents WHERE id = $1`,
    [id]
  );
}

export async function createDocument(doc: {
  entity_type: DocumentEntityType;
  entity_id?: string | null;
  file_name: string;
  file_type: string;
  file_size: number;
  file_data: Buffer;
  document_type?: DocumentType;
  description?: string | null;
  tags?: string[];
  uploaded_by?: string | null;
}): Promise<ProposalDocument | null> {
  return queryOne<ProposalDocument>(
    `INSERT INTO proposal_documents (entity_type, entity_id, file_name, file_type, file_size, file_data, document_type, description, tags, uploaded_by)
     VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
     RETURNING ${DOCUMENT_LIST_FIELDS}`,
    [
      doc.entity_type,
      doc.entity_id || null,
      doc.file_name,
      doc.file_type,
      doc.file_size,
      doc.file_data,
      doc.document_type || 'proposal',
      doc.description || null,
      JSON.stringify(doc.tags || []),
      doc.uploaded_by || null,
    ]
  );
}

export async function deleteDocument(id: string): Promise<boolean> {
  const result = await queryOne<{ id: string }>(
    `DELETE FROM proposal_documents WHERE id = $1 RETURNING id`,
    [id]
  );
  return result !== null;
}

// ================== Threat Response Functions ==================

export async function getThreatEvents(limit = 50): Promise<ThreatEvent[]> {
  try {
    return await query<ThreatEvent>(
      `SELECT * FROM threat_events ORDER BY created_at DESC LIMIT $1`,
      [limit]
    );
  } catch {
    // Table may not exist yet - return empty
    return [];
  }
}

export async function getThreatSummary(): Promise<ThreatSummary> {
  try {
    const [stats] = await Promise.all([
      query<{
        total_events_24h: string;
        critical_count: string;
        high_count: string;
      }>(`
        SELECT
          COUNT(*) as total_events_24h,
          COUNT(*) FILTER (WHERE severity = 'critical') as critical_count,
          COUNT(*) FILTER (WHERE severity = 'high') as high_count
        FROM threat_events
        WHERE created_at >= NOW() - INTERVAL '24 hours'
      `),
    ]);

    return {
      total_events_24h: parseInt(stats[0]?.total_events_24h || '0'),
      critical_count: parseInt(stats[0]?.critical_count || '0'),
      high_count: parseInt(stats[0]?.high_count || '0'),
      blocked_ips: 0,
      active_jails: 5,
      suricata_rules: 47957,
      crowdsec_decisions: 0,
    };
  } catch {
    return {
      total_events_24h: 0,
      critical_count: 0,
      high_count: 0,
      blocked_ips: 0,
      active_jails: 5,
      suricata_rules: 47957,
      crowdsec_decisions: 0,
    };
  }
}

// ================== Campaign Functions ==================

export async function getCampaigns(status?: CampaignStatus, limit = 50): Promise<CampaignRecord[]> {
  try {
    let sql = `SELECT * FROM campaigns WHERE 1=1`;
    const params: any[] = [];

    if (status) {
      params.push(status);
      sql += ` AND status = $${params.length}`;
    }

    params.push(limit);
    sql += ` ORDER BY created_at DESC LIMIT $${params.length}`;

    return await query<CampaignRecord>(sql, params);
  } catch {
    return [];
  }
}

export async function getCampaign(id: string): Promise<CampaignRecord | null> {
  try {
    return await queryOne<CampaignRecord>(
      `SELECT * FROM campaigns WHERE id = $1`,
      [id]
    );
  } catch {
    return null;
  }
}

export async function createCampaign(campaign: {
  name: string;
  description?: string;
  audience?: string;
  channels?: string[];
  budget?: number;
}): Promise<CampaignRecord | null> {
  try {
    return await queryOne<CampaignRecord>(
      `INSERT INTO campaigns (name, description, audience, channels, budget)
       VALUES ($1, $2, $3, $4, $5)
       RETURNING *`,
      [
        campaign.name,
        campaign.description || null,
        campaign.audience || null,
        campaign.channels || [],
        campaign.budget || null,
      ]
    );
  } catch {
    return null;
  }
}

export async function updateCampaign(id: string, updates: Partial<CampaignRecord>): Promise<CampaignRecord | null> {
  try {
    const fields: string[] = [];
    const params: any[] = [];

    const allowedFields = ['name', 'description', 'audience', 'channels', 'budget', 'status'];

    for (const [key, value] of Object.entries(updates)) {
      if (allowedFields.includes(key)) {
        params.push(Array.isArray(value) ? value : value);
        fields.push(`${key} = $${params.length}`);
      }
    }

    // Handle status transitions
    if (updates.status === 'active' && !updates.started_at) {
      fields.push(`started_at = NOW()`);
    }
    if (updates.status === 'completed' && !updates.completed_at) {
      fields.push(`completed_at = NOW()`);
    }

    if (fields.length === 0) return getCampaign(id);

    params.push(id);
    const sql = `UPDATE campaigns SET ${fields.join(', ')} WHERE id = $${params.length} RETURNING *`;
    return await queryOne<CampaignRecord>(sql, params);
  } catch {
    return null;
  }
}

export async function getCampaignSteps(campaignId: string): Promise<CampaignStepRecord[]> {
  try {
    return await query<CampaignStepRecord>(
      `SELECT * FROM campaign_steps WHERE campaign_id = $1 ORDER BY created_at`,
      [campaignId]
    );
  } catch {
    return [];
  }
}

export async function getCampaignMetrics(campaignId: string): Promise<CampaignMetrics[]> {
  try {
    return await query<CampaignMetrics>(
      `SELECT * FROM campaign_metrics WHERE campaign_id = $1 ORDER BY created_at DESC`,
      [campaignId]
    );
  } catch {
    return [];
  }
}

// ================== Project Timeline Functions ==================

export async function getProjects(status?: ProjectStatus, limit = 50): Promise<ProjectTimelineRecord[]> {
  try {
    let sql = `
      SELECT pt.*,
        COUNT(pm.id) as milestone_count,
        COUNT(pm.id) FILTER (WHERE pm.status = 'completed') as completed_milestones
      FROM project_timelines pt
      LEFT JOIN project_milestones pm ON pm.project_id = pt.id
      WHERE 1=1
    `;
    const params: any[] = [];

    if (status) {
      params.push(status);
      sql += ` AND pt.status = $${params.length}`;
    }

    sql += ` GROUP BY pt.id ORDER BY pt.created_at DESC`;

    params.push(limit);
    sql += ` LIMIT $${params.length}`;

    const rows = await query<ProjectTimelineRecord>(sql, params);
    return rows.map(r => ({
      ...r,
      milestone_count: typeof r.milestone_count === 'string' ? parseInt(r.milestone_count) : r.milestone_count,
      completed_milestones: typeof r.completed_milestones === 'string' ? parseInt(r.completed_milestones) : r.completed_milestones,
    }));
  } catch {
    return [];
  }
}

export async function getProject(id: string): Promise<ProjectTimelineRecord | null> {
  try {
    return await queryOne<ProjectTimelineRecord>(
      `SELECT * FROM project_timelines WHERE id = $1`,
      [id]
    );
  } catch {
    return null;
  }
}

export async function getProjectMilestones(projectId: string): Promise<ProjectMilestoneRecord[]> {
  try {
    return await query<ProjectMilestoneRecord>(
      `SELECT * FROM project_milestones WHERE project_id = $1 ORDER BY target_date NULLS LAST, created_at`,
      [projectId]
    );
  } catch {
    return [];
  }
}

export async function updateMilestone(
  id: string,
  updates: { status?: MilestoneStatus; actual_date?: string }
): Promise<ProjectMilestoneRecord | null> {
  try {
    const fields: string[] = [];
    const params: any[] = [];

    if (updates.status) {
      params.push(updates.status);
      fields.push(`status = $${params.length}`);
    }

    if (updates.actual_date) {
      params.push(updates.actual_date);
      fields.push(`actual_date = $${params.length}`);
    }

    if (fields.length === 0) return null;

    params.push(id);
    const sql = `UPDATE project_milestones SET ${fields.join(', ')} WHERE id = $${params.length} RETURNING *`;
    return await queryOne<ProjectMilestoneRecord>(sql, params);
  } catch {
    return null;
  }
}

// ================== Service Health Functions ==================

export async function getServiceHealth(): Promise<ServiceHealth[]> {
  const services = [
    { name: 'LiteLLM Gateway', url: 'http://litellm.ai-inference.svc.cluster.local:4000/health/liveliness' },
    { name: 'Orchestrator', url: 'http://orchestrator.ihep-agents.svc.cluster.local:8080/health' },
    { name: 'PostgreSQL', url: '' },
    { name: 'Redis', url: '' },
  ];

  const results: ServiceHealth[] = [];

  for (const service of services) {
    const health: ServiceHealth = {
      name: service.name,
      url: service.url,
      status: 'unknown',
      response_time_ms: null,
      last_checked: new Date().toISOString(),
      details: {},
    };

    if (service.url) {
      try {
        const start = Date.now();
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), 5000);
        const res = await fetch(service.url, { signal: controller.signal });
        clearTimeout(timeout);
        health.response_time_ms = Date.now() - start;
        health.status = res.ok ? 'healthy' : 'degraded';
        health.details = { status_code: res.status };
      } catch {
        health.status = 'down';
        health.response_time_ms = null;
      }
    } else if (service.name === 'PostgreSQL') {
      // Check via a simple query
      try {
        const start = Date.now();
        await query('SELECT 1');
        health.response_time_ms = Date.now() - start;
        health.status = 'healthy';
      } catch {
        health.status = 'down';
      }
    } else if (service.name === 'Redis') {
      try {
        const start = Date.now();
        const { createConnection } = await import('net');
        await new Promise<void>((resolve, reject) => {
          const sock = createConnection({ host: 'redis.ihep-agents.svc.cluster.local', port: 6379 }, () => {
            sock.write('PING\r\n');
          });
          sock.setTimeout(5000);
          sock.on('data', (data) => {
            const resp = data.toString().trim();
            sock.end();
            if (resp.includes('PONG')) {
              resolve();
            } else {
              reject(new Error(`Unexpected response: ${resp}`));
            }
          });
          sock.on('timeout', () => { sock.destroy(); reject(new Error('timeout')); });
          sock.on('error', reject);
        });
        health.response_time_ms = Date.now() - start;
        health.status = 'healthy';
      } catch {
        health.status = 'down';
      }
    }

    results.push(health);
  }

  return results;
}

// ================== Discovery Engine Functions ==================

export async function getDiscoveryStats(): Promise<DiscoveryStats> {
  try {
    const [candidateStats, sweepStats, enrichmentStats] = await Promise.all([
      query<{
        total: string;
        promoted: string;
        rejected: string;
        avg_score: string;
      }>(`
        SELECT
          COUNT(*) as total,
          COUNT(*) FILTER (WHERE status = 'promoted') as promoted,
          COUNT(*) FILTER (WHERE status = 'rejected') as rejected,
          COALESCE(AVG(total_score) FILTER (WHERE total_score > 0), 0) as avg_score
        FROM investor_candidates
      `),
      query<{ active: string; total: string }>(`
        SELECT
          COUNT(*) FILTER (WHERE status = 'running') as active,
          COUNT(*) as total
        FROM discovery_sweeps
      `),
      query<{ completed: string }>(`
        SELECT COUNT(*) FILTER (WHERE status = 'completed') as completed
        FROM enrichment_log
      `),
    ]);

    return {
      total_candidates: parseInt(candidateStats[0]?.total || '0'),
      promoted_count: parseInt(candidateStats[0]?.promoted || '0'),
      rejected_count: parseInt(candidateStats[0]?.rejected || '0'),
      avg_score: parseFloat(candidateStats[0]?.avg_score || '0'),
      active_sweeps: parseInt(sweepStats[0]?.active || '0'),
      total_sweeps: parseInt(sweepStats[0]?.total || '0'),
      enrichments_completed: parseInt(enrichmentStats[0]?.completed || '0'),
    };
  } catch {
    return {
      total_candidates: 0,
      promoted_count: 0,
      rejected_count: 0,
      avg_score: 0,
      active_sweeps: 0,
      total_sweeps: 0,
      enrichments_completed: 0,
    };
  }
}

export async function getDiscoveryCategoryStats(): Promise<CategoryStats[]> {
  try {
    const rows = await query<CategoryStats>(`
      SELECT
        category,
        COUNT(*) as candidate_count,
        COALESCE(AVG(total_score) FILTER (WHERE total_score > 0), 0) as avg_score,
        COUNT(*) FILTER (WHERE status = 'promoted') as promoted_count,
        COUNT(*) FILTER (WHERE status = 'qualified') as qualified_count
      FROM investor_candidates
      GROUP BY category
      ORDER BY COUNT(*) DESC
    `);
    return rows.map(r => ({
      ...r,
      candidate_count: typeof r.candidate_count === 'string' ? parseInt(r.candidate_count) : r.candidate_count,
      avg_score: typeof r.avg_score === 'string' ? parseFloat(r.avg_score) : r.avg_score,
      promoted_count: typeof r.promoted_count === 'string' ? parseInt(r.promoted_count) : r.promoted_count,
      qualified_count: typeof r.qualified_count === 'string' ? parseInt(r.qualified_count) : r.qualified_count,
    }));
  } catch {
    return [];
  }
}

export async function getDiscoverySweeps(
  category?: DiscoveryCategory,
  status?: SweepStatus,
  limit = 50
): Promise<DiscoverySweep[]> {
  try {
    let sql = `SELECT * FROM discovery_sweeps WHERE 1=1`;
    const params: any[] = [];

    if (category) {
      params.push(category);
      sql += ` AND category = $${params.length}`;
    }

    if (status) {
      params.push(status);
      sql += ` AND status = $${params.length}`;
    }

    params.push(limit);
    sql += ` ORDER BY started_at DESC LIMIT $${params.length}`;

    const rows = await query<DiscoverySweep>(sql, params);
    return rows.map(r => ({
      ...r,
      results_count: typeof r.results_count === 'string' ? parseInt(r.results_count) : r.results_count,
      new_candidates: typeof r.new_candidates === 'string' ? parseInt(r.new_candidates) : r.new_candidates,
      duplicates_found: typeof r.duplicates_found === 'string' ? parseInt(r.duplicates_found) : r.duplicates_found,
    }));
  } catch {
    return [];
  }
}

export async function getDiscoverySweep(id: string): Promise<DiscoverySweep | null> {
  try {
    return queryOne<DiscoverySweep>(
      `SELECT * FROM discovery_sweeps WHERE id = $1`,
      [id]
    );
  } catch {
    return null;
  }
}

export async function getInvestorCandidates(filters?: {
  category?: DiscoveryCategory;
  status?: CandidateStatus;
  min_score?: number;
  sweep_id?: string;
  limit?: number;
}): Promise<InvestorCandidate[]> {
  try {
    let sql = `SELECT * FROM investor_candidates WHERE 1=1`;
    const params: any[] = [];

    if (filters?.category) {
      params.push(filters.category);
      sql += ` AND category = $${params.length}`;
    }

    if (filters?.status) {
      params.push(filters.status);
      sql += ` AND status = $${params.length}`;
    }

    if (filters?.min_score != null) {
      params.push(filters.min_score);
      sql += ` AND total_score >= $${params.length}`;
    }

    if (filters?.sweep_id) {
      params.push(filters.sweep_id);
      sql += ` AND sweep_id = $${params.length}`;
    }

    params.push(filters?.limit ?? 100);
    sql += ` ORDER BY total_score DESC, created_at DESC LIMIT $${params.length}`;

    const rows = await query<InvestorCandidate>(sql, params);
    return rows.map(r => ({
      ...r,
      total_score: typeof r.total_score === 'string' ? parseFloat(r.total_score) : r.total_score,
      thesis_alignment_score: typeof r.thesis_alignment_score === 'string' ? parseFloat(r.thesis_alignment_score) : r.thesis_alignment_score,
      check_size_score: typeof r.check_size_score === 'string' ? parseFloat(r.check_size_score) : r.check_size_score,
      stage_fit_score: typeof r.stage_fit_score === 'string' ? parseFloat(r.stage_fit_score) : r.stage_fit_score,
      portfolio_synergy_score: typeof r.portfolio_synergy_score === 'string' ? parseFloat(r.portfolio_synergy_score) : r.portfolio_synergy_score,
      activity_recency_score: typeof r.activity_recency_score === 'string' ? parseFloat(r.activity_recency_score) : r.activity_recency_score,
      accessibility_score: typeof r.accessibility_score === 'string' ? parseFloat(r.accessibility_score) : r.accessibility_score,
      geographic_score: typeof r.geographic_score === 'string' ? parseFloat(r.geographic_score) : r.geographic_score,
    }));
  } catch {
    return [];
  }
}

export async function getInvestorCandidate(id: string): Promise<InvestorCandidate | null> {
  try {
    const row = await queryOne<InvestorCandidate>(
      `SELECT * FROM investor_candidates WHERE id = $1`,
      [id]
    );
    if (!row) return null;
    return {
      ...row,
      total_score: typeof row.total_score === 'string' ? parseFloat(row.total_score) : row.total_score,
      thesis_alignment_score: typeof row.thesis_alignment_score === 'string' ? parseFloat(row.thesis_alignment_score) : row.thesis_alignment_score,
      check_size_score: typeof row.check_size_score === 'string' ? parseFloat(row.check_size_score) : row.check_size_score,
      stage_fit_score: typeof row.stage_fit_score === 'string' ? parseFloat(row.stage_fit_score) : row.stage_fit_score,
      portfolio_synergy_score: typeof row.portfolio_synergy_score === 'string' ? parseFloat(row.portfolio_synergy_score) : row.portfolio_synergy_score,
      activity_recency_score: typeof row.activity_recency_score === 'string' ? parseFloat(row.activity_recency_score) : row.activity_recency_score,
      accessibility_score: typeof row.accessibility_score === 'string' ? parseFloat(row.accessibility_score) : row.accessibility_score,
      geographic_score: typeof row.geographic_score === 'string' ? parseFloat(row.geographic_score) : row.geographic_score,
    };
  } catch {
    return null;
  }
}

export async function getCandidateEnrichmentLog(candidateId: string): Promise<EnrichmentLogEntry[]> {
  try {
    return query<EnrichmentLogEntry>(
      `SELECT * FROM enrichment_log WHERE candidate_id = $1 ORDER BY created_at DESC`,
      [candidateId]
    );
  } catch {
    return [];
  }
}

export async function updateCandidateStatus(
  id: string,
  status: CandidateStatus
): Promise<InvestorCandidate | null> {
  const extra = status === 'promoted' ? `, promoted_at = NOW()` : '';
  return queryOne<InvestorCandidate>(
    `UPDATE investor_candidates
     SET status = $2, updated_at = NOW()${extra}
     WHERE id = $1
     RETURNING *`,
    [id, status]
  );
}

export async function getSweepCandidates(sweepId: string): Promise<InvestorCandidate[]> {
  return getInvestorCandidates({ sweep_id: sweepId });
}

// ================== Procedural Registry Functions ==================

export async function getProcedures(category?: ProcedureCategory, activeOnly = true): Promise<Procedure[]> {
  let sql = `
    SELECT p.*,
      COUNT(DISTINCT pr.id) as rule_count,
      COUNT(DISTINCT pa.id) as assignment_count
    FROM procedures p
    LEFT JOIN procedure_rules pr ON pr.procedure_id = p.id
    LEFT JOIN procedure_assignments pa ON pa.procedure_id = p.id
    WHERE 1=1
  `;
  const params: any[] = [];

  if (activeOnly) {
    sql += ` AND p.active = true`;
  }

  if (category) {
    params.push(category);
    sql += ` AND p.category = $${params.length}`;
  }

  sql += ` GROUP BY p.id ORDER BY p.category, p.name`;

  const rows = await query<Procedure>(sql, params);
  return rows.map(r => ({
    ...r,
    rule_count: typeof r.rule_count === 'string' ? parseInt(r.rule_count) : r.rule_count,
    assignment_count: typeof r.assignment_count === 'string' ? parseInt(r.assignment_count) : r.assignment_count,
  }));
}

export async function getProcedureById(id: string): Promise<Procedure | null> {
  const procedure = await queryOne<Procedure>(
    `SELECT * FROM procedures WHERE id = $1`,
    [id]
  );

  if (procedure) {
    procedure.rules = await getProcedureRules(id);
    procedure.assignments = await getProcedureAssignments(id);
  }

  return procedure;
}

export async function createProcedure(data: CreateProcedure): Promise<Procedure | null> {
  return queryOne<Procedure>(
    `INSERT INTO procedures (name, description, category, enforcement_level)
     VALUES ($1, $2, $3, $4)
     RETURNING *`,
    [data.name, data.description || null, data.category, data.enforcement_level || 'advisory']
  );
}

export async function updateProcedure(id: string, updates: Partial<Procedure>): Promise<Procedure | null> {
  const fields: string[] = [];
  const params: any[] = [];

  const allowedFields = ['name', 'description', 'category', 'enforcement_level', 'active'];

  for (const [key, value] of Object.entries(updates)) {
    if (allowedFields.includes(key)) {
      params.push(value);
      fields.push(`${key} = $${params.length}`);
    }
  }

  if (fields.length === 0) return getProcedureById(id);

  fields.push(`updated_at = NOW()`);
  params.push(id);
  const sql = `UPDATE procedures SET ${fields.join(', ')} WHERE id = $${params.length} RETURNING *`;

  return queryOne<Procedure>(sql, params);
}

export async function deleteProcedure(id: string): Promise<boolean> {
  // Soft delete by setting active = false
  const result = await queryOne<Procedure>(
    `UPDATE procedures SET active = false, updated_at = NOW() WHERE id = $1 RETURNING id`,
    [id]
  );
  return result !== null;
}

export async function getProcedureRules(procedureId: string): Promise<ProcedureRule[]> {
  return query<ProcedureRule>(
    `SELECT * FROM procedure_rules WHERE procedure_id = $1 ORDER BY created_at`,
    [procedureId]
  );
}

export async function createProcedureRule(data: CreateProcedureRule): Promise<ProcedureRule | null> {
  return queryOne<ProcedureRule>(
    `INSERT INTO procedure_rules (procedure_id, rule_type, condition, message, severity)
     VALUES ($1, $2, $3, $4, $5)
     RETURNING *`,
    [data.procedure_id, data.rule_type, JSON.stringify(data.condition), data.message, data.severity || 'warning']
  );
}

export async function deleteProcedureRule(id: string): Promise<boolean> {
  const result = await queryOne<{ id: string }>(
    `DELETE FROM procedure_rules WHERE id = $1 RETURNING id`,
    [id]
  );
  return result !== null;
}

export async function getProcedureAssignments(procedureId: string): Promise<ProcedureAssignment[]> {
  return query<ProcedureAssignment>(
    `SELECT * FROM procedure_assignments WHERE procedure_id = $1 ORDER BY priority, created_at`,
    [procedureId]
  );
}

export async function createProcedureAssignment(data: CreateProcedureAssignment): Promise<ProcedureAssignment | null> {
  return queryOne<ProcedureAssignment>(
    `INSERT INTO procedure_assignments (procedure_id, target_type, target_id, priority)
     VALUES ($1, $2, $3, $4)
     ON CONFLICT (procedure_id, target_type, target_id)
     DO UPDATE SET priority = EXCLUDED.priority
     RETURNING *`,
    [data.procedure_id, data.target_type, data.target_id || null, data.priority ?? 100]
  );
}

export async function deleteAssignment(id: string): Promise<boolean> {
  const result = await queryOne<{ id: string }>(
    `DELETE FROM procedure_assignments WHERE id = $1 RETURNING id`,
    [id]
  );
  return result !== null;
}

export async function getApplicableProcedures(
  targetType: string,
  targetId: string
): Promise<Array<Procedure & { rules: ProcedureRule[] }>> {
  // Get procedures assigned to this specific target or globally
  const procedures = await query<Procedure & { priority: number }>(
    `SELECT DISTINCT p.*, pa.priority
     FROM procedures p
     JOIN procedure_assignments pa ON pa.procedure_id = p.id
     WHERE p.active = true
       AND (
         (pa.target_type = $1 AND pa.target_id = $2)
         OR (pa.target_type = 'global' AND pa.target_id IS NULL)
         OR (pa.target_type = $1 AND pa.target_id IS NULL)
       )
     ORDER BY pa.priority ASC, p.name`,
    [targetType, targetId]
  );

  // Load rules for each procedure
  const result: Array<Procedure & { rules: ProcedureRule[] }> = [];
  for (const proc of procedures) {
    const rules = await getProcedureRules(proc.id);
    result.push({ ...proc, rules });
  }

  return result;
}

export async function logViolation(data: CreateViolation): Promise<ProcedureViolation | null> {
  return queryOne<ProcedureViolation>(
    `INSERT INTO procedure_violations
     (procedure_id, rule_id, actor_type, actor_id, action, context, enforcement_result)
     VALUES ($1, $2, $3, $4, $5, $6, $7)
     RETURNING *`,
    [
      data.procedure_id,
      data.rule_id,
      data.actor_type,
      data.actor_id,
      data.action,
      data.context ? JSON.stringify(data.context) : null,
      data.enforcement_result,
    ]
  );
}

export async function logExecution(data: CreateExecution): Promise<ProcedureExecution | null> {
  return queryOne<ProcedureExecution>(
    `INSERT INTO procedure_executions
     (procedure_id, actor_type, actor_id, action, passed, rules_evaluated, rules_failed, execution_ms)
     VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
     RETURNING *`,
    [
      data.procedure_id,
      data.actor_type,
      data.actor_id,
      data.action,
      data.passed,
      data.rules_evaluated,
      data.rules_failed,
      data.execution_ms,
    ]
  );
}

export async function getViolations(filters: ViolationFilters): Promise<ProcedureViolation[]> {
  let sql = `
    SELECT v.*, p.name as procedure_name, r.message as rule_message
    FROM procedure_violations v
    LEFT JOIN procedures p ON v.procedure_id = p.id
    LEFT JOIN procedure_rules r ON v.rule_id = r.id
    WHERE 1=1
  `;
  const params: any[] = [];

  if (filters.procedure_id) {
    params.push(filters.procedure_id);
    sql += ` AND v.procedure_id = $${params.length}`;
  }

  if (filters.actor_type) {
    params.push(filters.actor_type);
    sql += ` AND v.actor_type = $${params.length}`;
  }

  if (filters.actor_id) {
    params.push(filters.actor_id);
    sql += ` AND v.actor_id = $${params.length}`;
  }

  if (filters.enforcement_result) {
    params.push(filters.enforcement_result);
    sql += ` AND v.enforcement_result = $${params.length}`;
  }

  if (filters.start_date) {
    params.push(filters.start_date);
    sql += ` AND v.created_at >= $${params.length}`;
  }

  if (filters.end_date) {
    params.push(filters.end_date);
    sql += ` AND v.created_at <= $${params.length}`;
  }

  sql += ` ORDER BY v.created_at DESC`;

  if (filters.limit) {
    params.push(filters.limit);
    sql += ` LIMIT $${params.length}`;
  }

  if (filters.offset) {
    params.push(filters.offset);
    sql += ` OFFSET $${params.length}`;
  }

  return query<ProcedureViolation>(sql, params);
}

export async function getViolationStats(startDate: Date, endDate: Date): Promise<ViolationStats> {
  const [totals, byProcedure, byActor] = await Promise.all([
    query<{
      total: string;
      logged: string;
      warned: string;
      blocked: string;
    }>(`
      SELECT
        COUNT(*) as total,
        COUNT(*) FILTER (WHERE enforcement_result = 'logged') as logged,
        COUNT(*) FILTER (WHERE enforcement_result = 'warned') as warned,
        COUNT(*) FILTER (WHERE enforcement_result = 'blocked') as blocked
      FROM procedure_violations
      WHERE created_at >= $1 AND created_at <= $2
    `, [startDate.toISOString(), endDate.toISOString()]),

    query<{ procedure_id: string; procedure_name: string; count: string }>(`
      SELECT v.procedure_id, p.name as procedure_name, COUNT(*) as count
      FROM procedure_violations v
      JOIN procedures p ON v.procedure_id = p.id
      WHERE v.created_at >= $1 AND v.created_at <= $2
      GROUP BY v.procedure_id, p.name
      ORDER BY count DESC
      LIMIT 10
    `, [startDate.toISOString(), endDate.toISOString()]),

    query<{ actor_type: string; actor_id: string; count: string }>(`
      SELECT actor_type, actor_id, COUNT(*) as count
      FROM procedure_violations
      WHERE created_at >= $1 AND created_at <= $2
      GROUP BY actor_type, actor_id
      ORDER BY count DESC
      LIMIT 10
    `, [startDate.toISOString(), endDate.toISOString()]),
  ]);

  return {
    total_violations: parseInt(totals[0]?.total || '0'),
    logged_count: parseInt(totals[0]?.logged || '0'),
    warned_count: parseInt(totals[0]?.warned || '0'),
    blocked_count: parseInt(totals[0]?.blocked || '0'),
    by_procedure: byProcedure.map(r => ({
      procedure_id: r.procedure_id,
      procedure_name: r.procedure_name,
      count: parseInt(r.count),
    })),
    by_actor: byActor.map(r => ({
      actor_type: r.actor_type,
      actor_id: r.actor_id,
      count: parseInt(r.count),
    })),
  };
}

export async function getProcedureStats(): Promise<ProcedureStats> {
  const [totals, byCategory, byEnforcement, violations24h, executions24h] = await Promise.all([
    query<{ total: string; active: string }>(`
      SELECT COUNT(*) as total, COUNT(*) FILTER (WHERE active = true) as active
      FROM procedures
    `),

    query<{ category: ProcedureCategory; count: string }>(`
      SELECT category, COUNT(*) as count
      FROM procedures WHERE active = true
      GROUP BY category
      ORDER BY count DESC
    `),

    query<{ enforcement_level: EnforcementLevel; count: string }>(`
      SELECT enforcement_level, COUNT(*) as count
      FROM procedures WHERE active = true
      GROUP BY enforcement_level
      ORDER BY count DESC
    `),

    query<{ total: string; blocked: string }>(`
      SELECT COUNT(*) as total, COUNT(*) FILTER (WHERE enforcement_result = 'blocked') as blocked
      FROM procedure_violations
      WHERE created_at >= NOW() - INTERVAL '24 hours'
    `),

    query<{ count: string }>(`
      SELECT COUNT(*) as count
      FROM procedure_executions
      WHERE created_at >= NOW() - INTERVAL '24 hours'
    `),
  ]);

  return {
    total_procedures: parseInt(totals[0]?.total || '0'),
    active_procedures: parseInt(totals[0]?.active || '0'),
    violations_24h: parseInt(violations24h[0]?.total || '0'),
    blocked_24h: parseInt(violations24h[0]?.blocked || '0'),
    executions_24h: parseInt(executions24h[0]?.count || '0'),
    by_category: byCategory.map(r => ({
      category: r.category,
      count: parseInt(r.count),
    })),
    by_enforcement: byEnforcement.map(r => ({
      enforcement_level: r.enforcement_level,
      count: parseInt(r.count),
    })),
  };
}
