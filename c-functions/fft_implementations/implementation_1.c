#include <stdio.h>
#include <math.h>
#include "implementation_1.h"

// Function prototypes
void fourier(double* data, unsigned long nn);
void swap(double* data1, double* data2);

double intermediate_value;

/*
 * This function substitues the built-in swap() in C++
 */
void swap(double* data1, double* data2)
{
    intermediate_value = *data2;
    *data2 = *data1;
    *data1 = intermediate_value;
}

/*
 * FFT implementation, Cooley-Tukey algorithm from "Numerical
 * Recipes in C++", p.513.
 */
void fourier(double* data, unsigned long nn)
{
    unsigned long n, mmax, m, j, istep, i;
    double wtemp, wr, wpr, wpi, wi, theta;
    double tempr, tempi;

    // reverse-binary reindexing
    n = nn<<1;
    j=1;
    for (i=1; i<n; i+=2)
    {
        if (j>i)
        {
            swap(&data[j-1], &data[i-1]);
            swap(&data[j], &data[i]);
        }
        m = nn;
        while (m>=2 && j>m)
        {
            j -= m;
            m >>= 1;
        }
        j += m;
    };

    // here begins the Danielson-Lanczos section
    mmax=2;
    while (n>mmax)
    {
        istep = mmax<<1;
        theta = -(2*M_PI/mmax);
        wtemp = sin(0.5*theta);
        wpr = -2.0*wtemp*wtemp;
        wpi = sin(theta);
        wr = 1.0;
        wi = 0.0;
        for (m=1; m < mmax; m += 2)
        {
            for (i=m; i <= n; i += istep)
            {
                j=i+mmax;
                tempr = wr*data[j-1] - wi*data[j];
                tempi = wr * data[j] + wi*data[j-1];

                data[j-1] = data[i-1] - tempr;
                data[j] = data[i] - tempi;
                data[i-1] += tempr;
                data[i] += tempi;
            }
            wtemp=wr;
            wr += wr*wpr - wi*wpi;
            wi += wi*wpr + wtemp*wpi;
        }
        mmax=istep;
    }
}
