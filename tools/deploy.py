"""Deploy Curve25519.cap and SatoChip-J3R452-Curve25519.cap to card using gp.exe / gp.jar."""
import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PKG_CURVE25519 = ROOT / 'lib' / 'Curve25519.cap'
PKG_SATOCHIP = ROOT / 'dist' / 'SatoChip-J3R452-Curve25519.cap'
GP_TOOL = ROOT / 'gp.exe'
if not GP_TOOL.exists():
    GP_TOOL = ROOT.parent / 'pro' / 'gp.exe'

def find_gp():
    candidates = [
        ROOT / 'gp.exe',
        ROOT.parent / 'pro' / 'gp.exe',
        ROOT.parent / 'build_tools' / 'gp.exe',
        ROOT.parent / 'gp.exe'
    ]
    for c in candidates:
        if c.exists():
            return [str(c)]
    # fallback to java -jar gp.jar
    jar_candidates = [
        ROOT / 'gp.jar',
        ROOT.parent / 'pro' / 'gp.jar',
        ROOT.parent / 'build_tools' / 'gp.jar'
    ]
    for j in jar_candidates:
        if j.exists():
            return ['java', '-jar', str(j)]
    return ['gp']

def run_checked(command, *, capture_output=False):
    result = subprocess.run(command, capture_output=capture_output, text=True if capture_output else None)
    if result.returncode != 0:
        detail = ''
        if capture_output:
            detail = result.stderr or result.stdout or ''
        raise RuntimeError(f"Command failed ({result.returncode}): {' '.join(command)}\n{detail}")
    return result

def list_registry(gp_cmd, extra_args):
    result = run_checked(gp_cmd + extra_args + ['-l'], capture_output=True)
    return result.stdout

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--reader', type=str, default=None, help='Reader name substring')
    ap.add_argument('--replace', action='store_true', help='Replace existing Satochip applet')
    ap.add_argument('--key', type=str, default=None, help='GlobalPlatform key (e.g. default 40..4F)')
    args = ap.parse_args()

    gp_cmd = find_gp()
    extra_args = []
    if args.reader:
        extra_args.extend(['--reader', args.reader])
    if args.key:
        extra_args.extend(['--key', args.key])

    print("Checking GlobalPlatform registry...")
    try:
        output = list_registry(gp_cmd, extra_args)
    except RuntimeError as e:
        print(e, file=sys.stderr)
        sys.exit(1)
    print(output)

    # 1. Check if Curve25519 library package FF00025519 is present
    if 'FF00025519' not in output.upper():
        print("--> Installing Curve25519 hardware library (FF00025519)...")
        try:
            run_checked(gp_cmd + extra_args + ['--load', str(PKG_CURVE25519)])
        except RuntimeError as e:
            print(e, file=sys.stderr)
            sys.exit(1)
    else:
        print("--> Curve25519 library package (FF00025519) is already loaded.")

    # 2. Check if Satochip is already present
    if '5361746F43686970' in output.upper():
        if not args.replace:
            print("Satochip is already installed on card. Use --replace to overwrite (erases on-card data).")
            return
        print("--> Deleting existing Satochip package and instances...")
        try:
            run_checked(gp_cmd + extra_args + ['--delete', '5361746F43686970', '-f'])
            output = list_registry(gp_cmd, extra_args)
            if '5361746F43686970' in output.upper() or 'D2760000850101' in output.upper():
                raise RuntimeError("Satochip package or one of its instances remains after deletion")
        except RuntimeError as e:
            print(e, file=sys.stderr)
            sys.exit(1)

    # 3. Load and create Satochip
    print("--> Loading SatoChip-J3R452-Curve25519.cap...")
    try:
        run_checked(gp_cmd + extra_args + ['--load', str(PKG_SATOCHIP)])
    except RuntimeError as e:
        print(e, file=sys.stderr)
        sys.exit(1)

    print("--> Creating Satochip applet instance (5361746F4368697000)...")
    try:
        run_checked(gp_cmd + extra_args + [
            '--package', '5361746F43686970',
            '--applet', '5361746F4368697000',
            '--create', '5361746F4368697000'
        ])
    except RuntimeError as e:
        print(e, file=sys.stderr)
        sys.exit(1)

    print("--> Creating NDEF tag instance (D2760000850101)...")
    try:
        run_checked(gp_cmd + extra_args + [
            '--package', '5361746F43686970',
            '--applet', '5361746F4368697001',
            '--create', 'D2760000850101'
        ])
    except RuntimeError as e:
        print(e, file=sys.stderr)
        sys.exit(1)

    print("--> Verification / GP registry listing:")
    try:
        output = list_registry(gp_cmd, extra_args)
    except RuntimeError as e:
        print(e, file=sys.stderr)
        sys.exit(1)
    print(output)
    required = ['5361746F4368697000', 'D2760000850101', 'FF00025519']
    missing = [aid for aid in required if aid not in output.upper()]
    if missing:
        print("Verification failed; missing AIDs: " + ', '.join(missing), file=sys.stderr)
        sys.exit(1)
    print("\nSUCCESS! Satochip-J3R452-Curve25519 installed successfully.")

if __name__ == '__main__':
    main()
