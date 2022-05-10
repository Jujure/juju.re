int64_t encrypt_block(char* block, int64_t len)
{
    int64_t i;
    for (i = 0; i < len; i = (i + 1))
    {
        block[((len - i) - 1)] = (block[((len - i) - 1)] ^ block[((len - i) - 2)]);
    }
    return i;
}
