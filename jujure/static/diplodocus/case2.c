case 2:
{
    enum moves move = context.move; //__offset0xa0
    int32_t j = context.j;
    int32_t i = context.i;
    if (move == 0)
    {
        j = (j + 1);
    }
    else if (move == 1)
    {
        i = (i - 1);
    }
    else if (move == 2)
    {
        j = (j - 1);
    }
    else
    {
        op = op == 3;
        i = (i + ((uint32_t)op));
    }
    int32_t row;
    if ((j <= 0xb && i <= 0xb))
    {
        row = context.visited[i];
    }
    if (((j > 0xb || (j <= 0xb && i > 0xb)) || ((j <= 0xb && i <= 0xb) && (TEST_BITD(row, j)))))
    {
        context.err = (context.err | 1);
    }
    if (((j <= 0xb && i <= 0xb) && (!(TEST_BITD(row, j)))))
    {
        context.i = i;
        context.j = j;
        context.visited[i] = (row | ((int32_t)(1 << j)));  // set bit
    }
    break;
}
