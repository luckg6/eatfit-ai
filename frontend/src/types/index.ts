export interface User {
  id: number;
  username: string;
  email: string;
  auto_memory_enabled: boolean;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface UserFoodProfile {
  id?: number;
  user_id?: number;
  nickname?: string;
  gender?: string;
  age?: number;
  height_cm?: number;
  weight_kg?: number;
  body_fat_percent?: number;
  target_weight_kg?: number;
  primary_goal?: string;
  activity_level?: string;
  training_frequency?: number;
  training_type?: string;
  food_preferences?: string;
  food_dislikes?: string;
  allergies?: string;
  budget_per_meal?: number;
  common_eating_scenarios?: string;
  sleep_sensitive: boolean;
  sleep_notes?: string;
  notes?: string;
}

// Memory types
export interface MemoryItem {
  id: number;
  user_id: number;
  memory_type: string;
  content: string;
  importance_score: number;
  source: string;
  status?: string;
  confidence_score?: number;
  source_message_id?: number;
  last_used_at?: string;
  metadata_json?: Record<string, any>;
  created_at: string;
  updated_at?: string;
}

export interface MealLog {
  id: number;
  user_id: number;
  meal_type: string;
  meal_time: string;
  food_text: string;
  scenario: string;
  estimated_calories: number;
  estimated_protein: number;
  estimated_carbs: number;
  estimated_fat: number;
  health_score?: number;
  sleep_impact: string;
  ai_comment?: string;
}

export interface RecommendedOption {
  name: string;
  why_recommended: string;
  estimated_calories: number;
  estimated_protein: number;
  estimated_carbs: number;
  estimated_fat: number;
  order_modification: string;
  suitable_for: string[];
  score: number;
}

export interface NotRecommendedOption {
  name: string;
  reason: string;
  better_alternative: string;
}

export interface AdviceResponse {
  situation_summary: string;
  goal_analysis: string;
  recommendation_strategy: string;
  recommended_options: RecommendedOption[];
  not_recommended: NotRecommendedOption[];
  today_remaining_advice: string;
  sleep_friendly_tips: string;
  training_day_tips: string;
  next_meal_advice: string;
  risk_level: string;
  risk_warnings: string[];
  one_sentence_summary: string;
}

export interface DailyPlanResponse {
  breakfast_suggestion: string;
  lunch_suggestion: string;
  dinner_suggestion: string;
  snack_suggestion: string;
  protein_focus: string;
  avoid_today: string[];
  sleep_reminder: string;
  one_day_strategy: string;
}

export interface WeeklyReviewResponse {
  week_summary: string;
  what_went_well: string[];
  main_problems: string[];
  protein_consistency: string;
  sleep_impact_analysis: string;
  eating_out_pattern: string;
  weight_and_body_fat_trend: string;
  next_week_strategy: string;
  next_week_actions: string[];
  warnings: string[];
}

export interface WeightRecord {
  id: number;
  user_id: number;
  weight_kg: number;
  record_date: string;
  note?: string;
  created_at: string;
}

export interface BodyFatRecord {
  id: number;
  user_id: number;
  body_fat_percent: number;
  record_date: string;
  note?: string;
  created_at: string;
}

export interface TrainingRecord {
  id: number;
  user_id: number;
  training_type: string;
  duration_minutes: number;
  intensity: string;
  record_date: string;
  note?: string;
  created_at: string;
}

// Chat types
export type ChatRole = 'user' | 'assistant';

export type ActionType = 'meal_log' | 'profile_update' | 'memory_confirm' | 'restaurant_recommendation';

export interface ChatAction {
  type: ActionType;
  data: {
    // meal_log
    food_text?: string;
    meal_type?: string;
    estimated_calories?: number;
    estimated_protein?: number;
    estimated_carbs?: number;
    estimated_fat?: number;
    calorie_confidence?: number;
    nutrition_source?: string;
    scenario?: string;
    // profile_update
    updates?: Record<string, any>;
    old_values?: Record<string, any>;
    display_text?: string;
    // memory_confirm
    memory_type?: string;
    importance_score?: number;
    confidence_score?: number;
    // restaurant_recommendation
    restaurants?: any[];
    // common
    source_message_id?: number;
  };
  status: 'pending' | 'confirmed' | 'executed' | 'cancelled';
}

export interface ChatMessage {
  id: string;
  role: ChatRole;
  content: string;
  created_at?: string;
  action?: ChatAction;
}

// Agent trace types
export interface AgentStep {
  step: string;
  data: Record<string, any>;
  timestamp: string;
}