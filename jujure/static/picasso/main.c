char init_state[0x36] = 
{
	0x0d, 0x03, 0x02, 0x0e, 0x0f, 0x09, 0x07, 0x0e, 0x0d, 0x06, 0x03, 0x02, 0x07, 0x02, 0x08, 0x0e,
	0x07, 0x04, 0x04, 0x03, 0x0d, 0x04, 0x0c, 0x03, 0x0f, 0x02, 0x0a, 0x05, 0x09, 0x01, 0x06, 0x0a,
	0x0b, 0x02, 0x05, 0x0c, 0x0e, 0x0b, 0x0d, 0x01, 0x0a, 0x01, 0x05, 0x09, 0x01, 0x0f, 0x06, 0x0e,
	0x04, 0x04, 0x0b, 0x04, 0x0b, 0x0f, 0x00
};


int32_t main(int32_t argc, char** argv, char** envp)
{
    char* const init_state_ptr = &init_state;
    char state[0x36];
    char* state_ptr = &state;
    for (int64_t size = 0x36; size != 0; size -= 1)
    {
        *state_ptr = *init_state_ptr;
        state_ptr += 1;
        init_state_ptr += 1;
    }

    printf("Password: ", init_state_ptr);
    fflush(stdout);

    char input[0x18];
    scanf("%24s", &input);

    int64_t state_index = 0;

    while (true)
    {
        if (strlen(&input) <= state_index)
        {
            // Cutting everything that happens
            ...
            if (check == OK)
            {
                puts("Win!");
                FILE file = fopen("flag.txt", &rb);
                if (file != NULL)
                {
                    char flag[0x46];
                    fread(&flag, 1, 0x46, file);
                    fclose(file);
                    puts(flag);
                    return 0;
                }
                else
                    puts("Send your input on the remote se…");
            }
            else
                puts("Nope!");
            break;
        }
        else
        {
            char* pos_ptr = strchr("abcdefghjklmnpqrstuvwxyz", input[state_index]);
            if (pos_ptr != NULL)
            {
                // Do stuff iterating on the state
                ...
                state_index += 1;
                continue;
            }
        }
        puts("Nope!");
        break;
    }
    exit(1);
    /* no return */
}
