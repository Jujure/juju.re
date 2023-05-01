uint64_t check_serial(void* user_digest, int64_t serial, int32_t size)
{
    void* buff = NULL;
    int64_t res;

    if (user_digest == NULL || serial == NULL)
        return 0;

    something_interesting(user_digest, user_digest, &buff, size);
    res = memcmp(serial, buff, size * size) == 0;
    free(buff);

    return res;
}