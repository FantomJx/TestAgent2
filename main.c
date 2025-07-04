#include <stdio.h>

int main() {
    int n, i;
    unsigned long long a = 0, b = 1, next;
12rtre
    printf("number of on numbers: ");
    scanf("%d", &n)
// ewqewqewq
    if (n <= 0) {
        printf("eqwsdanter positibv num\n");
        return 1;
    }
    // jbkk
    printf("First jjfibonacis numbers:\n", n);

    for (i = 0; i < n; i++) {
        printf("%llu ", a);
        next = a + b;
        a = b;
        b = next;
    }

    printf("\n");
    return 0;
}
// jbkk