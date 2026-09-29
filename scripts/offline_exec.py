#!/usr/bin/env python3
"""Linux verification helper: deny socket/connect syscalls, then exec a command.

Requires libseccomp.so.2. The filter is inherited across exec and by children.
The application itself does not need libseccomp; this verifies its offline use.
"""
import ctypes
import errno
import os
import sys


def deny_network():
    lib=ctypes.CDLL('libseccomp.so.2',use_errno=True)
    lib.seccomp_init.argtypes=[ctypes.c_uint32];lib.seccomp_init.restype=ctypes.c_void_p
    lib.seccomp_syscall_resolve_name.argtypes=[ctypes.c_char_p];lib.seccomp_syscall_resolve_name.restype=ctypes.c_int
    lib.seccomp_rule_add.argtypes=[ctypes.c_void_p,ctypes.c_uint32,ctypes.c_int,ctypes.c_uint]
    lib.seccomp_load.argtypes=[ctypes.c_void_p];lib.seccomp_release.argtypes=[ctypes.c_void_p]
    context=lib.seccomp_init(0x7fff0000)
    if not context:raise OSError('seccomp_init failed')
    try:
        for name in (b'socket',b'connect'):
            number=lib.seccomp_syscall_resolve_name(name)
            if number<0 or lib.seccomp_rule_add(context,0x00050000|errno.EPERM,number,0)!=0:
                raise OSError('seccomp_rule_add failed')
        if lib.seccomp_load(context)!=0:raise OSError('seccomp_load failed')
    finally:
        lib.seccomp_release(context)


if __name__=='__main__':
    if len(sys.argv)<2:raise SystemExit('usage: offline_exec.py COMMAND [ARGS...]')
    deny_network()
    os.execvp(sys.argv[1],sys.argv[1:])
