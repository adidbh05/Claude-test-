"""
European Steel Section Properties Database.
Contains full geometric and structural properties for standard sections
per EN 10365 and EN 10210/10219.
"""
import math
from typing import Optional, List, Dict, Any


# ============== Section Property Data ==============

# IPE Sections (European I-beams) — Full property set
IPE_SECTIONS = {
    "IPE 80": {
        "h": 80, "b": 46, "tw": 3.8, "tf": 5.2, "r": 5.0,
        "A": 764, "Iy": 80.1e4, "Iz": 8.49e4, "It": 0.70e4, "Iw": 0.118e9,
        "Wpl_y": 23.2e3, "Wpl_z": 5.82e3, "Wel_y": 20.0e3, "Wel_z": 3.69e3,
        "iy": 32.4, "iz": 10.5, "mass": 6.0,
    },
    "IPE 100": {
        "h": 100, "b": 55, "tw": 4.1, "tf": 5.7, "r": 7.0,
        "A": 1030, "Iy": 171e4, "Iz": 15.9e4, "It": 1.20e4, "Iw": 0.351e9,
        "Wpl_y": 39.4e3, "Wpl_z": 9.15e3, "Wel_y": 34.2e3, "Wel_z": 5.79e3,
        "iy": 40.7, "iz": 12.4, "mass": 8.1,
    },
    "IPE 120": {
        "h": 120, "b": 64, "tw": 4.4, "tf": 6.3, "r": 7.0,
        "A": 1320, "Iy": 318e4, "Iz": 27.7e4, "It": 1.74e4, "Iw": 0.890e9,
        "Wpl_y": 60.7e3, "Wpl_z": 13.6e3, "Wel_y": 53.0e3, "Wel_z": 8.65e3,
        "iy": 49.0, "iz": 14.5, "mass": 10.4,
    },
    "IPE 140": {
        "h": 140, "b": 73, "tw": 4.7, "tf": 6.9, "r": 7.0,
        "A": 1640, "Iy": 541e4, "Iz": 44.9e4, "It": 2.45e4, "Iw": 1.98e9,
        "Wpl_y": 88.3e3, "Wpl_z": 19.3e3, "Wel_y": 77.3e3, "Wel_z": 12.3e3,
        "iy": 57.4, "iz": 16.5, "mass": 12.9,
    },
    "IPE 160": {
        "h": 160, "b": 82, "tw": 5.0, "tf": 7.4, "r": 9.0,
        "A": 2010, "Iy": 869e4, "Iz": 68.3e4, "It": 3.60e4, "Iw": 3.96e9,
        "Wpl_y": 124e3, "Wpl_z": 26.1e3, "Wel_y": 109e3, "Wel_z": 16.7e3,
        "iy": 65.8, "iz": 18.4, "mass": 15.8,
    },
    "IPE 180": {
        "h": 180, "b": 91, "tw": 5.3, "tf": 8.0, "r": 9.0,
        "A": 2390, "Iy": 1320e4, "Iz": 101e4, "It": 4.79e4, "Iw": 7.43e9,
        "Wpl_y": 166e3, "Wpl_z": 34.6e3, "Wel_y": 146e3, "Wel_z": 22.2e3,
        "iy": 74.2, "iz": 20.5, "mass": 18.8,
    },
    "IPE 200": {
        "h": 200, "b": 100, "tw": 5.6, "tf": 8.5, "r": 12.0,
        "A": 2850, "Iy": 1940e4, "Iz": 142e4, "It": 6.98e4, "Iw": 12.99e9,
        "Wpl_y": 221e3, "Wpl_z": 44.6e3, "Wel_y": 194e3, "Wel_z": 28.5e3,
        "iy": 82.6, "iz": 22.4, "mass": 22.4,
    },
    "IPE 220": {
        "h": 220, "b": 110, "tw": 5.9, "tf": 9.2, "r": 12.0,
        "A": 3340, "Iy": 2770e4, "Iz": 205e4, "It": 9.07e4, "Iw": 22.67e9,
        "Wpl_y": 285e3, "Wpl_z": 58.1e3, "Wel_y": 252e3, "Wel_z": 37.3e3,
        "iy": 91.1, "iz": 24.8, "mass": 26.2,
    },
    "IPE 240": {
        "h": 240, "b": 120, "tw": 6.2, "tf": 9.8, "r": 15.0,
        "A": 3910, "Iy": 3890e4, "Iz": 284e4, "It": 12.9e4, "Iw": 37.39e9,
        "Wpl_y": 367e3, "Wpl_z": 73.9e3, "Wel_y": 324e3, "Wel_z": 47.3e3,
        "iy": 99.7, "iz": 26.9, "mass": 30.7,
    },
    "IPE 270": {
        "h": 270, "b": 135, "tw": 6.6, "tf": 10.2, "r": 15.0,
        "A": 4590, "Iy": 5790e4, "Iz": 420e4, "It": 15.9e4, "Iw": 70.58e9,
        "Wpl_y": 484e3, "Wpl_z": 97.0e3, "Wel_y": 429e3, "Wel_z": 62.2e3,
        "iy": 112, "iz": 30.2, "mass": 36.1,
    },
    "IPE 300": {
        "h": 300, "b": 150, "tw": 7.1, "tf": 10.7, "r": 15.0,
        "A": 5380, "Iy": 8360e4, "Iz": 604e4, "It": 20.1e4, "Iw": 126e9,
        "Wpl_y": 628e3, "Wpl_z": 125e3, "Wel_y": 557e3, "Wel_z": 80.5e3,
        "iy": 125, "iz": 33.5, "mass": 42.2,
    },
    "IPE 330": {
        "h": 330, "b": 160, "tw": 7.5, "tf": 11.5, "r": 18.0,
        "A": 6260, "Iy": 11770e4, "Iz": 788e4, "It": 28.1e4, "Iw": 199e9,
        "Wpl_y": 804e3, "Wpl_z": 153e3, "Wel_y": 713e3, "Wel_z": 98.5e3,
        "iy": 137, "iz": 35.5, "mass": 49.1,
    },
    "IPE 360": {
        "h": 360, "b": 170, "tw": 8.0, "tf": 12.7, "r": 18.0,
        "A": 7270, "Iy": 16270e4, "Iz": 1040e4, "It": 37.3e4, "Iw": 314e9,
        "Wpl_y": 1019e3, "Wpl_z": 191e3, "Wel_y": 904e3, "Wel_z": 122.8e3,
        "iy": 150, "iz": 37.9, "mass": 57.1,
    },
    "IPE 400": {
        "h": 400, "b": 180, "tw": 8.6, "tf": 13.5, "r": 21.0,
        "A": 8450, "Iy": 23130e4, "Iz": 1318e4, "It": 51.1e4, "Iw": 490e9,
        "Wpl_y": 1307e3, "Wpl_z": 229e3, "Wel_y": 1156e3, "Wel_z": 146e3,
        "iy": 165, "iz": 39.5, "mass": 66.3,
    },
    "IPE 450": {
        "h": 450, "b": 190, "tw": 9.4, "tf": 14.6, "r": 21.0,
        "A": 9880, "Iy": 33740e4, "Iz": 1676e4, "It": 66.9e4, "Iw": 791e9,
        "Wpl_y": 1702e3, "Wpl_z": 276e3, "Wel_y": 1500e3, "Wel_z": 176e3,
        "iy": 185, "iz": 41.2, "mass": 77.6,
    },
    "IPE 500": {
        "h": 500, "b": 200, "tw": 10.2, "tf": 16.0, "r": 21.0,
        "A": 11600, "Iy": 48200e4, "Iz": 2142e4, "It": 89.3e4, "Iw": 1249e9,
        "Wpl_y": 2194e3, "Wpl_z": 336e3, "Wel_y": 1928e3, "Wel_z": 214e3,
        "iy": 204, "iz": 43.1, "mass": 90.7,
    },
    "IPE 550": {
        "h": 550, "b": 210, "tw": 11.1, "tf": 17.2, "r": 24.0,
        "A": 13440, "Iy": 67120e4, "Iz": 2668e4, "It": 123e4, "Iw": 1884e9,
        "Wpl_y": 2787e3, "Wpl_z": 401e3, "Wel_y": 2441e3, "Wel_z": 254e3,
        "iy": 223, "iz": 44.5, "mass": 106,
    },
    "IPE 600": {
        "h": 600, "b": 220, "tw": 12.0, "tf": 19.0, "r": 24.0,
        "A": 15600, "Iy": 92080e4, "Iz": 3387e4, "It": 165e4, "Iw": 2846e9,
        "Wpl_y": 3512e3, "Wpl_z": 486e3, "Wel_y": 3069e3, "Wel_z": 308e3,
        "iy": 243, "iz": 46.6, "mass": 122,
    },
}

