if (strlen(&input) <= state_index)
{
    int64_t board = 0x3da8e0915f2c4b67;
    int64_t next_board;
    int64_t i = 0;
    uint64_t move;
    while (true)
    {
        uint64_t c = state[i];
        void* allowed_moves = &allowed_moves;
        int32_t shifter = 0x3c;
        do
        {
            if (c == ((board >> shifter) & 0xf))
            {
                uint64_t* moves = allowed_moves;
                do
                {
                    move = *moves;

                    if (move == 0)
                        break;

                    moves += 1;
                } while (((move * 0xf) & board) != 0);

                if (move != 0)
                    break;
            }
            shifter -= 4;
            allowed_moves += 0x28;
        } while (shifter != 0xfffffffc);

        if (c != ((board >> shifter) & 0xf) || move == 0)
            break;

        int64_t swapper = ((c * move) ^ (c << shifter));
        next_board = (board ^ swapper);
        if (board == swapper)
            break;

        i += 1;

        if (i == 0x36)
            break;

        board = next_board;
    }
    if (next_board == 0x123456789abcdef0)
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
