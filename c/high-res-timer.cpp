#include <iostream>
#include <chrono>

int main() {
    auto start = std::chrono::high_resolution_clock::now();

    auto end = std::chrono::high_resolution_clock::now();
    auto elapsed = end - start;

    std::cout << "Elapsed time: "
              << std::chrono::duration_cast<std::chrono::nanoseconds>(elapsed).count()
              << " ns\n";

    return 0;
}
