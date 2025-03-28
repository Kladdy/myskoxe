C***********************************************************************
C FROM https://t2.lanl.gov/nis/codes/transx-hyper/matxs.html           -
C               PROPOSED 09/09/77                                      -
C                       (MODIFIED 09/80)                               -
C                       (NOMENCLATURE CHANGED 06/88)                   -
C                       (MODIFIED FOR CONST SUB-BLOCKS 06/90)          -
C                       (ORDERING CHANGED 10/90)                       -
C                                                                      -
CF           MATXS                                                     -
CE           MATERIAL CROSS SECTION FILE                               -
C                                                                      -
CN                       THIS FILE CONTAINS CROSS SECTION              -
CN                       VECTORS AND MATRICES FOR ALL                  -
CN                       PARTICLES, MATERIALS, AND REACTIONS;          -
CN                       DELAYED NEUTRON SPECTRA BY TIME GROUP;        -
CN                       AND DECAY HEAT AND PHOTON SPECTRA.            -
C                                                                      -
CN           FORMATS GIVEN ARE FOR FILE EXCHANGE ONLY                  -
C                                                                      -
C***********************************************************************
C
C
C-----------------------------------------------------------------------
CS          FILE STRUCTURE                                             -
CS                                                                     -
CS              RECORD TYPE                       PRESENT IF           -
CS              ==============================    ===============      -
CS              FILE IDENTIFICATION                 ALWAYS             -
CS              FILE CONTROL                        ALWAYS             -
CS              SET HOLLERITH IDENTIFICATION        ALWAYS             -
CS              FILE DATA                           ALWAYS             -
CS                                                                     -
CS   *************(REPEAT FOR ALL PARTICLES)                           -
CS   *          GROUP STRUCTURES                    ALWAYS             -
CS   *************                                                     -
CS                                                                     -
CS   *************(REPEAT FOR ALL MATERIALS)                           -
CS   *          MATERIAL CONTROL                    ALWAYS             -
CS   *                                                                 -
CS   * ***********(REPEAT FOR ALL SUBMATERIALS)                        -
CS   * *        VECTOR CONTROL                      N1DB.GT.0          -
CS   * *                                                               -
CS   * * *********(REPEAT FOR ALL VECTOR BLOCKS)                       -
CS   * * *      VECTOR BLOCK                        N1DB.GT.0          -
CS   * * *********                                                     -
CS   * *                                                               -
CS   * * *********(REPEAT FOR ALL MATRIX BLOCKS)                       -
CS   * * *      MATRIX CONTROL                      N2D.GT.0           -
CS   * * *                                                             -
CS   * * * *******(REPEAT FOR ALL SUB-BLOCKS)                          -
CS   * * * *    MATRIX SUB-BLOCK                    N2D.GT.0           -
CS   * * * *******                                                     -
CS   * * *                                                             -
CS   * * *      CONSTANT SUB-BLOCK                  JCONST.GT.0        -
CS   * * *                                                             -
CS   *************                                                     -
C                                                                      -
C-----------------------------------------------------------------------
C
C
C-----------------------------------------------------------------------
CR           FILE IDENTIFICATION                                       -
C                                                                      -
CL    HNAME,(HUSE(I),I=1,2),IVERS                                      -
C                                                                      -
CW    1+3*MULT                                                         -
C                                                                      -
CB    FORMAT(4H OV ,A8,1H*,2A8,1H*,I6)                                 -
C                                                                      -
CD    HNAME         HOLLERITH FILE NAME  - MATXS -  (A8)               -
CD    HUSE          HOLLERITH USER IDENTIFIATION    (A8)               -
CD    IVERS         FILE VERSION NUMBER                                -
CD    MULT          DOUBLE PRECISION PARAMETER                         -
CD                       1- A8 WORD IS SINGLE WORD                     -
CD                       2- A8 WORD IS DOUBLE PRECISION WORD           -
C                                                                      -
C-----------------------------------------------------------------------
C
C
C-----------------------------------------------------------------------
CR           FILE CONTROL                                              -
C                                                                      -
CL    NPART,NTYPE,NHOLL,NMAT,MAXW,LENGTH                               -
C                                                                      -
CW    6                                                                -
C                                                                      -
CB    FORMAT(4H 1D ,4I6)                                               -
C                                                                      -
CD    NPART       NUMBER OF PARTICLES FOR WHICH GROUP                  -
CD                   STRUCTURES ARE GIVEN                              -
CD    NTYPE       NUMBER OF DATA TYPES PRESENT IN SET                  -
CD    NHOLL       NUMBER OF WORDS IN SET HOLLERITH                     -
CD                    IDENTIFICATION RECORD                            -
CD    NMAT        NUMBER OF MATERIALS ON FILE                          -
CD    MAXW        MAXIMUM RECORD SIZE FOR SUB-BLOCKING                 -
CD    LENGTH      LENGTH OF FILE                                       -
C                                                                      -
C-----------------------------------------------------------------------
C
C
C-----------------------------------------------------------------------
CR           SET HOLLERITH IDENTIFICATION                              -
C                                                                      -
CL    (HSETID(I),I=1,NHOLL)                                            -
C                                                                      -
CW    NHOLL*MULT                                                       -
C                                                                      -
CB    FORMAT(4H 2D ,8A8/(9A8))                                         -
C                                                                      -
CD    HSETID      HOLLERITH IDENTIFICATION OF SET (A8)                 -
CD                 (TO BE EDITED OUT 72 CHARACTERS PER LINE)           -
C                                                                      -
C-----------------------------------------------------------------------
C
C
C-----------------------------------------------------------------------
CR          FILE DATA                                                  -
C                                                                      -
CL    (HPRT(J),J=1,NPART),(HTYPE(K),K=1,NTYPE),(HMATN(I),I=1,NMAT),    -
CL   1(NGRP(J),J=1,NPART),(JINP(K),K=1,NTYPE,(JOUTP(K),K=1,NTYPE),     -
CL   2(NSUBM(I)I=1,NMAT),(LOCM(I),I=1,NMAT)                            -
C                                                                      -
CW    (NPART+NTYPE+NMAT)*MULT+2*NTYPE+NPART+2*NMAT                     -
C                                                                      -
CB    FORMAT(4H 3D ,8A8/(9A8))      HPRT,HTYPE,HMATN                   -
CB    FORMAT(12I6)                  NGRP,JINP,JOUTP,NSUBM,LOCM         -
C                                                                      -
CD    HPRT(J)     HOLLERITH IDENTIFICATION FOR PARTICLE J              -
CD                     N         NEUTRON                               -
CD                     G         GAMMA                                 -
CD                     P         PROTON                                -
CD                     D         DEUTERON                              -
CD                     T         TRITON                                -
CD                     H         HE-3 NUCLEUS                          -
CD                     A         ALPHA (HE-4 NUCLEUS)                  -
CD                     B         BETA                                  -
CD                     R         RESIDUAL OR RECOIL                    -
CD                               (HEAVIER THAN ALPHA)                  -
CD    HTYPE(K)     HOLLERITH IDENTIFICATION FOR DATA TYPE K            -
CD                     NSCAT     NEUTRON SCATTERING                    -
CD                     NG        NEUTRON INDUCED GAMMA PRODUCTION      -
CD                     GSCAT     GAMMA SCATTERING                      -
CD                     PN        PROTON INDUCED NEUTRON PRODUCTION     -
CD                       .          .                                  -
CD                       .          .                                  -
CD                       .          .                                  -
CD                     DKN       DELAYED NEUTRON DATA                  -
CD                     DKHG      DECAY HEAT AND GAMMA DATA             -
CD                     DKB       DECAY BETA DATA                       -
CD    HMATN(I)    HOLLERITH IDENTIFICATION FOR MATERIAL I              -
CD    NGRP(J)      NUMBER OF ENERGY GROUPS FOR PARTICLE J              -
CD    JINP(K)     TYPE OF INCIDENT PARTICLE ASSOCIATED WITH            -
CD                   DATA TYPE K.  FOR DK DATA TYPES, JINP IS 0.       -
CD    JOUTP(K)    TYPE OF OUTGOING PARTICLE ASSOCIATED WITH            -
CD                   DATA TYPE K                                       -
CD    NSUBM(I)    NUMBER OF SUBMATERIALS FOR MATERIAL I                -
CD    LOCM(I)     LOCATION OF MATERIAL I                               -
C                                                                      -
C-----------------------------------------------------------------------
C
C
C-----------------------------------------------------------------------
CR          GROUP STRUCTURE                                            -
C                                                                      -
CL    (GPB(I),I=1,NGR),EMIN                                            -
C                                                                      -
CC    NGR=NGRP(J)                                                      -
C                                                                      -
CW    NGRP(J)+1                                                        -
C                                                                      -
CB    FORMAT(4H 4D ,1P5E12.5/(6E12.5))                                 -
C                                                                      -
CD    GPB(I)      MAXIMUM ENERGY BOUND FOR GROUP I FOR PARTICLE J      -
CD    EMIN        MINIMUM ENERGY BOUND FOR PARTICLE J                  -
C                                                                      -
C-----------------------------------------------------------------------
C
C
C-----------------------------------------------------------------------
CR          MATERIAL CONTROL                                           -
C                                                                      -
CL    HMAT,AMASS,(TEMP(I),SIGZ(I),ITYPE(I),N1D(I),N2D(I),              -
CL   1LOCS(I),I=1,NSUBM)                                               -
C                                                                      -
CW    MULT+1+6*NSUBM                                                   -
C                                                                      -
CB    FORMAT(4H 6D ,A8,1H*,1P2E12.5/(2E12.5,5I6))                      -
C                                                                      -
CD    HMAT        HOLLERITH MATERIAL IDENTIFIER                        -
CD    AMASS       ATOMIC WEIGHT RATIO                                  -
CD    TEMP        AMBIENT TEMPERATURE OR OTHER PARAMETERS FOR          -
CD                    SUBMATERIAL I                                    -
CD    SIGZ        DILUTION FACTOR OR OTHER PARAMETERS FOR              -
CD                    SUBMATERIAL I                                    -
CD    ITYPE       DATA TYPE FOR SUBMATERIAL I                          -
CD    N1D         NUMBER OF VECTORS FOR SUBMATERIAL I                  -
CD    N2D         NUMBER OF MATRIX BLOCKS FOR SUBMATERIAL I            -
CD    LOCS        LOCATION OF SUBMATERIAL I                            -
C                                                                      -
C-----------------------------------------------------------------------
C
C
C-----------------------------------------------------------------------
CR          VECTOR CONTROL                                             -
C                                                                      -
CL    (HVPS(I),I=1,N1D),(NFG(I),I=1,N1D),(NLG(I),I=1,N1D)              -
C                                                                      -
CW    (MULT+2)*N1D                                                     -
C                                                                      -
CB    FORMAT(4H 7D ,8A8/(9A8))        HVPS                             -
CB    FORMAT(12I6)                    IBLK,NFG,NLG                     -
C                                                                      -
CD    HVPS(I)     HOLLERITH IDENTIFIER OF VECTOR                       -
CD                      NELAS     NEUTRON ELASTIC SCATTERING           -
CD                      N2N       (N,2N)                               -
CD                      NNF       SECOND CHANCE FISSION                -
CD                      GABS      GAMMA ABSORPTION                     -
CD                      P2N       PROTONS IN, 2 NEUTRONS OUT           -
CD                         .          .                                -
CD                         .          .                                -
CD                         .          .                                -
CD    NFG(I)      NUMBER OF FIRST GROUP IN BAND FOR VECTOR I           -
CD    NLG(I)      NUMBER OF LAST GROUP IN BAND FOR VECTOR I            -
C                                                                      -
C-----------------------------------------------------------------------
C
C
C-----------------------------------------------------------------------
CR          VECTOR BLOCK                                               -
C                                                                      -
CL    (VPS(I),I=1,KMAX)                                                -
C                                                                      -
CC    KMAX=SUM OVER GROUP BAND FOR EACH VECTOR IN BLOCK J              -
C                                                                      -
CW    KMAX                                                             -
C                                                                      -
CB    FORMAT(4H 8D ,1P5E12.5/(6E12.5))                                 -
C                                                                      -
CD    VPS(I)      DATA FOR GROUP BANDS FOR VECTORS IN BLOCK J.         -
CD                BLOCK SIZE IS DETERMINED BY TAKING ALL THE GROUP     -
CD                BANDS THAT HAVE A TOTAL LENGTH LESS THAN OR EQUAL    -
CD                TO MAXW.                                             -
C                                                                      -
C-----------------------------------------------------------------------
C
C
C-----------------------------------------------------------------------
CR        SCATTERING MATRIX CONTROL                                    -
C                                                                      -
CL    HMTX,LORD,JCONST,
CL   1(JBAND(L),L=1,NOUTG(K)),(IJJ(L),L=1,NOUTG(K))                    -
C                                                                      -
CW    MULT+2+2*NOUTG(K)                                                -
C                                                                      -
CB    FORMAT(4H 9D ,A8/(12I6))        HMTX,LORD,JCONST,                -
CB                                     JBAND,IJJ                       -
C                                                                      -
CD    HMTX        HOLLERITH IDENTIFICATION OF BLOCK                    -
CD    LORD        NUMBER OF ORDERS PRESENT                             -
CD    JCONST      NUMBER OF GROUPS WITH CONSTANT SPECTRUM              -
CD    JBAND(L)    BANDWIDTH FOR GROUP L                                -
CD    IJJ(L)      LOWEST GROUP IN BAND FOR GROUP L                     -
C                                                                      -
C-----------------------------------------------------------------------
C
C
C-----------------------------------------------------------------------
CR          SCATTERING SUB-BLOCK                                       -
C                                                                      -
CL    (SCAT(K),K=1,KMAX)                                               -
C                                                                      -
CC    KMAX=LORD TIMES THE SUM OVER ALL JBAND IN THE GROUP RANGE OF     -
CC            THIS SUB-BLOCK                                           -
C                                                                      -
CB    FORMAT(5H 10D ,1P5E12.5/(6E12.5))                                -
C                                                                      -
CW    KMAX                                                             -
C                                                                      -
CD    SCAT(K)     MATRIX DATA GIVEN AS BANDS OF ELEMENTS FOR INITIAL   -
CD                GROUPS THAT LEAD TO EACH FINAL GROUP.  THE ORDER     -
CD                OF THE ELEMENTS IS AS FOLLOWS:  BAND FOR P0 OF       -
CD                GROUP I, BAND FOR P1 OF GROUP I, ... , BAND FOR P0   -
CD                OF GROUP I+1, BAND FOR P1 OF GROUP I+1, ETC.  THE    -
CD                GROUPS IN EACH BAND ARE GIVEN IN DESCENDING ORDER.   -
CD                THE SIZE OF EACH SUB-BLOCK IS DETERMINED BY THE      -
CD                TOTAL LENGTH OF A GROUP OF BANDS THAT IS LESS THAN   -
CD                OR EQUAL TO MAXW.                                    -
CD                                                                     -
CD                IF JCONST.GT.0, THE CONTRIBUTIONS FROM THE JCONST    -
CD                LOW-ENERGY GROUPS ARE GIVEN SEPARATELY.              -
C                                                                      -
C-----------------------------------------------------------------------
C                                                                      -
C                                                                      -
C-----------------------------------------------------------------------
CR          CONSTANT SUB-BLOCK                                         -
C                                                                      -
CL    (SPEC(L),L=1,NOUTG(K)),(PROD(L),L=L1,NING(K))                    -
C                                                                      -
CC    L1=NING(K)-JCONST+1                                              -
C                                                                      -
CW    NOUTG(K)+JCONST                                                  -
C                                                                      -
CB    FORMAT(4H11D ,1P5E12.5/(6E12.5))                                 -
C                                                                      -
CD    SPEC        NORMALIZED SPECTRUM OF FINAL PARTICLES FOR INITIAL   -
CD                PARTICLES IN GROUPS L1 TO NING(K)                    -
CD    PROD        PRODUCTION CROSS SECTION (E.G., NU*SIGF) FOR         -
CD                INITIAL GROUPS L1 THROUGH NING(K)                    -
CD                                                                     -
CD         THIS OPTION IS NORMALLY USED FOR THE ENERGY-INDEPENDENT     -
CD         NEUTRON AND PHOTON SPECTRA FROM FISSION AND RADIATIVE       -
CD         CAPTURE USUALLY SEEN AT LOW ENERGIES.                       -
C                                                                      -
C-----------------------------------------------------------------------