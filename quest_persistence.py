
from datetime import datetime, date

LAST_RESET_DATE = date.today()


HERO_DATA = {
    "xp": 0,
    "level": 1,
    "total_quests": 3
}

QUESTS = {
    1: {
        "id": 1,
        "title": "Defeat the Dental Dragon!",
        "description": "Brush your teeth for 2 minutes to slay the dragon.",
        "status": "active",
        "icon": "🪥",
        "required_time_start": "06:00",
        "required_time_end": "09:00",
        "xp_reward": 50
    },
    2: {
        "id": 2,
        "title": "Tame Up for Adventure",
        "description": "Put on your clothes and shoes.",
        "status": "locked",
        "icon": "👟",
        "required_time_start": "06:30",
        "required_time_end": "09:30",
        "xp_reward": 100
    },
    3: {
        "id": 3,
        "title": "Fuel the Breakfast",
        "description": "Eat a healthy breakfast.",
        "status": "locked",
        "icon": "🥣",
        "required_time_start": "07:00",
        "required_time_end": "09:30",
        "xp_reward": 50
    }
}

SUBMISSIONS = []

def check_and_reset_daily():
    global LAST_RESET_DATE, SUBMISSIONS
    today = date.today()
    if today > LAST_RESET_DATE:
        LAST_RESET_DATE = today
        SUBMISSIONS = []
        keys = sorted(list(QUESTS.keys()))
        for i, qid in enumerate(keys):
            QUESTS[qid]["status"] = "active" if i == 0 else "locked"

def get_all_quests():
    check_and_reset_daily()
    return list(QUESTS.values())

def get_hero_data():
    check_and_reset_daily()
    completed = sum(1 for q in QUESTS.values() if q["status"] == "completed" or q["status"] == "pending")
    return {
        "xp": HERO_DATA["xp"],
        "level": HERO_DATA["level"],
        "completed": completed,
        "total": len(QUESTS)
    }

def add_quest(title, description, icon, xp_reward):
    new_id = max(QUESTS.keys()) + 1 if QUESTS else 1
    QUESTS[new_id] = {
        "id": new_id,
        "title": title,
        "description": description,
        "status": "locked",
        "icon": icon,
        "required_time_start": "00:00",
        "required_time_end": "23:59",
        "xp_reward": int(xp_reward)
    }
    HERO_DATA["total_quests"] = len(QUESTS)
    if len(QUESTS) == 1:
        QUESTS[new_id]["status"] = "active"
    return QUESTS[new_id]

def remove_quest(quest_id):
    if quest_id in QUESTS:
        del QUESTS[quest_id]
        global SUBMISSIONS
        SUBMISSIONS = [s for s in SUBMISSIONS if s["quest_id"] != quest_id]
        HERO_DATA["total_quests"] = len(QUESTS)
        
        # Adjust active state if needed
        has_active = any(q["status"] in ["active", "pending"] for q in QUESTS.values())
        all_completed = all(q["status"] == "completed" for q in QUESTS.values())
        
        if not has_active and not all_completed and len(QUESTS) > 0:
            keys = sorted(list(QUESTS.keys()))
            for k in keys:
                if QUESTS[k]["status"] == "locked":
                    QUESTS[k]["status"] = "active"
                    break
        return True
    return False

def add_submission(quest_id, file_path, metadata, sticker):
    check_and_reset_daily()
    sub = {
        "id": len(SUBMISSIONS) + 1,
        "quest_id": quest_id,
        "file_path": file_path,
        "metadata": metadata,
        "sticker": sticker,
        "status": "pending",
        "submitted_at": datetime.now().isoformat()
    }
    SUBMISSIONS.append(sub)
    if quest_id in QUESTS:
        QUESTS[quest_id]["status"] = "pending"
    return sub

def get_pending_submissions():
    check_and_reset_daily()
    return [s for s in SUBMISSIONS if s["status"] == "pending"]

def approve_submission(sub_id):
    for sub in SUBMISSIONS:
        if sub["id"] == sub_id:
            sub["status"] = "approved"
            quest_id = sub["quest_id"]
            if quest_id in QUESTS:
                QUESTS[quest_id]["status"] = "completed"
                HERO_DATA["xp"] += QUESTS[quest_id]["xp_reward"]
                
                keys = sorted(list(QUESTS.keys()))
                idx = keys.index(quest_id)
                if idx + 1 < len(keys):
                    next_id = keys[idx + 1]
                    if QUESTS[next_id]["status"] == "locked":
                        QUESTS[next_id]["status"] = "active"
            return True
    return False

def get_quest(quest_id):
    return QUESTS.get(quest_id)
