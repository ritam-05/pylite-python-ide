from pylite.cli import main
import sys

if __name__ == "__main__":
    # Force the GUI flag if launched directly as a desktop app
    if len(sys.argv) == 1:
        sys.argv.append("--gui")
    main()