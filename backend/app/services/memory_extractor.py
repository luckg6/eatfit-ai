import json
import re
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.memory import MemoryItem
from app.services.llm_service import get_llm_service


# Keywords that trigger memory extraction
MEMORY_TRIGGERS = {
    "DIET_PREFERENCE": [
        r"喜欢吃(.+)",
        r"喜欢(.+?[食物菜品])",
        r"常吃(.+)",
        r"一般吃(.+)",
    ],
    "FOOD_DISLIKE": [
        r"不喜欢(.+)",
        r"不能吃(.+)",
        r"吃不了(.+)",
        r"过敏(.+?)(?:过敏|反应)",
        r"(?:乳糖|海鲜|麸质|坚果)(?:不耐|过敏)",
    ],
    "ALLERGY_INTOLERANCE": [
        r"过敏(.+)",
        r"(?:乳糖|麸质|海鲜|坚果)不耐",
        r"(?:吃了|喝了).*(?:过敏|不舒服|拉肚子)",
    ],
    "PROGRESS": [
        r"想(增肌|减脂|维持|控糖|改善睡眠)",
        r"目标(.+)",
        r"最近在(.+)(?:训练|运动|减肥)",
        r"(?:已经|已经)减肥了(.+)",
    ],
    "TRAINING_HABIT": [
        r"每周训练([一二三四五六日天几次]+)",
        r"训练频率(.+)",
        r"平时(.+?[天次周]?训练)",
        r"(跑步|力量|瑜伽|游泳|健身)(?:频率|时间|习惯)",
    ],
    "SLEEP_TRIGGER": [
        r"(?:睡眠|觉)被.*(影响|影响睡眠)",
        r"(?:咖啡|茶|奶茶|可乐).*睡不着",
        r"(?:晚上|睡前).*吃.*(?:睡|着)",
        r"睡眠.*(?:浅|差|失眠|早醒)",
    ],
    "BODY_CONDITION": [
        r"胃(?:不|不太)舒服",
        r"容易水肿",
        r"容易疲劳",
        r"(?:上火|长痘|便秘)",
    ],
    "LIFE_CONSTRAINT": [
        r"没有厨房",
        r"主要外食",
        r"预算有限",
        r"学校食堂",
        r"只能吃食堂",
        r"只能点外卖",
    ],
    "DIET_CONSTRAINT": [
        r"少油",
        r"少糖",
        r"少盐",
        r"多蛋白",
        r"(?:不|很少)喝奶茶",
        r"不吃.*(零食|甜食|油炸)",
    ],
}


def extract_memories_from_text(
    user_question: str,
    ai_response: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Extract memories from user text and AI response using keyword triggers."""
    extracted = []
    combined_text = f"{user_question} {ai_response.get('one_sentence_summary', '')}"

    for memory_type, patterns in MEMORY_TRIGGERS.items():
        for pattern in patterns:
            match = re.search(pattern, combined_text)
            if match:
                content = match.group(0)
                # Avoid duplicates
                if not any(m["content"] == content for m in extracted):
                    extracted.append({
                        "memoryType": memory_type,
                        "content": content,
                        "importanceScore": 5,
                        "source": "auto_extracted"
                    })
                break  # Only one match per type

    # Cap at 3
    return extracted[:3]


def is_significant_preference(content: str, existing_memories: List[MemoryItem]) -> bool:
    """Check if a preference has been mentioned multiple times."""
    count = sum(1 for m in existing_memories if content in m.content)
    return count >= 2


class MemoryExtractor:
    """Proactive memory extraction service."""

    @staticmethod
    async def extract_and_save(
        db: Session,
        user: User,
        user_question: str,
        ai_response: Dict[str, Any]
    ):
        """Extract significant memories and save to database."""
        if not user.auto_memory_enabled:
            return

        # Keyword-triggered extraction (lightweight, no LLM call)
        extracted = extract_memories_from_text(user_question, ai_response)

        if not extracted:
            return

        # Check existing memories to avoid noise
        existing = db.query(MemoryItem).filter(
            MemoryItem.user_id == user.id
        ).all()

        for mem in extracted:
            # Skip if already exists
            existing_same = next(
                (e for e in existing if e.memory_type == mem["memoryType"] and e.content == mem["content"]),
                None
            )
            if existing_same:
                continue

            # Skip if it's a repeated preference (noise filter)
            if mem["memoryType"] in ("DIET_PREFERENCE", "FOOD_DISLIKE"):
                if not is_significant_preference(mem["content"], existing):
                    continue

            new_mem = MemoryItem(
                user_id=user.id,
                memory_type=mem["memoryType"],
                content=mem["content"],
                importance_score=mem["importanceScore"],
                source=mem["source"]
            )
            db.add(new_mem)

        try:
            db.commit()
        except Exception:
            db.rollback()