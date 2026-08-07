'''
script to create desktop shortcuts for all run scripts in plim.main
'''
from pyshortcuts import make_shortcut

SCRIPTS = {
    'runRealIFC': 'Real IFC',
    'runVirtualIFC': 'Virtual IFC',
    'runRealMSC': 'Real MSC',
    'runSImageAnalyser': 'Spectral Image Analyser',
    'runSignalAnalyser': 'Signal Analyser',
}

def main():
    for script, name in SCRIPTS.items():
        make_shortcut(
            script=script,
            name=name,
            description=f'Plim {name}',
            terminal=False,
            desktop=True,
            startmenu=False,
            folder='plim',
        )

if __name__ == "__main__":
    main()
