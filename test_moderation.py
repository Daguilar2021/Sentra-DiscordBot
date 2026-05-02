import time
import os
import sys

# Add the project root to the python path so imports work correctly
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from Bot.DB.dbLink import get_session
from Bot.DB.dbAccessLayer import Infraction
from Bot.Moderation.engine import ModerationEngine

def run_test():
    print("⏳ Loading moderation engine (this may take a few seconds)...")
    engine = ModerationEngine()
    print("✅ Engine loaded!\n")

    texts_to_test = [
        "kys",
        "I like this project",
        "I Dont like this project",
        "you are stupid",
        "This bot is complete garbage, you are all stupid idiots and this entire server is a terrible place full of losers. I hate it here."
    ]

    for test_text in texts_to_test:
        print(f"Testing text: '{test_text}'")
        
        start_time = time.perf_counter()
        result = engine.analyze(test_text)
        processing_time = (time.perf_counter() - start_time) * 1000
        
        print(f"  Toxic: {result['toxic']}")
        print(f"  Score: {result['score']:.4f}")
        print(f"  Keywords: {result['keywords']}")
        print(f"  Time: {processing_time:.0f}ms\n")

        if result["toxic"]:
            print("  [Action] Saving test infraction to DB...")
            try:
                db = get_session()
                infraction = Infraction(
                    guild_id=123456789,  # Dummy Guild ID
                    user_id=987654321,   # Dummy User ID
                    message_content=test_text,
                    toxicity_score=result["score"],
                    keywords=result["keywords"],
                    action_taken="bot_test",
                    created_at=int(time.time()),
                    reviewed=False,
                )
                db.add(infraction)
                db.commit()
                db.close()
                print("  ✅ Infraction successfully saved!")
            except Exception as e:
                print(f"  ❌ Failed to save to database: {e}")
        else:
            print("  [Action] Ignored (score under threshold).")
        print("-" * 40)

if __name__ == "__main__":
    run_test()
