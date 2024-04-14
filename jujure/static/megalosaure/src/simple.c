#include <stdint.h>
#include <stdio.h>
uint64_t megalosaure(uint32_t m0, uint32_t m1);

int main(int argc, char **argv)
{
    char m0_c[8] = {'F', 'C', 'S', 'C', '{', '0', '0', '0'};
    uint32_t *m0 = (uint32_t *)(m0_c);
    uint32_t *m1 = (uint32_t *)(&m0_c[4]);

    for (int i = 30; i < 127; ++i)
    {
        m0_c[5] = i;
        for (int j = 30; j < 127; ++j)
        {
            m0_c[6] = j;
            for (int k = 30; k < 127; ++k)
            {
                m0_c[7] = k;
                uint64_t res = megalosaure(*m0, *m1);
                if (res == 0x9b07e7ce91a8a7b5)
                {
                    printf("%s\n", m0_c);
                    return 0;
                }
            }
        }
    }
}
