#include <stdio.h>

int main() {
    int n, i;
    unsigned long long a = 0, b = 1, next;

    printf("Number of Fibonacci numbers: ");
    scanf("%d", &n);

    if (n <= 0) {
        printf("Enter a positive number\n");
        return 1;
    }

    printf("First %d Fibonacci numbers:\n", n);

    for (i = 0; i < n; i++) {
        printf("%llu ", a);
        next = a + b;
        a = b;
        b = next;
    }

    printf("\n");
    return 0;
}