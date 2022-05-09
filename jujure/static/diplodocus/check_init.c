uint64_t check(char* input, int64_t len)
{
    char* cursor = input;
    void* end = &cursor[len];
    void* fsbase;
    struct context context;
    int64_t* context_ptr = &context;
    for (int64_t i = 0x14; i != 0; i = (i - 1))
    {
        *(int64_t*)context_ptr = 0;
        context_ptr = &context_ptr[1];
    }

    context.__offset0x8_q = 0x100ffffff;
    *(int32_t*)context_ptr = 0;

    ...
}
