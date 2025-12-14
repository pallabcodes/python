// cpp_performance.h
// C++ header for performance-critical operations
// 
// This header defines C functions for Python-C++ bindings using ctypes.
// Compile with: g++ -shared -fPIC -o libcpp_performance.so cpp_performance.cpp

#ifndef CPP_PERFORMANCE_H
#define CPP_PERFORMANCE_H

extern "C" {
    // Vector dot product
    // Computes dot product of two vectors of given size
    double dot_product(double* a, double* b, int size);
    
    // Vector normalization (in-place)
    // Normalizes vector to unit length
    void normalize(double* vec, int size);
    
    // Cosine similarity
    // Computes cosine similarity between two vectors
    double cosine_similarity(double* a, double* b, int size);
}

#endif // CPP_PERFORMANCE_H