# HEB Sections (European wide-flange beams)
HEB_SECTIONS = {
    "HEB 100": {
        "h": 100, "b": 100, "tw": 6.0, "tf": 10.0, "r": 12.0,
        "A": 2600, "Iy": 450e4, "Iz": 167e4, "It": 9.25e4, "Iw": 3.38e9,
        "Wpl_y": 104e3, "Wpl_z": 51.4e3, "Wel_y": 89.9e3, "Wel_z": 33.5e3,
        "iy": 41.6, "iz": 25.3, "mass": 20.4,
    },
    "HEB 120": {
        "h": 120, "b": 120, "tw": 6.5, "tf": 11.0, "r": 12.0,
        "A": 3400, "Iy": 864e4, "Iz": 318e4, "It": 13.8e4, "Iw": 9.41e9,
        "Wpl_y": 165e3, "Wpl_z": 80.9e3, "Wel_y": 144e3, "Wel_z": 52.9e3,
        "iy": 50.4, "iz": 30.6, "mass": 26.7,
    },
    "HEB 140": {
        "h": 140, "b": 140, "tw": 7.0, "tf": 12.0, "r": 12.0,
        "A": 4300, "Iy": 1510e4, "Iz": 550e4, "It": 20.1e4, "Iw": 22.48e9,
        "Wpl_y": 246e3, "Wpl_z": 119e3, "Wel_y": 216e3, "Wel_z": 78.5e3,
        "iy": 59.3, "iz": 35.7, "mass": 33.7,
    },
    "HEB 160": {
        "h": 160, "b": 160, "tw": 8.0, "tf": 13.0, "r": 15.0,
        "A": 5430, "Iy": 2490e4, "Iz": 889e4, "It": 31.2e4, "Iw": 47.94e9,
        "Wpl_y": 354e3, "Wpl_z": 170e3, "Wel_y": 311e3, "Wel_z": 111e3,
        "iy": 67.8, "iz": 40.5, "mass": 42.6,
    },
    "HEB 180": {
        "h": 180, "b": 180, "tw": 8.5, "tf": 14.0, "r": 15.0,
        "A": 6530, "Iy": 3830e4, "Iz": 1360e4, "It": 42.2e4, "Iw": 93.75e9,
        "Wpl_y": 481e3, "Wpl_z": 231e3, "Wel_y": 426e3, "Wel_z": 151e3,
        "iy": 76.6, "iz": 45.7, "mass": 51.2,
    },
    "HEB 200": {
        "h": 200, "b": 200, "tw": 9.0, "tf": 15.0, "r": 18.0,
        "A": 7810, "Iy": 5700e4, "Iz": 2000e4, "It": 59.3e4, "Iw": 171e9,
        "Wpl_y": 642e3, "Wpl_z": 305e3, "Wel_y": 570e3, "Wel_z": 200e3,
        "iy": 85.6, "iz": 50.7, "mass": 61.3,
    },
    "HEB 220": {
        "h": 220, "b": 220, "tw": 9.5, "tf": 16.0, "r": 18.0,
        "A": 9100, "Iy": 8090e4, "Iz": 2840e4, "It": 76.6e4, "Iw": 295e9,
        "Wpl_y": 827e3, "Wpl_z": 393e3, "Wel_y": 736e3, "Wel_z": 258e3,
        "iy": 94.3, "iz": 55.9, "mass": 71.5,
    },
    "HEB 240": {
        "h": 240, "b": 240, "tw": 10.0, "tf": 17.0, "r": 21.0,
        "A": 10600, "Iy": 11260e4, "Iz": 3920e4, "It": 103e4, "Iw": 487e9,
        "Wpl_y": 1053e3, "Wpl_z": 498e3, "Wel_y": 938e3, "Wel_z": 327e3,
        "iy": 103, "iz": 60.8, "mass": 83.2,
    },
    "HEB 260": {
        "h": 260, "b": 260, "tw": 10.0, "tf": 17.5, "r": 24.0,
        "A": 11800, "Iy": 14920e4, "Iz": 5135e4, "It": 124e4, "Iw": 753e9,
        "Wpl_y": 1283e3, "Wpl_z": 602e3, "Wel_y": 1148e3, "Wel_z": 395e3,
        "iy": 112, "iz": 66.0, "mass": 93.0,
    },
    "HEB 280": {
        "h": 280, "b": 280, "tw": 10.5, "tf": 18.0, "r": 24.0,
        "A": 13100, "Iy": 19270e4, "Iz": 6595e4, "It": 144e4, "Iw": 1130e9,
        "Wpl_y": 1534e3, "Wpl_z": 718e3, "Wel_y": 1376e3, "Wel_z": 471e3,
        "iy": 121, "iz": 71.0, "mass": 103,
    },
    "HEB 300": {
        "h": 300, "b": 300, "tw": 11.0, "tf": 19.0, "r": 27.0,
        "A": 14900, "Iy": 25170e4, "Iz": 8563e4, "It": 185e4, "Iw": 1688e9,
        "Wpl_y": 1869e3, "Wpl_z": 870e3, "Wel_y": 1678e3, "Wel_z": 571e3,
        "iy": 130, "iz": 75.8, "mass": 117,
    },
    "HEB 320": {
        "h": 320, "b": 300, "tw": 11.5, "tf": 20.5, "r": 27.0,
        "A": 16100, "Iy": 30820e4, "Iz": 9239e4, "It": 225e4, "Iw": 2069e9,
        "Wpl_y": 2149e3, "Wpl_z": 939e3, "Wel_y": 1926e3, "Wel_z": 616e3,
        "iy": 138, "iz": 75.8, "mass": 127,
    },
    "HEB 340": {
        "h": 340, "b": 300, "tw": 12.0, "tf": 21.5, "r": 27.0,
        "A": 17100, "Iy": 36660e4, "Iz": 9690e4, "It": 257e4, "Iw": 2454e9,
        "Wpl_y": 2408e3, "Wpl_z": 986e3, "Wel_y": 2156e3, "Wel_z": 646e3,
        "iy": 146, "iz": 75.3, "mass": 134,
    },
    "HEB 360": {
        "h": 360, "b": 300, "tw": 12.5, "tf": 22.5, "r": 27.0,
        "A": 18100, "Iy": 43190e4, "Iz": 10140e4, "It": 293e4, "Iw": 2883e9,
        "Wpl_y": 2683e3, "Wpl_z": 1032e3, "Wel_y": 2400e3, "Wel_z": 676e3,
        "iy": 154, "iz": 74.9, "mass": 142,
    },
    "HEB 400": {
        "h": 400, "b": 300, "tw": 13.5, "tf": 24.0, "r": 27.0,
        "A": 19800, "Iy": 57680e4, "Iz": 10820e4, "It": 356e4, "Iw": 3817e9,
        "Wpl_y": 3232e3, "Wpl_z": 1104e3, "Wel_y": 2884e3, "Wel_z": 721e3,
        "iy": 171, "iz": 73.9, "mass": 155,
    },
    "HEB 450": {
        "h": 450, "b": 300, "tw": 14.0, "tf": 26.0, "r": 27.0,
        "A": 21800, "Iy": 79890e4, "Iz": 11720e4, "It": 440e4, "Iw": 5258e9,
        "Wpl_y": 3982e3, "Wpl_z": 1198e3, "Wel_y": 3551e3, "Wel_z": 781e3,
        "iy": 192, "iz": 73.3, "mass": 171,
    },
    "HEB 500": {
        "h": 500, "b": 300, "tw": 14.5, "tf": 28.0, "r": 27.0,
        "A": 23900, "Iy": 107200e4, "Iz": 12620e4, "It": 538e4, "Iw": 7018e9,
        "Wpl_y": 4815e3, "Wpl_z": 1292e3, "Wel_y": 4287e3, "Wel_z": 842e3,
        "iy": 212, "iz": 72.7, "mass": 187,
    },
}

