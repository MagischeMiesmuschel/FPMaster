import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import curve_fit
from uncertainties import ufloat
from uncertainties import unumpy as unp
from uncertainties.unumpy import exp
from scipy import constants
from scipy.integrate import quad, trapz

# to run code 6

I1, T1 = np.genfromtxt("data/temp1.txt", unpack=True)
I2, T2 = np.genfromtxt("data/temp2.txt", unpack=True)

T1 = constants.convert_temperature(T1, 'Celsius', 'Kelvin')
T2 = constants.convert_temperature(T2, 'Celsius', 'Kelvin')

Ws = {'integrated': {}, 'approx': {}}

def linear_fit(T, A, B):
    return A*T + B


def exp_fit(T, A, B, T0, I0):
    return A * np.exp(B * (T - T0)) + I0


# this loop runs twice for T1/j1 and a second time for T2/j2
for T, I, selection, offset_selection, p0, name, ff in [
        [
            T1,
            I1,
            ((T1 > 230) & (T1 < 236) | (T1 > 280)),
            (T1 > 230) & (T1 < 290),
            None,
            'set1',
            linear_fit,
        ],
        [
            T2,
            I2,
            ((T2 > 230) & (T2 < 240) | (T2 > 285)),
            (T2 > 230) & (T2 < 290),
            None,
            'set2',
            linear_fit,
        ]]:

    # I_cleaned will be coorected by Offset
    var, cov = curve_fit(ff, T[selection],I[selection], p0=p0)
    errs = np.sqrt(np.diag(cov))
    I_cleaned = I - ff(T, *var)
    I_min = np.min(I_cleaned[offset_selection])
    I_cleaned -= I_min

    print(var[0], errs[0])
    print(var[1], errs[1])

    xs = np.linspace(220, 320)

    plt.plot(T[selection],I[selection], 'b.', label='verwendete Daten')
    plt.plot(T[~selection],I[~selection], 'g.', label='ignorierte Daten')
    plt.plot(xs, ff(xs, *var), label='fit')
    plt.plot(T, I_cleaned + I_min, 'r.', label='bereinigte Daten')
    plt.plot(xs, [I_min] * len(xs), label='Offset') # Liste mit Eintrag I_min, Anzahl len(xs)
    plt.xlim(220, 320)
    if name == 'set1':
        plt.ylim(-1.5, 15)
        I1_cleaned = I_cleaned
    else:
        plt.ylim(-3, 21)
        I2_cleaned = I_cleaned
    plt.xlabel(r'$T$ / K')
    plt.ylabel(r'$i$ / pA')
    plt.grid()
    plt.legend(loc='best')
    if name == 'set1':
        plt.savefig('build/plot1.pdf')
    else:
        plt.savefig('build/plot2.pdf')
    plt.clf()

print("#############################")

def j_aprox(T, C, W):
    return W*T + C

# Fit and plot for each dataset
for T, I, selection1, selection2, name in [
        [
            T1,
            I1_cleaned,
            (T1 > 236) & (T1 < 255),
            (T1 > 228) & (T1 < 262),
            'set1',
        ],
        [
            T2,
            I2_cleaned,
            (T2 > 236) & (T2 < 255),
            (T2 > 228) & (T2 < 262),
            'set2',
        ]]:
    print(name)

    T_sel1 = 1/T[selection1]
    I_sel1 = np.log(I[selection1]*1e-12)
    T_sel2 = 1/T[selection2]
    I_sel2 = np.log(I[selection2]*1e-12)

    val, cov = curve_fit( j_aprox,T_sel1, I_sel1, maxfev=2000)
    errs = np.sqrt(np.diag(cov))
    W = ufloat(val[1], errs[1])*constants.k / constants.eV
    print("W:", W)
    print("C:", val[0], errs[0])
    Ws['approx'][name] = W

    xs = np.linspace(0.0037, 0.0045, 100)
    #plt.ylim(-2, 5)
    plt.xlim(0.0038, 0.0044)
    plt.grid()
    plt.plot(xs, j_aprox(xs, C=val[0], W=val[1]), 'r-', label='Fit')
    plt.plot(T_sel2, I_sel2, 'b.', label='bereinigte Daten\n(nicht verwendet)')
    plt.plot(T_sel1, I_sel1, 'g.', label='bereinigte Daten\n(für Fit verwendet)')
    plt.xlabel(r'$T^{-1}$ / $\text{K}^{-1}$')
    plt.ylabel(r'$\ln(i)$ / pA')
    plt.legend(loc='best')
    if name == 'set1':
        plt.savefig('build/plot3.pdf')
    else:
        plt.savefig('build/plot4.pdf')
    plt.clf()


