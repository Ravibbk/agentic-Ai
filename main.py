from agent import ResearchAgent


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Run the local agentic research agent")
    parser.add_argument("--goal", default="Summarize the benefits of agentic AI", help="Research goal")
    args = parser.parse_args()

    agent = ResearchAgent()
    report = agent.run(args.goal)
    print("\n--- FINAL REPORT ---\n")
    print(report)


if __name__ == "__main__":
    main()
