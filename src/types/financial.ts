export interface Opportunity {
  id: string;
  title: string;
  category: string;
  payout: string;
  matchScore: number; // 0-100
  status: 'new' | 'applied' | 'in-progress';
}

export interface Benefit {
  id: string;
  name: string;
  type: string;
  value: string;
  eligibility: string;
  status: 'not-started' | 'in-progress' | 'submitted' | 'approved';
}

export interface PersonalFinanceSnapshot {
  netCashFlow: number;
  monthlyIncome: number;
  monthlyExpenses: number;
  bufferMonths: number;
  alerts: string[];
}

export interface FocusGroup {
  id: string;
  title: string;
  theme: string;
  scheduledFor: string;
  capacity: number;
  enrolled: number;
}

export interface FinancialModuleResponse {
  opportunities: Opportunity[];
  benefits: Benefit[];
  personalFinance: PersonalFinanceSnapshot;
  focusGroups: FocusGroup[];
}

