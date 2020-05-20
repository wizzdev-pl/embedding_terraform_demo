import os
import sys

from wist.common import _running_from_source


if _running_from_source():
    _this_file_path = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(os.path.join(_this_file_path, '../'))


if __name__ == '__main__':
    from wist.__main__ import main
    main()
    
