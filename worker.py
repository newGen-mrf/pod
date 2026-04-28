import os
import sys
import json
import logging
from datetime import datetime

import config
import trend_engine
import design_generator
import seo_generator
from uploaders.printify import upload_to_printify
from uploaders.redbubble import upload_to_redbubble
from uploaders.pinterest import promote_on_pinterest

# Setup basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(config.LOG_DIR, f"worker_{datetime.now().strftime('%Y%m%d')}.log")) if os.path.exists(config.LOG_DIR) else logging.NullHandler(),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("pod.worker")


def load_state() -> dict:
    """Load the pipeline state tracking file."""
    if os.path.exists(config.STATE_FILE):
        try:
            with open(config.STATE_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Could not load state file: {e}")
            
    return {
        "run_count": 0,
        "history": [],
        "uploaded": {
            "printify": [],
            "redbubble": [],
            "pinterest": []
        },
        "trends_used": [],
        "last_error": None
    }


def save_state(state: dict):
    """Save the pipeline state tracking file."""
    with open(config.STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def cleanup_old_files(state: dict):
    """Keep only the last N designs locally to save space."""
    history = state.get("history", [])
    if len(history) > config.MAX_HISTORY:
        to_remove = history[:-config.MAX_HISTORY]
        state["history"] = history[-config.MAX_HISTORY:]
        
        for item in to_remove:
            img_path = item.get("design_path")
            if img_path and os.path.exists(img_path):
                try:
                    os.remove(img_path)
                    logger.info(f"Cleaned up old design: {img_path}")
                except Exception as e:
                    logger.warning(f"Could not delete {img_path}: {e}")


def run_worker(dry_run: bool = False):
    """Main orchestration function."""
    os.makedirs(config.OUTPUT_DIR, exist_ok=True)
    os.makedirs(config.LOG_DIR, exist_ok=True)
    
    state = load_state()
    state["run_count"] = state.get("run_count", 0) + 1
    
    logger.info(f"=== Starting POD Pipeline Run #{state['run_count']} ===")
    if dry_run:
        logger.info("*** DRY RUN MODE: No uploads will occur ***")
        
    try:
        # Phase 1: Planning
        category = trend_engine.pick_category()
        trend = trend_engine.discover_trend(category, state)
        
        # Phase 2: Creation
        design_path = design_generator.generate_design(trend, category)
        seo = seo_generator.generate_seo(trend, category)
        
        results = {}
        
        # Phase 3: Distribution (if not dry run)
        if not dry_run:
            results["printify"] = upload_to_printify(design_path, seo)
            results["redbubble"] = upload_to_redbubble(design_path, seo, state)
            results["pinterest"] = promote_on_pinterest(design_path, seo, results)
        else:
            logger.info("DRY RUN: Skipping platform uploads")
            
        # Update State
        if "trends_used" not in state:
            state["trends_used"] = []
        state["trends_used"].append(trend)
        if len(state["trends_used"]) > config.MAX_HISTORY * 2:
            state["trends_used"] = state["trends_used"][-config.MAX_HISTORY * 2:]
            
        state["history"].append({
            "timestamp": datetime.now().isoformat(),
            "trend": trend,
            "category": category["name"],
            "design_path": design_path,
            "seo_title": seo["title"],
            "results": results
        })
        
        today = datetime.now().strftime("%Y-%m-%d")
        if "uploaded" not in state:
            state["uploaded"] = {}
        for plat, res in results.items():
            if res.get("status") == "success":
                state["uploaded"].setdefault(plat, []).append({
                    "date": today,
                    "trend": trend
                })

    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        state["last_error"] = str(e)
        
    finally:
        cleanup_old_files(state)
        save_state(state)
        logger.info(f"=== Completed Run #{state['run_count']} ===")


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    run_worker(dry_run=dry_run)
