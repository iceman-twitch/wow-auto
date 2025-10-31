"""
WoWAuto - Sequence Runner (Backward compatibility wrapper)

This file is maintained for backward compatibility.
For new code, use: from wowauto import SequenceRunner
"""

# Import the new modular version
from wowauto import SequenceRunner

# Re-export for backward compatibility
__all__ = ["SequenceRunner"]


# Backward compatibility - run if executed directly
if __name__ == "__main__":

    # Example usage
    runner = SequenceRunner(dry_run=True)
    try:
        runner.load_file("example_sequences.json")
        print("Sequences:", runner.list_sequences())
        runner.run_forever()
    except FileNotFoundError:
        print("Place example_sequences.json next to this script to test.")