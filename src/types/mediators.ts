export interface MediatorModule {
  id: string;
  title: string;
  summary: string;
  durationMinutes: number;
  status: 'not-started' | 'in-progress' | 'completed';
}

export interface MediatorSession {
  id: string;
  topic: string;
  facilitator: string;
  scheduledFor: string;
  attendees: number;
  status: 'scheduled' | 'completed';
}

export interface MediatorRosterEntry {
  id: string;
  name: string;
  role: 'peer-mediator' | 'admin';
  cohort: string;
  progress: number; // percentage
}

export interface MediatorCurriculumResponse {
  modules: MediatorModule[];
  sessions: MediatorSession[];
}

export interface MediatorAdminResponse {
  roster: MediatorRosterEntry[];
  sessions: MediatorSession[];
}

