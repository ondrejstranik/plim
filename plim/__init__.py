from pathlib import Path

import __main__

dataFolder = str(Path(__file__).parent.joinpath('DATA'))

testVar = 'ahoj'

__main__.testVar = testVar