# HEA Sections (European wide-flange beams - light series)
HEA_SECTIONS = {
    "HEA 100": {
        "h": 96, "b": 100, "tw": 5.0, "tf": 8.0, "r": 12.0,
        "A": 2120, "Iy": 349e4, "Iz": 134e4, "It": 5.24e4, "Iw": 2.33e9,
        "Wpl_y": 83.0e3, "Wpl_z": 41.1e3, "Wel_y": 72.8e3, "Wel_z": 26.8e3,
        "iy": 40.6, "iz": 25.2, "mass": 16.7,
    },
    "HEA 120": {
        "h": 114, "b": 120, "tw": 5.0, "tf": 8.0, "r": 12.0,
        "A": 2530, "Iy": 606e4, "Iz": 231e4, "It": 5.99e4, "Iw": 6.47e9,
        "Wpl_y": 119e3, "Wpl_z": 58.8e3, "Wel_y": 106e3, "Wel_z": 38.5e3,
        "iy": 49.0, "iz": 30.2, "mass": 19.9,
    },
    "HEA 140": {
        "h": 133, "b": 140, "tw": 5.5, "tf": 8.5, "r": 12.0,
        "A": 3140, "Iy": 1030e4, "Iz": 389e4, "It": 8.13e4, "Iw": 15.06e9,
        "Wpl_y": 173e3, "Wpl_z": 84.9e3, "Wel_y": 155e3, "Wel_z": 55.6e3,
        "iy": 57.3, "iz": 35.2, "mass": 24.7,
    },
    "HEA 160": {
        "h": 152, "b": 160, "tw": 6.0, "tf": 9.0, "r": 15.0,
        "A": 3880, "Iy": 1670e4, "Iz": 616e4, "It": 12.2e4, "Iw": 31.41e9,
        "Wpl_y": 245e3, "Wpl_z": 117e3, "Wel_y": 220e3, "Wel_z": 77.0e3,
        "iy": 65.7, "iz": 39.8, "mass": 30.4,
    },
    "HEA 180": {
        "h": 171, "b": 180, "tw": 6.0, "tf": 9.5, "r": 15.0,
        "A": 4530, "Iy": 2510e4, "Iz": 925e4, "It": 14.8e4, "Iw": 60.19e9,
        "Wpl_y": 325e3, "Wpl_z": 156e3, "Wel_y": 294e3, "Wel_z": 103e3,
        "iy": 74.5, "iz": 45.2, "mass": 35.5,
    },
    "HEA 200": {
        "h": 190, "b": 200, "tw": 6.5, "tf": 10.0, "r": 18.0,
        "A": 5380, "Iy": 3690e4, "Iz": 1340e4, "It": 20.9e4, "Iw": 108e9,
        "Wpl_y": 429e3, "Wpl_z": 204e3, "Wel_y": 389e3, "Wel_z": 134e3,
        "iy": 82.8, "iz": 49.8, "mass": 42.3,
    },
    "HEA 220": {
        "h": 210, "b": 220, "tw": 7.0, "tf": 11.0, "r": 18.0,
        "A": 6430, "Iy": 5410e4, "Iz": 1955e4, "It": 28.5e4, "Iw": 193e9,
        "Wpl_y": 568e3, "Wpl_z": 271e3, "Wel_y": 515e3, "Wel_z": 178e3,
        "iy": 91.7, "iz": 55.1, "mass": 50.5,
    },
    "HEA 240": {
        "h": 230, "b": 240, "tw": 7.5, "tf": 12.0, "r": 21.0,
        "A": 7680, "Iy": 7760e4, "Iz": 2770e4, "It": 41.5e4, "Iw": 329e9,
        "Wpl_y": 745e3, "Wpl_z": 352e3, "Wel_y": 675e3, "Wel_z": 231e3,
        "iy": 101, "iz": 60.1, "mass": 60.3,
    },
    "HEA 260": {
        "h": 250, "b": 260, "tw": 7.5, "tf": 12.5, "r": 24.0,
        "A": 8680, "Iy": 10450e4, "Iz": 3668e4, "It": 52.4e4, "Iw": 516e9,
        "Wpl_y": 920e3, "Wpl_z": 430e3, "Wel_y": 836e3, "Wel_z": 282e3,
        "iy": 110, "iz": 65.0, "mass": 68.2,
    },
    "HEA 280": {
        "h": 270, "b": 280, "tw": 8.0, "tf": 13.0, "r": 24.0,
        "A": 9730, "Iy": 13670e4, "Iz": 4763e4, "It": 62.1e4, "Iw": 765e9,
        "Wpl_y": 1112e3, "Wpl_z": 518e3, "Wel_y": 1013e3, "Wel_z": 340e3,
        "iy": 119, "iz": 70.0, "mass": 76.4,
    },
    "HEA 300": {
        "h": 290, "b": 300, "tw": 8.5, "tf": 14.0, "r": 27.0,
        "A": 11300, "Iy": 18260e4, "Iz": 6310e4, "It": 85.2e4, "Iw": 1200e9,
        "Wpl_y": 1383e3, "Wpl_z": 641e3, "Wel_y": 1260e3, "Wel_z": 421e3,
        "iy": 127, "iz": 74.9, "mass": 88.3,
    },
    "HEA 320": {
        "h": 310, "b": 300, "tw": 9.0, "tf": 15.5, "r": 27.0,
        "A": 12400, "Iy": 22930e4, "Iz": 6985e4, "It": 109e4, "Iw": 1520e9,
        "Wpl_y": 1628e3, "Wpl_z": 709e3, "Wel_y": 1479e3, "Wel_z": 466e3,
        "iy": 136, "iz": 75.1, "mass": 97.6,
    },
    "HEA 340": {
        "h": 330, "b": 300, "tw": 9.5, "tf": 16.5, "r": 27.0,
        "A": 13300, "Iy": 27690e4, "Iz": 7436e4, "It": 127e4, "Iw": 1838e9,
        "Wpl_y": 1850e3, "Wpl_z": 756e3, "Wel_y": 1678e3, "Wel_z": 496e3,
        "iy": 144, "iz": 74.8, "mass": 105,
    },
    "HEA 360": {
        "h": 350, "b": 300, "tw": 10.0, "tf": 17.5, "r": 27.0,
        "A": 14300, "Iy": 33090e4, "Iz": 7887e4, "It": 149e4, "Iw": 2177e9,
        "Wpl_y": 2088e3, "Wpl_z": 802e3, "Wel_y": 1891e3, "Wel_z": 526e3,
        "iy": 152, "iz": 74.4, "mass": 112,
    },
    "HEA 400": {
        "h": 390, "b": 300, "tw": 11.0, "tf": 19.0, "r": 27.0,
        "A": 15900, "Iy": 45070e4, "Iz": 8564e4, "It": 189e4, "Iw": 2942e9,
        "Wpl_y": 2562e3, "Wpl_z": 873e3, "Wel_y": 2311e3, "Wel_z": 571e3,
        "iy": 168, "iz": 73.4, "mass": 125,
    },
}

