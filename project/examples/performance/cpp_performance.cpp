// cpp_performance.cpp
// C++ implementation for performance-critical operations
//
// Compilation:
//   Linux: g++ -shared -fPIC -o libcpp_performance.so cpp_performance.cpp
//   macOS: g++ -shared -fPIC -o libcpp_performance.dylib cpp_performance.cpp
//   Windows: g++ -shared -o cpp_performance.dll cpp_performance.cpp

#include <cmath>
#include "cpp_performance.h"

extern "C" {
    double dot_product(double* a, double* b, int size) {
        double result = 0.0;
        for (int i = 0; i < size; ++i) {
            result += a[i] * b[i];
        }
        return result;
    }
    
    void normalize(double* vec, int size) {
        double magnitude = 0.0;
        for (int i = 0; i < size; ++i) {
            magnitude += vec[i] * vec[i];
        }
        magnitude = std::sqrt(magnitude);
        if (magnitude > 0.0) {
            for (int i = 0; i < size; ++i) {
                vec[i] /= magnitude;
            }
        }
    }
    
    double cosine_similarity(double* a, double* b, int size) {
        double dot = 0.0;
        double norm_a = 0.0;
        double norm_b = 0.0;
        
        for (int i = 0; i < size; ++i) {
            dot += a[i] * b[i];
            norm_a += a[i] * a[i];
            norm_b += b[i] * b[i];
        }
        
        norm_a = std::sqrt(norm_a);
        norm_b = std::sqrt(norm_b);
        
        if (norm_a == 0.0 || norm_b == 0.0) {
            return 0.0;
        }
        
        return dot / (norm_a * norm_b);
    }
}