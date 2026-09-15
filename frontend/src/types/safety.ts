export type UserRole = 'Safety Officer' | 'Management' | 'Administrator';

export interface HealthStatus {
  status: string;
  service: string;
  version: string;
  database: string;
  total_datasets: number;
  total_reports: number;
}

export interface DatasetColumn {
  id: string;
  dataset_id: string;
  column_index: number;
  original_name: string;
  sanitized_name: string;
  detected_data_type: string;
  semantic_type: string;
  is_nullable: boolean;
  null_count: number;
  unique_count: number;
  is_constant: boolean;
  constant_value: string | null;
  sample_values: any[] | null;
  mapped_canonical_field: string | null;
}

export interface DatasetItem {
  id: string;
  dataset_name: string;
  original_filename: string;
  sheet_name?: string | null;
  file_type: string;
  dataset_type?: string;
  factor_count?: number;
  factor_names?: string[];
  file_size_bytes: number;
  upload_timestamp: string;
  row_count: number;
  column_count: number;
  status: string;
  data_quality_status?: string;
  duplicate_count?: number;
  is_derived_dataset?: boolean;
  is_summary_dataset?: boolean;
  parent_dataset?: string | null;
  description: string | null;
  is_active: boolean;
  created_at: string;
  columns?: DatasetColumn[];
}

export interface DatasetSchemaInfo {
  dataset_id: string;
  dataset_name: string;
  row_count: number;
  column_count: number;
  columns: DatasetColumn[];
  constant_fields: DatasetColumn[];
  mapped_fields_count: number;
  unmapped_fields_count: number;
}

export interface DataQualitySummary {
  id: string;
  dataset_id: string;
  dataset_name?: string;
  calculated_at: string;
  total_rows: number;
  total_columns: number;
  valid_records_count: number;
  missing_values_count: number;
  duplicate_ids_count: number;
  invalid_dates_count: number;
  constant_fields_count: number;
  empty_columns_count: number;
  data_quality_score: number;
  date_range_start: string | null;
  date_range_end: string | null;
  column_metrics: Record<string, any>;
  constant_fields: string[];
  summary_notes: string[];
}

export interface SafetyReport {
  id: string;
  dataset_id: string;
  original_id: string | null;
  report_date: string | null;
  location: string | null;
  refinery_unit: string | null;
  equipment: string | null;
  work_type: string | null;
  department: string | null;
  report_type: string | null;
  description: string | null;
  hazard: string | null;
  unsafe_act: string | null;
  unsafe_condition: string | null;
  ppe_issue: boolean | null;
  immediate_cause: string | null;
  potential_consequence: string | null;
  risk_level: string | null;
  sif_precursor: boolean | null;
  high_potential: boolean | null;
  previous_similar_reports: number | null;
  repeated_issue: boolean | null;
  supervisor_factor: boolean | null;
  maintenance_factor: boolean | null;
  corrective_action: string | null;
  action_status: string | null;
  assigned_to?: string | null;
  assigned_department?: string | null;
  due_date?: string | null;
  completion_date?: string | null;
  closure_verified_by?: string | null;
  closure_verified_at?: string | null;
  action_comments?: string | null;
  source_dataset: string | null;
  analysis_status?: string | null;
  submitting_user?: string | null;
  submitting_role?: string | null;
  created_at: string;
  raw_data?: Record<string, any>;
}

export interface SafetyReportCreate {
  description: string;
  report_type?: string;
  report_date?: string;
  location?: string;
  refinery_unit?: string;
  equipment?: string;
  work_type?: string;
  department?: string;
  hazard?: string;
  unsafe_act?: string;
  unsafe_condition?: string;
  ppe_issue?: boolean;
  supervisor_factor?: boolean;
  maintenance_factor?: boolean;
  repeated_issue?: boolean;
  immediate_cause?: string;
  potential_consequence?: string;
  risk_level?: string;
  corrective_action?: string;
  assigned_to?: string;
  assigned_department?: string;
  due_date?: string;
  dataset_id?: string;
  submitting_user?: string;
  submitting_role?: string;
}

export interface EscalationScenario {
  current_condition: string;
  continued_exposure: string;
  loss_of_control: string;
  incident_event: string;
  serious_consequence: string;
  potential_fatal_consequence: string;
}

