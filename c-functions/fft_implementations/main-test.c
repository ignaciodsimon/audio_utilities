#include <stdio.h>
#include <math.h>
#include "implementation_1.h"

#define SEQUENCE_LENGTH 1024 // Must be a power of 2
 
// Global variables
double input_data[SEQUENCE_LENGTH];//, ir[1000];

// Main function
int main(void)
{
    int i;

    // Fill input vector with a 1kHz sine signal
    for(i=0; i<SEQUENCE_LENGTH; i = i+2)
        input_data[i] = sin(2.0 * M_PI * (float)(1000.0/48000.0) * (float)i/2.0);

    printf("Input data: \n");
    for(i=0; i<SEQUENCE_LENGTH; i = i+2)
        printf("%.5f+1i*%.5f ", input_data[i], input_data[i+1]);

    printf("\n > Computing FFT ...\n");
    fourier(input_data, SEQUENCE_LENGTH/2);

    printf(" > Results:\n");
    for(i=0; i<SEQUENCE_LENGTH; i = i+2)
        printf("%.5f+1i*%.5f ", input_data[i], input_data[i+1]);

    printf("\n");
    return 0;
}