# CHS Sections (Circular Hollow Sections) - selected sizes
CHS_SECTIONS = {
    "CHS 48.3x3.2": {
        "d": 48.3, "t": 3.2, "A": 453, "I": 7.62e4, "W_pl": 4.14e3,
        "W_el": 3.15e3, "i": 16.0, "mass": 3.56,
    },
    "CHS 60.3x3.2": {
        "d": 60.3, "t": 3.2, "A": 574, "I": 15.5e4, "W_pl": 6.78e3,
        "W_el": 5.14e3, "i": 20.2, "mass": 4.51,
    },
    "CHS 76.1x3.2": {
        "d": 76.1, "t": 3.2, "A": 732, "I": 32.6e4, "W_pl": 11.4e3,
        "W_el": 8.56e3, "i": 25.8, "mass": 5.75,
    },
    "CHS 88.9x4.0": {
        "d": 88.9, "t": 4.0, "A": 1070, "I": 63.5e4, "W_pl": 19.1e3,
        "W_el": 14.3e3, "i": 30.0, "mass": 8.38,
    },
    "CHS 114.3x5.0": {
        "d": 114.3, "t": 5.0, "A": 1720, "I": 172e4, "W_pl": 40.4e3,
        "W_el": 30.1e3, "i": 38.7, "mass": 13.5,
    },
    "CHS 139.7x5.0": {
        "d": 139.7, "t": 5.0, "A": 2120, "I": 323e4, "W_pl": 62.0e3,
        "W_el": 46.2e3, "i": 47.6, "mass": 16.6,
    },
    "CHS 168.3x6.3": {
        "d": 168.3, "t": 6.3, "A": 3210, "I": 710e4, "W_pl": 114e3,
        "W_el": 84.3e3, "i": 57.4, "mass": 25.2,
    },
    "CHS 193.7x8.0": {
        "d": 193.7, "t": 8.0, "A": 4660, "I": 1360e4, "W_pl": 190e3,
        "W_el": 140e3, "i": 65.7, "mass": 36.6,
    },
    "CHS 219.1x8.0": {
        "d": 219.1, "t": 8.0, "A": 5300, "I": 2020e4, "W_pl": 249e3,
        "W_el": 184e3, "i": 74.7, "mass": 41.6,
    },
    "CHS 273.0x8.0": {
        "d": 273.0, "t": 8.0, "A": 6660, "I": 4030e4, "W_pl": 399e3,
        "W_el": 295e3, "i": 93.8, "mass": 52.3,
    },
    "CHS 323.9x10.0": {
        "d": 323.9, "t": 10.0, "A": 9870, "I": 8270e4, "W_pl": 690e3,
        "W_el": 511e3, "i": 111, "mass": 77.4,
    },
    "CHS 355.6x10.0": {
        "d": 355.6, "t": 10.0, "A": 10900, "I": 11000e4, "W_pl": 837e3,
        "W_el": 619e3, "i": 122, "mass": 85.2,
    },
}

