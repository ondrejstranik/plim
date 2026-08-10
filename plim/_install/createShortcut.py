'''
script to create desktop shortcuts for all run scripts in plim.main
'''
import sys
from pathlib import Path

from pyshortcuts import make_shortcut

SCRIPTS = {
    'runRealIFC': 'Real IFC',
    'runVirtualIFC': 'Virtual IFC',
    'runRealMSC': 'Real MSC',
    'runSImageAnalyser': 'Spectral Image Analyser',
    'runSignalAnalyser': 'Signal Analyser',
}

def _script_path(script):
    ''' full path to the installed console-script executable for `script`

    pyshortcuts only recognizes `script` as a real executable if it is
    given a path that exists on disk -- a bare entry-point name resolves
    to nothing and silently falls back to `python.exe <name>`, which then
    fails since `<name>` isn't a real file relative to the shortcut's
    working directory.
    '''
    scripts_dir = Path(sys.executable).parent
    if sys.platform == 'win32':
        scripts_dir = scripts_dir / 'Scripts'
        script = f'{script}.exe'
    return scripts_dir / script

def main():
    for script, name in SCRIPTS.items():
        make_shortcut(
            script=str(_script_path(script)),
            name=name,
            description=f'Plim {name}',
            terminal=False,
            desktop=True,
            startmenu=False,
            folder='plim',
        )

if __name__ == "__main__":
    main()
