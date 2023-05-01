uint64_t dot_product(char* A, char* B, char** out, int32_t size)
{
    if (A == NULL || B == NULL)
    {
        return 0;
    }
    int32_t res = 1;
    int64_t i = 0;
    int32_t j = 0;

    *out = calloc(size * size, 1);

    while (size > j)
    {
        int64_t k = 0;
        char* A_line = A + i;
        do
        {
            char* B_col = B + k;
            int64_t col = 0;
            int32_t sum = 0;

            do
            {
                char element;
                element = A_line[col];
                element *= B_col[0];
                col += 1;
                B_col += size;
                sum += element;
            } while (size > col);

            ((*out) + i)[k] = sum; // ith line, kth column

            bool win;
            if (j != k) // Check if on the diagonal
                win = sum == 0; // if not check that it is 0
            else
                win = sum == 1; // if yes check it is 1

            k += 1;
            res &= win; // Bitwise and, every number must be correct
        } while (size > k);

        j += 1;
        i += size;
    }
    return res;
}