# RHS/SHS Sections (Rectangular/Square Hollow Sections) — selected sizes
RHS_SECTIONS = {
    "SHS 40x40x3.0": {
        "h": 40, "b": 40, "t": 3.0, "A": 426, "Iy": 8.22e4, "Iz": 8.22e4,
        "Wpl_y": 5.45e3, "Wpl_z": 5.45e3, "Wel_y": 4.11e3, "Wel_z": 4.11e3,
        "iy": 15.3, "iz": 15.3, "mass": 3.35,
    },
    "SHS 50x50x4.0": {
        "h": 50, "b": 50, "t": 4.0, "A": 694, "Iy": 18.7e4, "Iz": 18.7e4,
        "Wpl_y": 10.0e3, "Wpl_z": 10.0e3, "Wel_y": 7.47e3, "Wel_z": 7.47e3,
        "iy": 18.9, "iz": 18.9, "mass": 5.45,
    },
    "SHS 60x60x5.0": {
        "h": 60, "b": 60, "t": 5.0, "A": 1050, "Iy": 38.6e4, "Iz": 38.6e4,
        "Wpl_y": 17.4e3, "Wpl_z": 17.4e3, "Wel_y": 12.9e3, "Wel_z": 12.9e3,
        "iy": 22.5, "iz": 22.5, "mass": 8.22,
    },
    "SHS 80x80x5.0": {
        "h": 80, "b": 80, "t": 5.0, "A": 1430, "Iy": 96.4e4, "Iz": 96.4e4,
        "Wpl_y": 31.7e3, "Wpl_z": 31.7e3, "Wel_y": 24.1e3, "Wel_z": 24.1e3,
        "iy": 30.5, "iz": 30.5, "mass": 11.2,
    },
    "SHS 100x100x6.0": {
        "h": 100, "b": 100, "t": 6.0, "A": 2130, "Iy": 223e4, "Iz": 223e4,
        "Wpl_y": 59.0e3, "Wpl_z": 59.0e3, "Wel_y": 44.5e3, "Wel_z": 44.5e3,
        "iy": 38.1, "iz": 38.1, "mass": 16.7,
    },
    "SHS 120x120x8.0": {
        "h": 120, "b": 120, "t": 8.0, "A": 3390, "Iy": 494e4, "Iz": 494e4,
        "Wpl_y": 110e3, "Wpl_z": 110e3, "Wel_y": 82.3e3, "Wel_z": 82.3e3,
        "iy": 44.8, "iz": 44.8, "mass": 26.6,
    },
    "SHS 150x150x8.0": {
        "h": 150, "b": 150, "t": 8.0, "A": 4290, "Iy": 1010e4, "Iz": 1010e4,
        "Wpl_y": 178e3, "Wpl_z": 178e3, "Wel_y": 134e3, "Wel_z": 134e3,
        "iy": 56.9, "iz": 56.9, "mass": 33.7,
    },
    "SHS 200x200x10.0": {
        "h": 200, "b": 200, "t": 10.0, "A": 7170, "Iy": 2910e4, "Iz": 2910e4,
        "Wpl_y": 387e3, "Wpl_z": 387e3, "Wel_y": 291e3, "Wel_z": 291e3,
        "iy": 75.2, "iz": 75.2, "mass": 56.3,
    },
    "SHS 250x250x10.0": {
        "h": 250, "b": 250, "t": 10.0, "A": 9070, "Iy": 5940e4, "Iz": 5940e4,
        "Wpl_y": 628e3, "Wpl_z": 628e3, "Wel_y": 475e3, "Wel_z": 475e3,
        "iy": 95.4, "iz": 95.4, "mass": 71.2,
    },
    "RHS 100x50x4.0": {
        "h": 100, "b": 50, "t": 4.0, "A": 1070, "Iy": 128e4, "Iz": 43.7e4,
        "Wpl_y": 34.1e3, "Wpl_z": 22.0e3, "Wel_y": 25.7e3, "Wel_z": 17.5e3,
        "iy": 37.8, "iz": 20.2, "mass": 8.42,
    },
    "RHS 120x60x5.0": {
        "h": 120, "b": 60, "t": 5.0, "A": 1630, "Iy": 280e4, "Iz": 97.3e4,
        "Wpl_y": 63.0e3, "Wpl_z": 41.2e3, "Wel_y": 46.7e3, "Wel_z": 32.4e3,
        "iy": 45.0, "iz": 24.4, "mass": 12.8,
    },
    "RHS 150x100x6.0": {
        "h": 150, "b": 100, "t": 6.0, "A": 2770, "Iy": 729e4, "Iz": 389e4,
        "Wpl_y": 131e3, "Wpl_z": 100e3, "Wel_y": 97.2e3, "Wel_z": 77.9e3,
        "iy": 55.5, "iz": 37.5, "mass": 21.7,
    },
    "RHS 200x100x8.0": {
        "h": 200, "b": 100, "t": 8.0, "A": 4350, "Iy": 1910e4, "Iz": 651e4,
        "Wpl_y": 254e3, "Wpl_z": 166e3, "Wel_y": 191e3, "Wel_z": 130e3,
        "iy": 72.9, "iz": 38.7, "mass": 34.2,
    },
    "RHS 250x150x10.0": {
        "h": 250, "b": 150, "t": 10.0, "A": 7370, "Iy": 5470e4, "Iz": 2430e4,
        "Wpl_y": 584e3, "Wpl_z": 414e3, "Wel_y": 438e3, "Wel_z": 324e3,
        "iy": 91.3, "iz": 57.5, "mass": 57.8,
    },
    "RHS 300x200x10.0": {
        "h": 300, "b": 200, "t": 10.0, "A": 9370, "Iy": 10250e4, "Iz": 5620e4,
        "Wpl_y": 910e3, "Wpl_z": 718e3, "Wel_y": 683e3, "Wel_z": 562e3,
        "iy": 112, "iz": 77.4, "mass": 73.6,
    },
}

