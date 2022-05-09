int32_t main(int32_t argc, char** argv, char** envp)
{
    char input[0x400];
    ssize_t len = read(0, &input, 0x400);
    if (len <= 0)
    {
        puts("Error.");
        exit(1);
        /* no return */
    }
    int32_t res = check(&input, len);
    if (res == 0)
    {
        FILE* file = fopen("flag.txt", &r);
        if (file == 0)
        {
            puts("Well done! You can submit your i…");
            exit(1);
            /* no return */
        }
        char flag[0x46];
        if (fread(&flag, 1, 0x46, file) != 0)
        {
            __printf_chk(1, "Well done, the flag is %s\n", &flag);
        }
        fclose(file);
    }
    return res;
}
