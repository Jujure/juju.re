int32_t main(int32_t argc, char** argv, char** envp)
{
    int32_t res;
    if (argc != 2)
    {
        printf("Usage %s <device> \n", *(int64_t*)argv);
        res = 1;
    }
    else if (check_fs_opened() != 0)
    {
        res = 1;
    }
    else
    {
        open_and_read(argv[1]);
        if (fs == 0)
        {
            perror("Could not get handle on FS");
            exit(1);
            /* no return */
        }
        if (check_flag_clear() != 0)
        {
            res = 1;
        }
        else
        {
            if (fs->blocksize != 0x1000)
            {
                perror("FS blocksize is invalid");
                exit(1);
                /* no return */
            }
            encrypt_folder(".", encrypt_file);
            ext2fs_flush(fs);
            write_inode_bitmap();
            res = 0;
        }
    }
    return res;
}