# UPN Sections (European Channels)
UPN_SECTIONS = {
    "UPN 80": {
        "h": 80, "b": 45, "tw": 6.0, "tf": 8.0, "r": 8.0,
        "A": 1100, "Iy": 106e4, "Iz": 19.4e4,
        "Wpl_y": 31.4e3, "Wpl_z": 9.11e3, "Wel_y": 26.5e3, "Wel_z": 6.36e3,
        "iy": 31.0, "iz": 13.3, "mass": 8.64,
    },
    "UPN 100": {
        "h": 100, "b": 50, "tw": 6.0, "tf": 8.5, "r": 8.5,
        "A": 1350, "Iy": 206e4, "Iz": 29.3e4,
        "Wpl_y": 48.2e3, "Wpl_z": 12.2e3, "Wel_y": 41.2e3, "Wel_z": 8.49e3,
        "iy": 39.0, "iz": 14.7, "mass": 10.6,
    },
    "UPN 120": {
        "h": 120, "b": 55, "tw": 7.0, "tf": 9.0, "r": 9.0,
        "A": 1700, "Iy": 364e4, "Iz": 43.2e4,
        "Wpl_y": 71.0e3, "Wpl_z": 16.6e3, "Wel_y": 60.7e3, "Wel_z": 11.1e3,
        "iy": 46.2, "iz": 15.9, "mass": 13.4,
    },
    "UPN 140": {
        "h": 140, "b": 60, "tw": 7.0, "tf": 10.0, "r": 10.0,
        "A": 2040, "Iy": 605e4, "Iz": 62.7e4,
        "Wpl_y": 100e3, "Wpl_z": 22.3e3, "Wel_y": 86.4e3, "Wel_z": 14.8e3,
        "iy": 54.4, "iz": 17.5, "mass": 16.0,
    },
    "UPN 160": {
        "h": 160, "b": 65, "tw": 7.5, "tf": 10.5, "r": 10.5,
        "A": 2400, "Iy": 925e4, "Iz": 85.3e4,
        "Wpl_y": 134e3, "Wpl_z": 28.3e3, "Wel_y": 116e3, "Wel_z": 18.3e3,
        "iy": 62.0, "iz": 18.9, "mass": 18.8,
    },
    "UPN 180": {
        "h": 180, "b": 70, "tw": 8.0, "tf": 11.0, "r": 11.0,
        "A": 2800, "Iy": 1350e4, "Iz": 114e4,
        "Wpl_y": 174e3, "Wpl_z": 35.0e3, "Wel_y": 150e3, "Wel_z": 22.4e3,
        "iy": 69.4, "iz": 20.2, "mass": 22.0,
    },
    "UPN 200": {
        "h": 200, "b": 75, "tw": 8.5, "tf": 11.5, "r": 11.5,
        "A": 3220, "Iy": 1910e4, "Iz": 148e4,
        "Wpl_y": 220e3, "Wpl_z": 42.4e3, "Wel_y": 191e3, "Wel_z": 27.0e3,
        "iy": 77.0, "iz": 21.4, "mass": 25.3,
    },
    "UPN 220": {
        "h": 220, "b": 80, "tw": 9.0, "tf": 12.5, "r": 12.5,
        "A": 3740, "Iy": 2690e4, "Iz": 197e4,
        "Wpl_y": 282e3, "Wpl_z": 52.8e3, "Wel_y": 245e3, "Wel_z": 33.6e3,
        "iy": 84.8, "iz": 22.9, "mass": 29.4,
    },
    "UPN 240": {
        "h": 240, "b": 85, "tw": 9.5, "tf": 13.0, "r": 13.0,
        "A": 4230, "Iy": 3600e4, "Iz": 248e4,
        "Wpl_y": 345e3, "Wpl_z": 62.6e3, "Wel_y": 300e3, "Wel_z": 39.6e3,
        "iy": 92.2, "iz": 24.2, "mass": 33.2,
    },
    "UPN 300": {
        "h": 300, "b": 100, "tw": 10.0, "tf": 16.0, "r": 16.0,
        "A": 5880, "Iy": 8030e4, "Iz": 495e4,
        "Wpl_y": 612e3, "Wpl_z": 107e3, "Wel_y": 535e3, "Wel_z": 67.8e3,
        "iy": 117, "iz": 29.0, "mass": 46.2,
    },
}

