case 0:
{
    int32_t count = 0;
    for (int i = 0; i <= 0xb; ++i) // Refactorized SIMD instruction as loop
        count += pop_count(context.visited[i]);

    int32_t err = count != 0x90;
    err = err | context.err;
    context.err = err; // Set error

    int128_t third_board_1 = context.third_board; // Trying to clean up SIMD
    int128_t third_board_2 = *(((uint128_t *)&context.third_board) + 1);
    int128_t third_board_3 = *(((uint128_t *)&context.third_board) + 2);
    int128_t zmm0 = ((third_board_1 & third_board_2) & third_board_3);
    zmm0 = (zmm0 & _mm_bsrli_si128(zmm0, 8)); // More SIMD magic
    zmm0 = (zmm0 & _mm_bsrli_si128(zmm0, 4));

    int32_t all_set = (zmm0 & 0xfff) != 0xfff;// Check that context.third_board
    err = all_set | err;  // Is all set to 1
    context.err = err;

    uint32_t flag = 1; // Set error flag
    if (context.bit_queue == 0) // Check that we emptied the bit queue
    {
        int32_t x = 0;
        for (int i = 0; i <= 0xb; ++i) // SIMD refactor
            x ^= context.board[i];
        flag = x;
    }

    res = ((uint64_t)(err | flag));

    break;
    break;
}
