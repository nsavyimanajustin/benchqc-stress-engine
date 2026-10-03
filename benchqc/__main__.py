import os
import sys

# Ensure parent directory is in sys.path
package_parent = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if package_parent not in sys.path:
    sys.path.insert(0, package_parent)

from benchqc.cli import main

if __name__ == "__main__":
    sys.exit(main())