export interface ReportAnalysis {
  id: string;
  report_id: string;
  dataset_id: string;
  analysis_timestamp: string;
  model_version: string;
  observed_problem: string;
  extracted_ppe_items: string[];
  extracted_ppe_issue_type: string;
  hazard_identified: string;
  exposure_target: string;
  immediate_cause: string | null;
  potential_consequence: string | null;
  recorded_risk_level: string;
  ai_risk_level: string;
  sif_precursor: 'YES' | 'NO' | 'UNCERTAIN';
  sif_category: string;
  confidence_score: number;
  reasoning: string[];
  iogp_rule?: string | null;
  secondary_iogp_rules?: string[];
  iogp_confidence?: number | null;
  iogp_reasoning?: string | null;
  barrier_failure?: string | null;
  missing_control?: string | null;
  existing_barrier?: string | null;
  is_recurring: boolean;
  recurrence_score: number;
  recurrence_details: Record<string, any>;
  immediate_action_recommendation: string;
  preventive_action_recommendation: string;
  escalation_scenario: EscalationScenario;
  organizational_factors: string[];
  human_overridden?: boolean;
  human_risk_level?: string | null;
  human_sif_precursor?: string | null;
  human_feedback_reason?: string | null;
  report?: SafetyReport | null;
}

export interface ReportCounts {
  total_reports: number;
  by_risk_level: Record<string, number>;
  by_department: Record<string, number>;
  by_refinery_unit: Record<string, number>;
  by_action_status: Record<string, number>;
  by_work_type: Record<string, number>;
}

export interface SIFSummary {
  total_analyzed: number;
  sif_precursors_detected: number;
  sif_precursor_rate_percentage: number;
  by_sif_precursor: Record<string, number>;
  by_ai_risk_level: Record<string, number>;
  by_recorded_risk_level: Record<string, number>;
  risk_level_upgrades: number;
  by_sif_category: Record<string, number>;
  by_ppe_issue_type: Record<string, number>;
  top_recurring_units: { name: string; reports_count: number }[];
  top_recurring_equipment: { name: string; reports_count: number }[];
}

export interface RecurringIssueItem {
  category: string;
  identifier: string;
  count: number;
  sif_precursor_count: number;
  high_risk_count: number;
  sample_descriptions: string[];
  sample_report_ids: string[];
}

export interface RecurringIssuesResponse {
  total_recurring_clusters: number;
  by_equipment: RecurringIssueItem[];
  by_refinery_unit: RecurringIssueItem[];
  by_department: RecurringIssueItem[];
  by_work_type: RecurringIssueItem[];
}

export interface AIFeedback {
  id: string;
  report_id: string;
  analysis_id: string;
  reviewer_name: string;
  agrees_with_ai: boolean;
  human_risk_level?: string;
  human_sif_precursor?: string;
  feedback_reason: string;
  submitted_at: string;
}

export interface MetadataFieldOption {
  field_name: string;
  display_name: string;
  data_type: string;
  distinct_values: any[];
  is_constant: boolean;
}

