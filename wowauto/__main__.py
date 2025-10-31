"""Main entry point for wowauto as a module."""
from wowauto import SequenceRunner


if __name__ == "__main__":
    # Example usage
    runner = SequenceRunner(dry_run=True)
    try:
        runner.load_file("example_sequences.json")
        print("Sequences:", runner.list_sequences())
        runner.run_forever()
    except FileNotFoundError:
        print("Place example_sequences.json next to this script to test.")
