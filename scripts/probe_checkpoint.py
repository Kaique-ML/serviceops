import argparse
import os

from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.types import Command

from serviceops.graphs.conversation import build_graph


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=["start", "resume"])
    parser.add_argument("thread_id")
    args = parser.parse_args()
    url = os.environ["SERVICEOPS_DATABASE_URL"].replace("postgresql+psycopg://", "postgresql://")
    config = {"configurable": {"thread_id": args.thread_id}}
    with PostgresSaver.from_conn_string(url) as saver:
        saver.setup()
        graph = build_graph(saver)
        if args.phase == "start":
            result = graph.invoke(
                {"intent": "support_case", "proposal_id": "checkpoint-probe"}, config=config
            )
            assert result.get("__interrupt__"), result
            print("paused=true")
        else:
            result = graph.invoke(Command(resume="authenticated-confirmed"), config=config)
            assert result["phase"] == "resume", result
            print(f"resumed=true decision={result['decision']}")


if __name__ == "__main__":
    main()