# Equal Angle Sections
ANGLE_SECTIONS = {
    "L 30x30x3": {"a": 30, "t": 3, "A": 174, "I_max": 2.49e4, "mass": 1.36},
    "L 40x40x4": {"a": 40, "t": 4, "A": 308, "I_max": 7.64e4, "mass": 2.42},
    "L 50x50x5": {"a": 50, "t": 5, "A": 480, "I_max": 18.6e4, "mass": 3.77},
    "L 60x60x6": {"a": 60, "t": 6, "A": 691, "I_max": 38.0e4, "mass": 5.42},
    "L 70x70x7": {"a": 70, "t": 7, "A": 940, "I_max": 68.4e4, "mass": 7.38},
    "L 80x80x8": {"a": 80, "t": 8, "A": 1230, "I_max": 113e4, "mass": 9.63},
    "L 90x90x9": {"a": 90, "t": 9, "A": 1550, "I_max": 175e4, "mass": 12.2},
    "L 100x100x10": {"a": 100, "t": 10, "A": 1920, "I_max": 261e4, "mass": 15.0},
    "L 120x120x12": {"a": 120, "t": 12, "A": 2760, "I_max": 537e4, "mass": 21.6},
    "L 150x150x15": {"a": 150, "t": 15, "A": 4300, "I_max": 1290e4, "mass": 33.8},
    "L 200x200x16": {"a": 200, "t": 16, "A": 6150, "I_max": 3320e4, "mass": 48.3},
}


