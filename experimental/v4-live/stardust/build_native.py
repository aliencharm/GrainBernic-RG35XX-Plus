"""Build Stardust for ARM64 runtime or native-host DSP verification."""
import argparse,os,subprocess,shutil
from pathlib import Path
root=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--host',action='store_true');p.add_argument('--output',type=Path);p.add_argument('--cc');p.add_argument('--sysroot',type=Path);args=p.parse_args()
output=args.output or root/'libgrainbrick_stardust.so'
tool=Path('/workspace/v4-toolchain/root')
bundled=str(tool/'usr/bin/aarch64-linux-gnu-gcc-12')
compiler=args.cc or os.environ.get('STARDUST_CC') or ('cc' if args.host else shutil.which('aarch64-linux-gnu-gcc') or bundled)
command=[compiler]
if args.sysroot:command+=['--sysroot='+str(args.sysroot)]
elif not args.host and compiler==bundled:
    command+=['--sysroot='+str(tool),'-B'+str(tool/'usr/lib/gcc-cross/aarch64-linux-gnu/12')+'/', '-B'+str(tool/'usr/aarch64-linux-gnu/bin')+'/']
env=dict(os.environ)
if compiler==bundled:env['LD_LIBRARY_PATH']='/workspace/v4-toolchain/host-libs'+(':'+env['LD_LIBRARY_PATH'] if env.get('LD_LIBRARY_PATH') else '')
output.parent.mkdir(parents=True,exist_ok=True)
subprocess.run(command+['-std=c99','-O3','-fPIC','-shared','-Wall','-Wextra',str(root/'stardust.c'),'-o',str(output),'-lm'],check=True,env=env)
print(output)
