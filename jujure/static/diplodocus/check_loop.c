uint64_t check(char* input, int64_t len)
{
    ...

    uint64_t res;
    while (cursor < end)
    {
        char* next = &cursor[1];
        if (*(int8_t*)cursor > 4)
        {
            res = ((uint64_t)(context.err | 1));
            break;
        }
        switch (*(int8_t*)cursor)
        {
            case 0:
            {
                ...
                break;
                break;
            }
            case 1:
            {
                ...
                break;
            }
            case 2:
            {
                ...
                break;
            }
            case 3:
            {
                ...
                break;
            }
            case 4:
            {
                ...
                break;
            }
        }
        cursor = next;
    }
    if ((cursor >= end || (cursor < end && *(int8_t*)cursor <= 4)))
    {
        res = 1;
    }
    return res;
}

