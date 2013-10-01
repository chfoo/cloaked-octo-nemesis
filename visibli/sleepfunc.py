import math

if __name__ == '__main__':
    x = 1.0
    l = []
    s = 1 / 10 * 5.6
    while x < 2 * math.pi:
        y = abs(s * math.sin(x) * math.sin(x ** 2) / x)
        print(y)
        l.append(y)
        x += 0.05

    print('avg', sum(l) / len(l), len(l))
