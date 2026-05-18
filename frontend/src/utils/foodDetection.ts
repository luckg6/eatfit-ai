const FOOD_PATTERNS = [
  /吃了(.+)/,
  /刚吃了(.+)/,
  /刚才吃了(.+)/,
  /午餐吃了(.+)/,
  /中餐吃了(.+)/,
  /晚餐吃了(.+)/,
  /早饭吃了(.+)/,
  /早餐吃了(.+)/,
  /点了(.+)/,
  /吃了点(.+)/,
  /吃了午餐(.+)/,
  /吃了晚餐(.+)/,
  /吃了早饭(.+)/,
  /吃了早餐(.+)/,
];

const TRAINING_PATTERNS = [
  /刚训练了(.+)/,
  /训练了(.+)/,
  /锻炼了(.+)/,
  /跑步了(.+)/,
  /今天训练(.+)/,
  /去健身(.+)/,
];

export interface ParsedFood {
  food_text: string;
  meal_type?: string;
}

export function detectFoodMentions(text: string): ParsedFood[] {
  const results: ParsedFood[] = [];

  // Determine meal type from context
  let mealType = 'SNACK';
  if (text.includes('早餐') || text.includes('早饭')) mealType = 'BREAKFAST';
  else if (text.includes('午餐') || text.includes('中餐')) mealType = 'LUNCH';
  else if (text.includes('晚餐') || text.includes('晚餐')) mealType = 'DINNER';

  for (const pattern of FOOD_PATTERNS) {
    const match = text.match(pattern);
    if (match && match[1]) {
      results.push({
        food_text: match[1].trim(),
        meal_type: mealType,
      });
    }
  }

  return results;
}

export interface ParsedTraining {
  training_type: string;
  duration_minutes?: number;
}

export function detectTrainingMentions(text: string): ParsedTraining[] {
  const results: ParsedTraining[] = [];

  for (const pattern of TRAINING_PATTERNS) {
    const match = text.match(pattern);
    if (match && match[1]) {
      results.push({
        training_type: match[1].trim(),
      });
    }
  }

  // Also detect simple cases
  if (text.includes('跑步') && !results.some(r => r.training_type.includes('跑步'))) {
    results.push({ training_type: '跑步' });
  }
  if ((text.includes('健身') || text.includes('训练')) && !results.some(r => r.training_type.includes('健身') || r.training_type.includes('训练'))) {
    results.push({ training_type: '健身/力量训练' });
  }

  return results;
}