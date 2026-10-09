"""Fixed Linux child bootstrap: set limits before native imports, without preexec."""
import os
import sys

if __name__ == "__main__":
    memory, cpu = sys.argv[1:3]
    if os.name != "nt":
        import resource
        size = int(memory)*1024*1024
        resource.setrlimit(resource.RLIMIT_AS, (size, size))
        resource.setrlimit(resource.RLIMIT_CPU, (int(cpu), int(cpu)))
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    # Command originates only in the supervisor's fixed server command factory.
    # Recipe JSON has no executable/module/path fields.
    command = sys.argv[3:]
    os.execv(command[0], command)
