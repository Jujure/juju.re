int64_t _start()
{
    int64_t path = '_';
    syscall(sys_unlink {0x57}, &path);
    int32_t fd = syscall(sys_open {2}, &path, O_CREAT | O_WRONLY);
    syscall(sys_write {1}, fd, &__elf_header, 0x1a228);
    syscall(sys_close {3}, fd);
    syscall(sys_execve {0x3b}, &path, nullptr, nullptr);
}