print("######################################")

def better_fit(T, i_T, Tstar):
    integral = np.array(
        [trapz(i_T[(T > t) & (T < Tstar)], T[(T > t) & (T < Tstar)])
         for t in T]
    )
    #print(integral)
    #print(i_T)
    return np.log(integral / i_T)

def nearest_toZero(array1,array2):
    idx = np.abs(array2).argmin()
    return array1[idx]

for T, I, selection, selection2, name in [
        [
            T1,
            I1_cleaned,
            (T1 > 240) & (T1 < 265),
            (T1 > 235) & (T1 < 275),
            'set1',
        ],
        [
            T2,
            I2_cleaned,
            (T2 > 240) & (T2 < 276),
            (T2 > 235) & (T2 < 280),
            'set2',
        ]]:
    print(name)
    Tstar = nearest_toZero(T[(T > 260) & (T < 300)], I[(T > 260) & (T < 300)])

    T_ignored = T[selection2]
    I_ignored = I[selection2]
    T = T[selection]
    I = I[selection]
    #print(T)
    #print(T < Tstar)
    print("Tstar:", Tstar)

    logstuff = better_fit(T, I, Tstar)
    T = T[np.isfinite(logstuff)]
    logstuff = logstuff[np.isfinite(logstuff)]

    logstuff_ignored = better_fit(T_ignored, I_ignored, Tstar)
    T_ignored = T_ignored[np.isfinite(logstuff_ignored)]
    logstuff_ignored = logstuff_ignored[np.isfinite(logstuff_ignored)]
    #print(T, logstuff)

    var, cov = curve_fit(linear_fit, 1 / T, logstuff)
    errs = np.sqrt(np.diag(cov))
    W = ufloat(var[0], errs[0])* constants.k / constants.eV
    print("W:", W)
    print("C:", var[1], errs[1])
    Ws['integrated'][name] = W

    xs = np.linspace(0.0035, 0.0043, 100)
    #plt.ylim(-2, 5)
    if name == "set1":
        plt.xlim(0.00375, 0.0042)
    else:
        plt.xlim(0.0036, 0.0042)
    plt.grid()
    plt.plot(xs, linear_fit(xs, A=var[0], B=var[1]), 'r-', label='Fit')
    #plt.plot(1/T_ignored, logstuff_ignored, 'b.', label='bereinigte Daten\n(nicht verwendet)')
    plt.plot(1/T, logstuff, 'g.', label='bereinigte Daten \n(für Fit verwendet)')
    plt.xlabel(r'$T^{-1}$ / $\text{K}^{-1}$')
    plt.ylabel(r'$\ln\left(\int_{T}^{T*} i(T) \mathrm{d}\,T \:/\: i(T) \cdot b \right)$')
    plt.legend(loc='best')
    if name == 'set1':
        plt.savefig('build/plot5.pdf')
    else:
        plt.savefig('build/plot6.pdf')
    plt.clf()


print("##############################")


def tau(W, T, h):
    T *= constants.k
    return (T**2)/(constants.k*W*h)* unp.exp(-W/T)

def find_maxT(array1,array2):
    idx = array2.argmax()
    return array1[idx]



for T, I, name in [[T1, I1, "set1"], [T2, I2, "set2"]]:

    time = np.linspace(0,0.5*(len(T)-1), len(T))
    steigung = []
    new_time = []
    i = 0

    while i < len(T)-1:
        steigung = np.append(steigung, (T[i+1]-T[i])/(time[i+1]-time[i]))
        new_time = np.append(new_time, (time[i+1]+time[i])/2)
        i += 1

    Tmax = find_maxT(T, I)

    steigung_plot = steigung
    steigung = ufloat(np.mean(steigung), np.std(steigung))

    print(name)
    print("Tmax: ", Tmax)
    print("Steigung: ", steigung.n, steigung.s)
    print("Tau approx:", tau(-Ws['approx'][name]*constants.eV, Tmax, steigung), -Ws['approx'][name])
    print("Tau integrated:", tau(Ws['integrated'][name]*constants.eV, Tmax, steigung), Ws['integrated'][name])
    plt.plot(new_time, steigung_plot)


plt.savefig('build/plot7.pdf')

#
