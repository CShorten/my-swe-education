#include <iostream>
#include <x86intrin.h>

int main() {
    unsigned int ui;
    unsigned long long start = __rdtscp(&ui);

    // Code you want to measure

    unsigned long long end = __rdtscp(&ui);
    unsigned long long elapsed = end - start;

    std::cout << "Elapsed CPU cycles: " << elapsed << "\n";

    return 0;
}