export interface MetadataFieldsResponse {
  available_filters: MetadataFieldOption[];
  canonical_schema: { name: string; description: string; data_type: string; is_required: boolean }[];
  total_active_datasets: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

// --- PART 4: ACTIONS & HISTORY ---
export interface ActionItem {
  report_id: string;
  original_id: string | null;
  problem: string | null;
  risk_level: string | null;
  corrective_action: string | null;
  refinery_unit: string | null;
  department: string | null;
  assigned_to: string | null;
  assigned_department: string | null;
  action_status: string;
  due_date: string | null;
  completion_date: string | null;
  closure_verified_by: string | null;
  closure_verified_at: string | null;
  action_comments: string | null;
  is_overdue: boolean;
  days_overdue?: number | null;
  history_count: number;
}

export interface ActionHistoryItem {
  id: string;
  report_id: string;
  actor_name: string;
  actor_role: string;
  action_type: string;
  old_status: string | null;
  new_status: string | null;
  comments: string | null;
  timestamp: string;
}

export interface ActionStats {
  total_actions: number;
  open_count: number;
  in_progress_count: number;
  closed_count: number;
  overdue_count: number;
  unassigned_count: number;
}

// --- PART 4: NOTIFICATIONS & ESCALATION ---
export interface NotificationConfigItem {
  id: string;
  tier: 'SAFETY_HSE' | 'DEPT_HEAD' | 'MANAGEMENT';
  role_name: string;
  department: string | null;
  email_address: string;
  notify_on_high_risk: boolean;
  notify_on_overdue: boolean;
  notify_on_assignment: boolean;
  is_active: boolean;
  created_at: string;
}

export interface EmailRecipientPreview {
  tier: string;
  role_name: string;
  email_address: string;
  department: string | null;
}

export interface EmailRecordedInfo {
  report_id: string;
  original_id: string | null;
  observed_problem: string;
  recorded_risk_level: string;
  refinery_unit: string | null;
  department: string | null;
  work_type: string | null;
  equipment: string | null;
  immediate_cause: string | null;
  potential_consequence: string | null;
  corrective_action: string | null;
  action_status: string | null;
  assigned_to: string | null;
  assigned_department: string | null;
  due_date: string | null;
  report_date: string | null;
}

export interface EmailAIRecommendations {
  ai_risk_level: string;
  sif_precursor: string;
  sif_category: string | null;
  confidence_score: number;
  immediate_action_recommendation: string;
  preventive_action_recommendation: string;
  escalation_consequence: string | null;
  reasoning: string[];
}

export interface EmailPreviewData {
  notification_type: string;
  subject: string;
  recipients: EmailRecipientPreview[];
  recorded_information: EmailRecordedInfo;
  ai_recommendations: EmailAIRecommendations;
  rendered_html: string;
  rendered_plain_text: string;
}

export interface EmailLogItem {
  id: string;
  report_id: string | null;
  recipient_email: string;
  recipient_name: string | null;
  recipient_role: string | null;
  escalation_tier: string | null;
  subject: string;
  body_html: string;
  status: string;
  triggered_by: string | null;
  sent_at: string;
}

export interface ExportFilterParams {
  dataset_id?: string;
  risk_level?: string;
  department?: string;
  refinery_unit?: string;
  report_type?: string;
  action_status?: string;
  date_from?: string;
  date_to?: string;
}

export interface ExportPreviewData {
  total_matching_reports: number;
  by_risk_level: Record<string, number>;
  by_department: Record<string, number>;
  by_refinery_unit: Record<string, number>;
  by_action_status: Record<string, number>;
  sif_precursor_count: number;
  overdue_count: number;
  available_export_formats: string[];
  active_filters_applied: Record<string, any>;
}

export type FactorSummary = FactorSummaryData;
export type HighPotentialIntelligence = HighPotentialIntelligenceData;

export interface FactorMetric {
  factor_name: string;
  display_name: string;
  total_count: number;
  percentage: number;
  high_risk_count: number;
  critical_count: number;
  high_potential_count: number;
  recurring_count: number;
  top_consequence?: string | null;
  top_refinery_unit?: string | null;
}

export interface FactorSummaryData {
  total_reports_analyzed: number;
  active_dataset_count: number;
  single_factor_reports_count: number;
  multi_factor_reports_count: number;
  high_potential_reports_count: number;
  factors: FactorMetric[];
}

export interface FactorCombinationItem {
  combination_key: string;
  factor_names: string[];
  factor_count: number;
  report_count: number;
  high_risk_count: number;
  critical_count: number;
  high_potential_count: number;
  high_risk_ratio: number;
  danger_score: number;
  danger_level: string;
  top_consequences: string[];
  top_causes: string[];
  sample_report_ids: string[];
}

export interface FactorCombinationsData {
  total_reports_analyzed: number;
  level_1_count: number;
  level_2_count: number;
  level_3_count: number;
  level_4_count: number;
  combinations: FactorCombinationItem[];
  danger_ranked_combinations: FactorCombinationItem[];
}

export interface DatasetComparisonData {
  dataset_a: {
    id: string;
    name: string;
    type: string;
    factor_count: number;
    factors: string[];
  };
  dataset_b: {
    id: string;
    name: string;
    type: string;
    factor_count: number;
    factors: string[];
  };
  total_reports_a: number;
  total_reports_b: number;
  risk_distribution_comparison: Array<{
    risk_level: string;
    count_a: number;
    percentage_a: number;
    count_b: number;
    percentage_b: number;
    delta_percentage: number;
  }>;
  factor_presence_comparison: Array<{
    factor_name: string;
    count_a: number;
    percentage_a: number;
    count_b: number;
    percentage_b: number;
    delta_percentage: number;
  }>;
  top_consequences_a: Array<{ consequence: string; count: number }>;
  top_consequences_b: Array<{ consequence: string; count: number }>;
  top_causes_a: Array<{ cause: string; count: number }>;
  top_causes_b: Array<{ cause: string; count: number }>;
  high_potential_count_a: number;
  high_potential_count_b: number;
  open_actions_count_a: number;
  open_actions_count_b: number;
  comparative_insights: string[];
}

export interface HighPotentialPatternItem {
  pattern_name: string;
  incident_count: number;
  factor_combination: string[];
  immediate_causes: string[];
  potential_consequences: string[];
  affected_units: string[];
  severity_rating: string;
}

export interface HighPotentialIntelligenceData {
  total_high_potential_incidents: number;
  critical_risk_count: number;
  high_risk_count: number;
  multi_barrier_failure_count: number;
  repeated_issue_co_occurrence_count: number;
  top_potential_consequences: Array<{ consequence: string; count: number }>;
  top_immediate_causes: Array<{ cause: string; count: number }>;
  top_refinery_units: Array<{ unit: string; count: number }>;
  key_failure_patterns: HighPotentialPatternItem[];
  preventive_imperatives: string[];
}

// -------------------------------------------------------------
// PHASE 1-6 BARRIER, BDI, SIF ESCALATION, ACTIONS & SLA TYPES
// -------------------------------------------------------------

export interface BarrierAssessmentItem {
  barrier_type: string;
  barrier_name: string;
  status: 'INTACT' | 'DEGRADED' | 'FAILED' | 'UNKNOWN';
  confidence: number;
  evidence_phrases: string[];
  reasoning: string;
}

export interface SwissCheeseLayer {
  layer_index: number;
  barrier_name: string;
  barrier_type: string;
  status: 'INTACT' | 'DEGRADED' | 'FAILED' | 'UNKNOWN';
  hole_size: number;
  description: string;
}

export interface ReportBarrierResponse {
  report_id: string;
  total_barriers: number;
  failed_barriers_count: number;
  degraded_barriers_count: number;
  intact_barriers_count: number;
  barriers: BarrierAssessmentItem[];
  layers: SwissCheeseLayer[];
  multi_barrier_convergence: boolean;
  reasoning: string[];
}

export interface BarrierSummaryResponse {
  total_assessments: number;
  failed_distribution: Record<string, number>;
  degraded_distribution: Record<string, number>;
  critical_convergences_count: number;
  dominant_degraded_barriers: Array<{ barrier_name: string; count: number }>;
}

export interface BDIResponse {
  report_id: string;
  bdi_score: number;
  classification: 'MINIMAL' | 'LOW' | 'MODERATE' | 'SIGNIFICANT' | 'SEVERE';
  barrier_states_summary: Record<string, string>;
  component_contributions: Record<string, number>;
  dominant_degraded_barriers: string[];
  dominant_safety_factors: string[];
  independent_metrics: {
    recorded_risk: string;
    ai_risk: string;
    sif_status: string;
    hipo: boolean;
  };
}

export interface BDISummaryResponse {
  average_bdi: number;
  severe_bdi_count: number;
  significant_bdi_count: number;
  moderate_bdi_count: number;
  low_bdi_count: number;
  minimal_bdi_count: number;
  top_vulnerable_units: Array<{ unit: string; average_bdi: number; report_count: number }>;
  dominant_degraded_barriers: Array<{ barrier_name: string; count: number }>;
  dominant_safety_factors: Array<{ factor_name: string; count: number }>;
}

export interface BDITrendPoint {
  period: string;
  average_bdi: number;
  report_count: number;
  high_bdi_count: number;
}

export interface EscalationStageItem {
  stage_number: number;
  stage_name: string;
  description: string;
  is_active: boolean;
}

export interface PreventiveIntelligencePayload {
  current_condition: string;
  hazard_exposure: string;
  control_failure: string;
  immediate_containment: string;
  preventive_action: string;
  potential_escalation: string;
}

export interface ReportSIFEscalationResponse {
  report_id: string;
  severity: 'NORMAL' | 'WATCH' | 'ELEVATED' | 'HIGH' | 'CRITICAL';
  sif_precursor_status: boolean;
  sif_category: string;
  bdi_score: number;
  bdi_classification: string;
  barrier_summary: {
    intact: number;
    degraded: number;
    failed: number;
    unknown: number;
  };
  contributing_factors: string[];
  escalation_scenario: EscalationStageItem[];
  preventive_intelligence?: PreventiveIntelligencePayload | null;
  why_escalated: string;
  what_could_happen: string;
  which_barriers: string[];
  which_factors: string[];
  which_reports: string[];
  what_exposure: string;
  what_potential_consequence: string;
  what_remains_unresolved: string;
  recommended_immediate_action: string;
  recommended_preventive_action: string;
  confidence: number;
}

export interface SIFEscalationSummaryResponse {
  total_assessed: number;
  critical_count: number;
  high_count: number;
  elevated_count: number;
  watch_count: number;
  normal_count: number;
  sif_precursor_rate: number;
  top_vulnerable_units: Array<{ unit: string; critical_count: number; high_count: number }>;
}

export interface SafetyActionResponse {
  id: string;
  report_id: string;
  dataset_id?: string | null;
  action_type: string;
  severity: string;
  title: string;
  description: string;
  ai_recommendation: Record<string, any>;
  action_package: Record<string, any>;
  assigned_role: string;
  assigned_user?: string | null;
  sla_hours: number;
  sla_minutes?: number | null;
  sla_deadline?: string | null;
  sla_state?: string;
  escalation_level: number;
  status: string;
  approval_status: string;
  approved_by?: string | null;
  approved_at?: string | null;
  rejection_reason?: string | null;
  acknowledged_at?: string | null;
  containment_started_at?: string | null;
  remediation_completed_at?: string | null;
  completed_at?: string | null;
  verified_at?: string | null;
  verified_by?: string | null;
  closed_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface SafetyHoldResponse {
  id: string;
  report_id?: string | null;
  action_id?: string | null;
  permit_id?: string | null;
  jsa_id?: string | null;
  refinery_unit?: string | null;
  equipment?: string | null;
  trigger: string;
  reason: string;
  bdi?: number | null;
  sif_status?: string | null;
  status: string;
  requested_by: string;
  reviewed_by?: string | null;
  approved_by?: string | null;
  released_by?: string | null;
  verified_by?: string | null;
  verification_notes?: string | null;
  created_at: string;
  approved_at?: string | null;
  released_at?: string | null;
  updated_at: string;
}

export interface SLAPolicyResponse {
  id: string;
  severity: string;
  sla_minutes: number;
  reminder_minutes: number;
  warning_minutes: number;
  escalation_interval_minutes: number;
  escalation_level_0_role: string;
  escalation_level_1_role: string;
  escalation_level_2_role: string;
  escalation_level_3_role: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface SLACountdownResponse {
  action_id: string;
  report_id: string;
  severity: string;
  action_type: string;
  assigned_role: string;
  assigned_user?: string | null;
  sla_minutes: number;
  sla_deadline?: string | null;
  time_remaining_seconds: number;
  formatted_countdown: string;
  percentage_elapsed: number;
  sla_state: string;
  current_escalation_level: number;
  is_acknowledged: boolean;
  is_breached: boolean;
}

export interface SLAActionItemResponse {
  action_id: string;
  report_id: string;
  severity: string;
  title: string;
  status: string;
  sla_state: string;
  assigned_role: string;
  assigned_user?: string | null;
  sla_deadline?: string | null;
  time_remaining_seconds: number;
  formatted_countdown: string;
  escalation_level: number;
  created_at: string;
  acknowledged_at?: string | null;
}

export interface SLADashboardResponse {
  critical_open: number;
  awaiting_acknowledgement: number;
  approaching_sla: number;
  sla_breached: number;
  escalated: number;
  contained: number;
  awaiting_verification: number;
  closed: number;
  total_active_actions: number;
  active_actions: SLAActionItemResponse[];
}

// -------------------------------------------------------------
// PHASE 8 AUDIT TRAIL, HUMAN FEEDBACK, ADMIN SETTINGS & DEMO TYPES
// -------------------------------------------------------------

export interface SystemAuditLogItem {
  event_id: string;
  timestamp: string;
  report_id?: string | null;
  dataset_id?: string | null;
  action_id?: string | null;
  hold_id?: string | null;
  event_type: string;
  engine_version: string;
  trigger: string;
  evidence?: Record<string, any> | null;
  bdi?: number | null;
  sif_status?: string | null;
  severity?: string | null;
  recommended_action?: string | null;
  human_decision?: string | null;
  notification_status?: string | null;
  escalation_level?: number | null;
  final_resolution?: string | null;
  actor: string;
  is_simulated: boolean;
  client_host?: string | null;
}

export interface AuditTimelineEvent {
  event_id: string;
  timestamp: string;
  formatted_time: string;
  event_type: string;
  title: string;
  description: string;
  actor: string;
  severity?: string | null;
  bdi?: number | null;
  sif_status?: string | null;
  is_simulated: boolean;
  evidence?: Record<string, any> | null;
}

export interface AuditTimelineResponse {
  report_id?: string | null;
  total_events: number;
  events: AuditTimelineEvent[];
  first_event_at?: string | null;
  last_event_at?: string | null;
}

export interface AuditStatsResponse {
  total_events: number;
  real_events: number;
  simulated_events: number;
  event_types_breakdown: Record<string, number>;
  actors_breakdown: Record<string, number>;
  last_event_timestamp?: string | null;
}

export interface HumanFeedbackItem {
  id: string;
  report_id: string;
  analysis_id?: string | null;
  action_id?: string | null;
  reviewer_name: string;
  reviewer_role: string;
  rating: 'CORRECT' | 'INCORRECT' | 'PARTIALLY_CORRECT' | 'NOT_USEFUL';
  feedback_category: string;
  human_risk_level?: string | null;
  human_sif_status?: string | null;
  comments?: string | null;
  is_simulated: boolean;
  submitted_at: string;
}

export interface HumanFeedbackCreate {
  report_id: string;
  analysis_id?: string | null;
  action_id?: string | null;
  reviewer_name?: string;
  reviewer_role?: string;
  rating: string;
  feedback_category?: string;
  human_risk_level?: string | null;
  human_sif_status?: string | null;
  comments?: string | null;
  is_simulated?: boolean;
}

export interface FeedbackStatsResponse {
  total_feedback_count: number;
  agreement_rate_percentage: number;
  ratings_breakdown: Record<string, number>;
  categories_breakdown: Record<string, number>;
  recent_feedbacks: HumanFeedbackItem[];
}

export interface AdminSettingsResponse {
  demo_mode_active: boolean;
  ai_engine_version: string;
  human_approval_required: boolean;
  bdi_thresholds: {
    normal_max: number;
    low_max: number;
    moderate_max: number;
    high_max: number;
    critical_max: number;
  };
  bdi_methodology: {
    methodology: string;
    include_historical_penalty: boolean;
    near_miss_multiplier: number;
  };
  sif_thresholds: {
    high_bdi_cutoff: number;
    critical_bdi_cutoff: number;
    min_failed_barriers_for_critical: number;
    require_toxic_or_flammable_exposure: boolean;
  };
  sla_policies: Array<{
    severity: string;
    target_sla_minutes: number;
    reminder_interval_minutes: number;
    warning_interval_minutes: number;
    level_0_role: string;
    level_1_role: string;
    level_2_role: string;
    level_3_role: string;
  }>;
  notification_channels: {
    mock_mode: boolean;
    email_enabled: boolean;
    webhook_enabled: boolean;
    sms_enabled: boolean;
    smtp_host: string;
    smtp_port: number;
    smtp_user: string;
    smtp_password_masked: string;
    webhook_url_masked: string;
  };
  last_updated_at?: string | null;
  last_updated_by: string;
}

export interface AdminSettingsUpdate {
  demo_mode_active?: boolean;
  human_approval_required?: boolean;
  bdi_thresholds?: any;
  bdi_methodology?: any;
  sif_thresholds?: any;
  sla_policies?: any[];
  notification_channels?: any;
  updated_by?: string;
}

export interface DemoStatusResponse {
  demo_mode_active: boolean;
  status_label: string;
  current_simulated_time: string;
  simulated_time_offset_minutes: number;
  active_scenario?: string | null;
  loaded_report_id?: string | null;
  loaded_action_id?: string | null;
  loaded_hold_id?: string | null;
  external_notifications_suppressed: boolean;
}

export interface DemoPipelineStepItem {
  step_number: number;
  step_key: string;
  step_title: string;
  status: 'COMPLETED' | 'ACTIVE' | 'PENDING' | 'SKIPPED';
  summary: string;
  details?: Record<string, any> | null;
  timestamp: string;
}

export interface DemoScenarioExecutionResponse {
  scenario_type: string;
  status: string;
  summary: string;
  report_id: string;
  action_id?: string | null;
  hold_id?: string | null;
  bdi_score: number;
  sif_status: string;
  severity: string;
  pipeline_steps: DemoPipelineStepItem[];
  email_preview?: Record<string, any> | null;
  sla_info?: Record<string, any> | null;
}


