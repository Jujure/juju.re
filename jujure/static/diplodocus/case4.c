case 4:
{
    int32_t j = ((int32_t)cursor[1]);
    int64_t i = ((int64_t)cursor[2]);

    int32_t bits_set;
    bits_set = context.bits_queue != 0;
    context.err = (context.err | bits_set);

    next = &cursor[3];

    int32_t bit = sub_1570(j, i, context);
    context.third_board[i] = (context.third_board[i] | (bit << j));
    break;
}
