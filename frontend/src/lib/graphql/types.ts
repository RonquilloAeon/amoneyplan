export interface Account {
  id: string;
  name: string;
  balance: number;
  accountType: 'CHECKING' | 'SAVINGS' | 'CREDIT' | 'INVESTMENT';
  currency: string;
}

export interface Bucket {
  id: string;
  name: string;
  allocatedAmount: number;
  category: string;
}

export interface PlanAccount {
  id: string;
  account: Account;
  buckets: Bucket[];
  isChecked: boolean;
  notes?: string;
}

export interface Plan {
  id: string;
  name: string;
  description: string;
  planDate: string;
  createdAt: string;
  updatedAt: string;
  initialBalance: number;
  remainingBalance: number;
  isCommitted: boolean;
  isArchived: boolean;
  notes?: string;
  planAccounts: PlanAccount[];
}

export interface CreateAccountInput {
  name: string;
  balance: number;
  accountType: Account['accountType'];
  currency: string;
}

export interface UpdateAccountInput {
  name?: string;
  balance?: number;
  accountType?: Account['accountType'];
  currency?: string;
}

export interface CreateBucketInput {
  name: string;
  allocatedAmount: number;
  category: string;
}

export interface UpdateBucketInput {
  name?: string;
  allocatedAmount?: number;
  category?: string;
}

export interface CreatePlanInput {
  name: string;
  description: string;
  planDate: string;
  initialBalance: number;
  notes?: string;
  copyFrom?: string; // ID of plan to copy from
}

export interface UpdatePlanInput {
  name?: string;
  description?: string;
  planDate?: string;
  notes?: string;
  isArchived?: boolean;
}

export interface GetAccountsQuery {
  accounts: Account[];
}

export interface GetPlansQuery {
  plans: Plan[];
}

export interface GetDraftPlanQuery {
  draftPlan: Plan | null;
}

export interface CreatePlanMutation {
  createPlan: Plan;
}

export interface UpdatePlanMutation {
  updatePlan: Plan;
}

export interface DeletePlanMutation {
  deletePlan: boolean;
}

export interface CommitPlanMutation {
  commitPlan: Plan;
}

export interface ArchivePlanMutation {
  archivePlan: Plan;
}

export interface AddAccountToPlanMutation {
  addAccountToPlan: Plan;
}

export interface UpdatePlanAccountMutation {
  updatePlanAccount: Plan;
}

export interface RemoveAccountFromPlanMutation {
  removeAccountFromPlan: Plan;
}

export interface UpdatePlanAccountNotesMutation {
  updatePlanAccountNotes: Plan;
}

export interface UpdatePlanNotesMutation {
  updatePlanNotes: Plan;
} 