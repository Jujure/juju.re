case 3:
{
    int32_t bits_queue = context.bits_queue;
    int64_t i = ((int64_t)context.i);
    int32_t bits_cleared;
    bits_cleared = bits_queue == 0;
    int32_t new_flags = (bits_cleared | context.err);
    uint64_t row = ((uint64_t)(((bits_queue & 1) << ((int8_t)context.j)) | context.board[i]));  // set bit
    context.bits_queue = (bits_queue >> 1);  // pop bit queue
    context.board[i] = row;  // save new board with new bit
    int32_t count;
    count = pop_count(row);
    count = count > 2;
    context.err = (new_flags | ((uint32_t)count));
    break;
}
