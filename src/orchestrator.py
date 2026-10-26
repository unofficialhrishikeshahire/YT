"""Pipeline Orchestrator.
Coordinates execution of Agent 1 through Agent 5 with CLI flags:
--dry-run, --mock, --agent, --topic, --run-id.
"""

import argparse
import sys
import time
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

from src.config import load_config
from src.agents.researcher import ResearcherAgent
from src.agents.scriptwriter import ScriptwriterAgent
from src.agents.visual_director import VisualDirectorAgent
from src.agents.video_editor import VideoEditorAgent
from src.agents.publisher import PublisherAgent
from src.utils.logger import setup_logger


def parse_args():
    parser = argparse.ArgumentParser(
        description="Weekly Automated YouTube Documentary Pipeline"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Skip uploading to YouTube and sending Slack notifications",
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Use pre-grounded mock responses to test without consuming API quota",
    )
    parser.add_argument(
        "--agent",
        type=str,
        choices=["researcher", "scriptwriter", "visual_director", "video_editor", "publisher", "all"],
        default="all",
        help="Run only a specific agent or 'all' (default: all)",
    )
    parser.add_argument(
        "--topic",
        type=str,
        default=None,
        help="Override topic selection with an explicit documentary topic",
    )
    parser.add_argument(
        "--run-id",
        type=str,
        default=None,
        help="Custom run ID folder name in /output (default: run_YYYYMMDD_HHMMSS)",
    )
    return parser.parse_args()


def main():
    load_dotenv()
    args = parse_args()

    config = load_config("config.yaml")

    run_id = args.run_id or f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    run_dir = Path("output") / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    logger = setup_logger("orchestrator", log_file=run_dir / "pipeline.log")
    logger.info("=" * 60)
    logger.info(f"Starting Weekly Documentary Pipeline [Run ID: {run_id}]")
    logger.info(f"Mode: {'MOCK' if args.mock else 'LIVE'}, Dry Run: {args.dry_run}")
    logger.info("=" * 60)

    current_agent_name = "initialization"

    try:
        # Agent 1: Researcher
        current_agent_name = "researcher"
        if args.agent in ["researcher", "all"]:
            researcher = ResearcherAgent(config, run_dir, mock=args.mock)
            research_path = researcher.run(topic_override=args.topic)
        else:
            research_path = run_dir / "research.md"

        # Agent 2: Scriptwriter
        current_agent_name = "scriptwriter"
        if args.agent in ["scriptwriter", "all"]:
            scriptwriter = ScriptwriterAgent(config, run_dir, mock=args.mock)
            script_path = scriptwriter.run(research_path)
        else:
            script_path = run_dir / "script.json"

        # Agent 3: Visual Director
        current_agent_name = "visual_director"
        if args.agent in ["visual_director", "all"]:
            visual_director = VisualDirectorAgent(config, run_dir, mock=args.mock)
            visual_plan_path = visual_director.run(script_path)
        else:
            visual_plan_path = run_dir / "visual_plan.json"

        # Agent 4: Video Editor
        current_agent_name = "video_editor"
        if args.agent in ["video_editor", "all"]:
            video_editor = VideoEditorAgent(config, run_dir, mock=args.mock)
            video_path = video_editor.run(visual_plan_path)
        else:
            video_path = run_dir / "final_video.mp4"

        # Agent 5: Publisher & Notifier
        current_agent_name = "publisher"
        thumbnail_path = run_dir / "thumbnail.png"
        if args.agent in ["publisher", "all"]:
            publisher = PublisherAgent(config, run_dir, mock=args.mock, dry_run=args.dry_run)
            metadata = publisher.run(
                video_path=video_path,
                thumbnail_path=thumbnail_path,
                research_file=research_path,
                script_file=script_path,
            )
        else:
            metadata = {}

        logger.info("=" * 60)
        logger.info(f"Pipeline Succeeded for {run_id}!")
        logger.info(f"Final Video:    {video_path}")
        logger.info(f"Video URL:      {metadata.get('video_url', 'N/A')}")
        logger.info(f"SEO Title:      {metadata.get('title', 'N/A')}")
        logger.info(f"Output Folder:  {run_dir.resolve()}")
        logger.info("=" * 60)

    except Exception as e:
        logger.exception(f"Pipeline failed at run {run_id} during agent '{current_agent_name}': {e}")
        # Send Slack failure notification if configured
        try:
            PublisherAgent.send_slack_failure_alert(
                agent_name=current_agent_name,
                error_message=str(e),
            )
        except Exception:
            pass
        sys.exit(1)


if __name__ == "__main__":
    main()
