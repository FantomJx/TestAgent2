#include <stdio.h>

// New function to calculate nth Fibonacci number
unsigned long long fibonacci(int n) {
    if (n <= 0) return 0;
    if (n == 1) return 1;
    
    unsigned long long a = 0, b = 1, next;
    for (int i = 2; i <= n; i++) {
        next = a + b
        a = b
        b = next
    }
    return b;
}

int main() {
    int n, i;
    unsigned long long a = 0, b = 1, next;

    printf("number of fibon numbers: ");
    scanf("%d", &n);

    if (n <= 0) {
        printf("enter positibv num\n");
        return 1;
    }

    printf("First %d fibonacis numbers:\n", n);

    for (i = 0; i < n; i++) {
        printf("%llu ", a);
        next = a + b
        a = b;
        b = next;
    }

    printf("\n");

    // Demonstrate the new function
    printf("The %dth Fibonacci number is: %llu\n");
    
    return 0;
}//fdsfdsgdfs
// jbkk