# ============== All Sections Combined ==============

ALL_SECTION_TYPES = {
    "IPE": IPE_SECTIONS,
    "HEB": HEB_SECTIONS,
    "HEA": HEA_SECTIONS,
    "CHS": CHS_SECTIONS,
    "SHS/RHS": RHS_SECTIONS,
    "UPN": UPN_SECTIONS,
    "Angle": ANGLE_SECTIONS,
}


# ============== Section Database Service ==============

class SectionDatabase:
    """Service for querying steel section properties."""

    def __init__(self):
        self.sections = ALL_SECTION_TYPES

    def get_section(self, name: str) -> Optional[Dict[str, Any]]:
        """Get properties for a specific section by name."""
        name_upper = name.upper().strip()

        for section_type, sections in self.sections.items():
            for section_name, props in sections.items():
                if section_name.upper() == name_upper:
                    return {
                        "name": section_name,
                        "type": section_type,
                        "properties": props,
                    }
        return None

    def search_sections(
        self,
        query: str = "",
        section_type: Optional[str] = None,
        min_height: Optional[float] = None,
        max_height: Optional[float] = None,
        min_area: Optional[float] = None,
        max_mass: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """Search sections with filters."""
        results = []

        for s_type, sections in self.sections.items():
            if section_type and section_type.upper() not in s_type.upper():
                continue

            for name, props in sections.items():
                # Text query match
                if query and query.upper() not in name.upper():
                    continue

                # Height filter
                h = props.get("h", props.get("d", props.get("a", 0)))
                if min_height and h < min_height:
                    continue
                if max_height and h > max_height:
                    continue

                # Area filter
                if min_area and props.get("A", 0) < min_area:
                    continue

                # Mass filter
                if max_mass and props.get("mass", 0) > max_mass:
                    continue

                results.append({
                    "name": name,
                    "type": s_type,
                    "properties": props,
                })

        return sorted(results, key=lambda x: x["properties"].get("mass", 0))

    def list_section_types(self) -> List[str]:
        """List all available section types."""
        return list(self.sections.keys())

    def list_sections_by_type(self, section_type: str) -> List[Dict[str, Any]]:
        """List all sections of a given type."""
        for s_type, sections in self.sections.items():
            if section_type.upper() in s_type.upper():
                return [
                    {"name": name, "type": s_type, "properties": props}
                    for name, props in sections.items()
                ]
        return []

    def get_property_units(self) -> Dict[str, str]:
        """Return the units for each property field."""
        return {
            "h": "mm", "b": "mm", "tw": "mm", "tf": "mm", "r": "mm",
            "d": "mm", "t": "mm", "a": "mm",
            "A": "mm²",
            "Iy": "mm⁴ (×10⁴)", "Iz": "mm⁴ (×10⁴)",
            "I": "mm⁴ (×10⁴)", "I_max": "mm⁴ (×10⁴)",
            "It": "mm⁴ (×10⁴)", "Iw": "mm⁶ (×10⁹)",
            "Wpl_y": "mm³ (×10³)", "Wpl_z": "mm³ (×10³)",
            "Wel_y": "mm³ (×10³)", "Wel_z": "mm³ (×10³)",
            "W_pl": "mm³ (×10³)", "W_el": "mm³ (×10³)",
            "iy": "mm", "iz": "mm", "i": "mm",
            "mass": "kg/m",
        }
