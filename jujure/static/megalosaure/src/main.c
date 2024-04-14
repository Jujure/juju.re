#include <stdint.h>
#include <stdio.h>
#include <unistd.h>
#include <sys/wait.h>
uint64_t megalosaure(uint32_t m0, uint32_t m1);

int block = 1;
int main(int argc, char **argv)
{
    char charset[18] = "0123456789abcdef}";

    const uint64_t ref[9] =  { 0x9b07e7ce91a8a7b5, 0x9e819eac35e7e97c, 0xfd401d3317aa6b5f, 0xdf16a32fbd9d5587, 0x80c561ac0dab4fae, 0x9237d1ddd368e209, 0x07ebe4f6ee26882c, 0xb72ffd11e878303b, 0x99d2a7dc8267bf3f };


    int charset_len = 16;

    int pid = 0;
    for (int i = 0; i < 7; ++i)
    {
        if (pid == 0)
        {
            pid = fork();
            if (pid == 0)
            {
                block++;
            }
        }
    }

    char m0_c[8] = {'0', '0', '0', '0', '0', '0', '0', '0'};
    uint32_t *m0 = (uint32_t *)(&m0_c);
    uint32_t *m1 = (uint32_t *)(&m0_c[4]);
    uint64_t res;
    uint64_t x_int = ref[block - 1];
    char *x = (char*)&x_int;

    if (block == 8)
    {
        charset_len += 2;
    }

    for (int i0 = 0; i0 < 18; ++i0)
    {
        m0_c[0] = charset[i0] ^ x[0];
        for (int i1 = 0; i1 < charset_len; ++i1)
        {
            m0_c[1] = charset[i1] ^ x[1];
            for (int i2 = 0; i2 < charset_len; ++i2)
            {
                m0_c[2] = charset[i2] ^ x[2];
                for (int i3 = 0; i3 < charset_len; ++i3)
                {
                    m0_c[3] = charset[i3] ^ x[3];
                    for (int i4 = 0; i4 < charset_len; ++i4)
                    {
                        m0_c[4] = charset[i4] ^ x[4];
                        for (int i5 = 0; i5 < charset_len; ++i5)
                        {
                            m0_c[5] = charset[i5] ^ x[5];
                            for (int i6 = 0; i6 < charset_len; ++i6)
                            {
                                m0_c[6] = charset[i6] ^ x[6];
                                for (int i7 = 0; i7 < charset_len; ++i7)
                                {
                                    m0_c[7] = charset[i7] ^ x[7];
                                    res = megalosaure(*m0, *m1);
                                    if (res ==  ref[block])
                                    {
                                        char flag[9];
                                        flag[8] = 0;
                                        uint64_t *flag_ptr = (uint64_t*)flag;
                                        *flag_ptr = *m0 + (((uint64_t)*m1) << 32);
                                        *flag_ptr ^= x_int;
                                        printf("Block %d: %s\n", block, flag);
                                        if (pid != 0)
                                            waitpid(pid, NULL, 0);
                                        return 0;
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }

}
