import numpy as np

def spline_curvature(f, x):

    return f.derivative(2)(x) / ((1 + np.square(f.derivative(1)(x)))**(1.5))


def curvature(y):
    y_prime = y[1:] - y[:-1]
    y_pp = y_prime[1:] - y_prime[:-1]

    return y_pp / ((1 + np.square(y_prime[:-1]))**(1.5))